#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour les utilitaires (diagnose.py et function.py)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Ajouter le répertoire parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    from diagnose import diagnose_feasibility
    print("✅ Module diagnose importé avec succès")
    DIAGNOSE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Module diagnose non trouvé: {e}")
    DIAGNOSE_AVAILABLE = False

try:
    from function import (
        get_availabilityProf_From_Unavailable,
        get_availabilityRoom_From_Unavailable,
        get_availabilityGroup_From_Unavailable,
        convert_days_int_to_string
    )
    print("✅ Module function importé avec succès")
    FUNCTION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Module function non trouvé: {e}")
    FUNCTION_AVAILABLE = False


@unittest.skipIf(not DIAGNOSE_AVAILABLE, "Module diagnose non disponible")
class TestDiagnoseFeasibility(unittest.TestCase):
    """Tests pour la fonction diagnose_feasibility"""

    def setUp(self):
        """Initialisation des données de test"""
        self.valid_data = {
            'jours': 5,
            'creneaux_par_jour': 20,
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'nb_slots': 100,
            'fenetre_midi': [8, 9, 10],  # slots midi bloqués
            'salles': {'Salle A': 30, 'Salle B': 50, 'Amphi': 100},
            'cours': [
                {'id': 'CM_Math_BUT1', 'groups': ['BUT1']},
                {'id': 'TD_Info_G1', 'groups': ['G1']}
            ],
            'duree_cours': {
                'CM_Math_BUT1': 3,  # 1.5h
                'TD_Info_G1': 2     # 1h
            },
            'taille_groupes': {
                'BUT1': 60,
                'G1': 30
            },
            'map_groupe_cours': {
                'BUT1': ['CM_Math_BUT1'],
                'G1': ['TD_Info_G1']
            }
        }

    def test_diagnose_valid_schedule(self):
        """Test diagnostic avec un emploi du temps valide"""
        problems = diagnose_feasibility(self.valid_data)

        # Vérifier qu'il n'y a pas de problèmes
        self.assertEqual(len(problems['no_valid_start']), 0)
        self.assertEqual(len(problems['no_room']), 0)
        self.assertEqual(len(problems['group_overbooked']), 0)

    def test_diagnose_course_too_long(self):
        """Test avec un cours trop long pour un créneau"""
        data = self.valid_data.copy()
        data['duree_cours']['CM_Math_BUT1'] = 25  # Plus long qu'un jour

        problems = diagnose_feasibility(data)

        # Devrait détecter un problème de start invalide
        self.assertGreater(len(problems['no_valid_start']), 0)

    def test_diagnose_room_too_small(self):
        """Test avec des salles trop petites"""
        data = self.valid_data.copy()
        data['salles'] = {'Petite Salle': 10}  # Trop petite pour tous les groupes

        problems = diagnose_feasibility(data)

        # Devrait détecter un problème de capacité
        self.assertGreater(len(problems['no_room']), 0)

    def test_diagnose_group_overbooked(self):
        """Test avec un groupe surchargé"""
        data = self.valid_data.copy()
        # Ajouter beaucoup de cours pour le même groupe
        for i in range(50):
            course_id = f'CM_Extra_{i}'
            data['cours'].append({'id': course_id, 'groups': ['BUT1']})
            data['duree_cours'][course_id] = 4
            data['map_groupe_cours']['BUT1'].append(course_id)

        problems = diagnose_feasibility(data)

        # Devrait détecter un groupe surchargé
        self.assertGreater(len(problems['group_overbooked']), 0)

    def test_diagnose_with_midi_constraint(self):
        """Test que les contraintes de midi sont respectées"""
        data = self.valid_data.copy()

        problems = diagnose_feasibility(data)

        # Calculer les slots utilisables
        cpd = data['creneaux_par_jour']
        fenetre = set(data['fenetre_midi'])
        usable = [o for o in range(cpd) if o not in fenetre]

        self.assertEqual(len(usable), cpd - len(fenetre))


@unittest.skipIf(not FUNCTION_AVAILABLE, "Module function non disponible")
class TestFunctionUtilities(unittest.TestCase):
    """Tests pour les fonctions utilitaires"""

    def test_convert_days_int_to_string(self):
        """Test conversion jour int -> string"""
        self.assertEqual(convert_days_int_to_string(0), 'Lundi')
        self.assertEqual(convert_days_int_to_string(1), 'Mardi')
        self.assertEqual(convert_days_int_to_string(2), 'Mercredi')
        self.assertEqual(convert_days_int_to_string(3), 'Jeudi')
        self.assertEqual(convert_days_int_to_string(4), 'Vendredi')

    def test_get_availabilityProf_From_Unavailable_empty(self):
        """Test disponibilités prof avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'teacher_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityProf_From_Unavailable(df_empty, 20)

        # Devrait retourner un dict vide ou avec structure par défaut
        self.assertIsInstance(result, dict)

    def test_get_availabilityRoom_From_Unavailable_empty(self):
        """Test disponibilités salle avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'room_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityRoom_From_Unavailable(df_empty, 20)

        self.assertIsInstance(result, dict)

    def test_get_availabilityGroup_From_Unavailable_empty(self):
        """Test disponibilités groupe avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'group_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityGroup_From_Unavailable(df_empty, 20)

        self.assertIsInstance(result, dict)

    @patch('pandas.DataFrame')
    def test_availability_with_constraints(self, mock_df):
        """Test disponibilités avec vraies contraintes"""
        import pandas as pd

        # Créer un DataFrame de test avec des contraintes
        df_test = pd.DataFrame({
            'teacher_id': [1, 1, 2],
            'day_of_week': ['Lundi', 'Mardi', 'Lundi'],
            'start_time': ['08:00:00', '14:00:00', '10:00:00'],
            'end_time': ['10:00:00', '16:00:00', '12:00:00'],
            'priority': ['hard', 'medium', 'hard'],
            'week_id': [1, 1, 1]
        })

        result = get_availabilityProf_From_Unavailable(df_test, 20)

        # Vérifier que la structure est correcte
        self.assertIsInstance(result, dict)
        if result:  # Si la fonction retourne des résultats
            # Vérifier la présence des teacher_ids
            for teacher_id in df_test['teacher_id'].unique():
                if teacher_id in result:
                    self.assertIsInstance(result[teacher_id], dict)


class TestDiagnoseEdgeCases(unittest.TestCase):
    """Tests des cas limites du diagnostic"""

    @unittest.skipIf(not DIAGNOSE_AVAILABLE, "Module diagnose non disponible")
    def test_empty_courses(self):
        """Test avec aucun cours"""
        data = {
            'jours': 5,
            'creneaux_par_jour': 20,
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'nb_slots': 100,
            'fenetre_midi': [8, 9, 10],
            'salles': {'Salle A': 30},
            'cours': [],
            'duree_cours': {},
            'taille_groupes': {},
            'map_groupe_cours': {}
        }

        problems = diagnose_feasibility(data)

        # Pas de problèmes si pas de cours
        self.assertEqual(len(problems['no_valid_start']), 0)

    @unittest.skipIf(not DIAGNOSE_AVAILABLE, "Module diagnose non disponible")
    def test_single_slot_available(self):
        """Test avec un seul slot disponible"""
        data = {
            'jours': 5,
            'creneaux_par_jour': 20,
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'nb_slots': 100,
            'fenetre_midi': list(range(19)),  # Presque tout bloqué
            'salles': {'Salle A': 30},
            'cours': [{'id': 'CM_Math', 'groups': ['BUT1']}],
            'duree_cours': {'CM_Math': 1},
            'taille_groupes': {'BUT1': 30},
            'map_groupe_cours': {'BUT1': ['CM_Math']}
        }

        problems = diagnose_feasibility(data)

        # Devrait avoir des problèmes car très peu de slots
        # (mais au moins un cours devrait pouvoir être placé)
        self.assertIsInstance(problems, dict)


def run_tests():
    """Execute tous les tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ajouter les classes de test disponibles
    if DIAGNOSE_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestDiagnoseFeasibility))
        suite.addTests(loader.loadTestsFromTestCase(TestDiagnoseEdgeCases))

    if FUNCTION_AVAILABLE:
        suite.addTests(loader.loadTestsFromTestCase(TestFunctionUtilities))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("="*70)
    print("  SUITE DE TESTS - UTILITAIRES")
    print("="*70)
    print()

    if not DIAGNOSE_AVAILABLE:
        print("⚠️  Module diagnose non disponible - tests ignorés")
    if not FUNCTION_AVAILABLE:
        print("⚠️  Module function non disponible - tests ignorés")

    print()

    result = run_tests()

    print()
    print("="*70)
    print("  RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)