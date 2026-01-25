import os
import sys
import argparse
import itertools
import time

# --- IMPORT CONFIGURATION CENTRALISÉE ---
from connect_database import get_db_config

# --- DÉBUT DU BLOC DE CORRECTION DE CHEMIN (PyInstaller) ---
if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
    ortools_dll_path_1 = os.path.join(bundle_dir, '_internal', 'ortools', '.libs')
    ortools_dll_path_2 = os.path.join(bundle_dir, '_internal', 'ortools')
    
    paths_to_add = [p for p in [ortools_dll_path_1, ortools_dll_path_2] if os.path.exists(p)]
    for path_to_add in paths_to_add:
        os.environ['PATH'] = path_to_add + os.pathsep + os.environ['PATH']
        print(f"INFO: PATH ajusté pour OR-Tools: {path_to_add}")

from ortools.sat.python import cp_model

# Assure-toi que ces modules sont bien accessibles
import diagnose
from data_provider import DataProvider
from data_provider_id import DataProviderID
from solution_visualizer import SolutionVisualizer
from time_table_model import TimetableModel


def test_combination(model_class, data, disabled_blocks, timeout=60):
    """Teste si en désactivant une liste de blocs, le problème devient faisable"""
    print(f"\n{'='*70}")
    if len(disabled_blocks) == 1:
        print(f"TEST UNIQUE → Désactivation : {disabled_blocks[0]}")
    else:
        print(f"TEST COMBINAISON → Désactivation : {' + '.join(disabled_blocks)}")

    start = time.perf_counter()
    # Note: On suppose que model_class accepte data dans son init
    scheduler = model_class(data)
    scheduler.build_model(disable_blocks=disabled_blocks)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 8
    solver.parameters.log_search_progress = False

    status = solver.Solve(scheduler.model)
    elapsed = time.perf_counter() - start

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"SOLUTION TROUVÉE en {elapsed:.2f}s !")
        print(f"LES CONTRAINTES BLOQUANTES SONT DANS : {', '.join(disabled_blocks)}")
        return True
    else:
        print(f"Infaisable ({solver.StatusName(status)}) après {elapsed:.2f}s")
        return False


def diagnostic_automatique(model_class, data, timeout_per_test=60):
    blocks = [
        "profs", "salles", "etudiant", "hierarchies",
        "ordre_cm_td_tp", "prof disponibles", "salles dispo"
    ]

    print("DIAGNOSTIC AUTOMATIQUE DE L'INFAISABILITÉ")
    print("="*70)

    # === ÉTAPE 1 : Test un par un ===
    print("\n1. Test des blocs un par un...")
    for block in blocks:
        if test_combination(model_class, data, [block], timeout_per_test):
            print(f"\nUN SEUL BLOC SUFFIT → '{block}' est la source du problème.")
            return

    print("\nAucun bloc seul ne résout le problème.")

    # === ÉTAPE 2 : Test des paires ===
    print("\n2. Test des combinaisons de 2 blocs...")
    for combo in itertools.combinations(blocks, 2):
        if test_combination(model_class, data, list(combo), timeout_per_test):
            print(f"\nCOMBINAISON GAGNANTE → Il fallait désactiver : {combo[0]} + {combo[1]}")
            return

    print("\nAucune paire ne suffit.")

    # === ÉTAPE 3 : Test des triplets ===
    print("\n3. Test des combinaisons de 3 blocs...")
    for combo in itertools.combinations(blocks, 3):
        if test_combination(model_class, data, list(combo), timeout_per_test):
            print(f"\nCOMBINAISON GAGNANTE → Il fallait désactiver : {', '.join(combo)}")
            return

    print("\nMême en désactivant 3 blocs, toujours infaisable.")
    print("Possibles causes restantes :")
    print("   • Données incohérentes (ex: cours sans prof possible, salle trop petite obligatoire)")
    print("   • Problème dans les variables de décision ou les contraintes de base")
    print("   • Besoin de désactiver plus de 3 blocs (rare) ou assouplir les contraintes souples")
    print("\nProchaine étape recommandée : utiliser le module 'diagnose.py' avec explain_infeasibility()")


# ==============================================================================
# POINT D'ENTRÉE PRINCIPAL
# ==============================================================================
if __name__ == "__main__":
    start_time = time.perf_counter()
    
    parser = argparse.ArgumentParser(description="Générateur d'emploi du temps")
    parser.add_argument("--id_semaine", type=int, required=True, help="ID de la semaine à générer")
    argvs = parser.parse_args()

    print("Vous avez fourni l'ID semaine :", argvs.id_semaine)

    # --- REFACTO ICI : Utilisation de la config centralisée ---
    # On récupère le dictionnaire depuis db_config.py
    DB_CONFIG = get_db_config()

    # On passe le dictionnaire à tes classes existantes
    # (Je suppose ici que DataProvider et DataProviderID attendent toujours un dict)
    data_provider = DataProvider(DB_CONFIG)
    
    DataProviderInsert = DataProviderID(DB_CONFIG)
    model_data = DataProviderInsert.load_and_prepare_data(argvs.id_semaine)
    
    scheduler = TimetableModel(model_data)
    scheduler.build_model()

    # Résolution
    # probs = diagnose.diagnose_feasibility(model_data) # Décommenter si besoin
    solution = scheduler.solve(max_time_seconds=300)

    if solution and solution['vars']:
        visualizer = SolutionVisualizer(solution, model_data)
        visualizer.display(DataProviderInsert, argvs.id_semaine)
        
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"Programme exécuté en : {execution_time: .5f} secondes")
    else:
        print("\nÉchec de la résolution. Le modèle reste infaisable même avec des contraintes assouplies.")
        print("Causes possibles : Surcharge totale des ressources ou contrainte dure trop restrictive.")
        
        # diagnostic_automatique(TimetableModel, model_data, timeout_per_test=30)

        total_time = time.perf_counter() - start_time
        print(f"\nFin du programme en {total_time:.1f} secondes.")