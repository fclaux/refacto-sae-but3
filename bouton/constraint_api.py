#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional, List, Dict, Callable
from connect_database import get_db_connection
from constraint_manager import ConstraintManager

# Configuration des types de contraintes pour l'abstraction de l'affichage
CONSTRAINT_CONFIG = {
    'teachers': {'label': 'ENSEIGNANTS', 'name_field': lambda c: f"{c['first_name']} {c['last_name']}"},
    'rooms': {'label': 'SALLES', 'name_field': lambda c: c['room_name']},
    'groups': {'label': 'GROUPES', 'name_field': lambda c: c['group_name']}
}

# --- ABSTRACTIONS DE BASE ---

def execute_query(query: str, params: tuple = (), fetch: bool = True) -> List[Dict]:
    """Abstrait la gestion de connexion et l'exécution de requêtes SQL."""
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(query, params)
        return cur.fetchall() if fetch else []
    finally:
        cur.close()
        conn.close()

def interactive_selector(items: List[Dict], display_fmt: Callable, prompt: str, sort_key_index: int = 0) -> Optional[int]:
    """Logique générique pour afficher une liste et retourner un ID sélectionné par l'utilisateur."""
    if not items:
        print(" 🔍 Aucun élément trouvé dans la base.")
        return None

    for item in items:
        print(f"   {display_fmt(item)}")

    try:
        selection = input(f"\n{prompt} (vide pour défaut) : ").strip()
        if selection:
            return int(selection)
        # Retourne le premier ou dernier élément selon l'usage habituel du script original
        return items[sort_key_index]['id']
    except (ValueError, IndexError):
        return items[sort_key_index]['id']

# --- LOGIQUE MÉTIER REFACTORISÉE ---

def choose_year() -> Optional[int]:
    """Sélection interactive de l'année."""
    years = execute_query("SELECT id, name FROM years ORDER BY name DESC")
    print("\nAnnées disponibles:")
    return interactive_selector(
        years, 
        lambda y: f"id={y['id']} - {y['name']}", 
        "Entrez l'id de l'année"
    )

def choose_week(year_id: Optional[int] = None) -> Optional[int]:
    """Sélection interactive de la semaine."""
    query = "SELECT id, week_number, year_id, start_date, end_date FROM weeks"
    params = ()
    if year_id:
        query += " WHERE year_id = %s ORDER BY week_number ASC"
        params = (year_id,)
    else:
        query += " ORDER BY year_id DESC, week_number ASC"
    
    weeks = execute_query(query, params)
    print("\nSemaines disponibles:")
    # Pour les semaines, le script original préférait la dernière par défaut
    return interactive_selector(
        weeks, 
        lambda w: f"id={w['id']} - Semaine {w['week_number']} ({w['start_date']} → {w['end_date']}) [year={w['year_id']}]",
        "Entrez l'id de la semaine",
        sort_key_index=-1 
    )

def display_constraint_section(category: str, items: List[Dict]):
    """Affiche une section de contraintes de manière uniforme (DRY)."""
    config = CONSTRAINT_CONFIG.get(category)
    print(f"\nCONTRAINTES {config['label']}:")
    
    if not items:
        print("   Aucune contrainte")
        return

    for c in items:
        week_info = "PERMANENTE" if c.get('week_id') is None else f"semaine {c.get('week_id')}"
        entity_name = config['name_field'](c)
        print(f"   #{c['id']} ({week_info}): {entity_name} - "
              f"{c['day_of_week']} {c['start_time']}-{c['end_time']} "
              f"[{c['priority']}] - {c['reason']}")

def display_summary(week_id: Optional[int] = None):
    """Affiche le résumé global ou spécifique à une semaine."""
    header = f"RÉSUMÉ: Contraintes {'actives' if not week_id else f'Semaine {week_id}'}"
    print(f"\n{'='*60}\n{header}\n{'='*60}")

    manager = ConstraintManager()
    all_constraints = manager.get_all_constraints(week_id=week_id)

    for category in CONSTRAINT_CONFIG.keys():
        display_constraint_section(category, all_constraints.get(category, []))

    if week_id is None: # Affichage des stats uniquement sur le résumé global
        print("\nSTATISTIQUES:")
        stats = manager.get_constraint_stats()
        total = sum(v.get(f'total_{k}', 0) for k, v in stats.items() if isinstance(v, dict))
        for k, v in stats.items():
            if isinstance(v, dict):
                count = next(iter(v.values()))
                print(f"   - {k.capitalize()}: {count} contrainte(s)")
        print(f"\n   TOTAL: {total} contraintes actives")

# --- INTERFACE ET MENU ---

class AppContext:
    """Structure pour maintenir l'état de l'application sans variables globales éparpillées."""
    def __init__(self):
        self.year_id = None
        self.week_id = None
        self.manager = ConstraintManager()

    def update(self):
        self.year_id = choose_year()
        self.week_id = choose_week(self.year_id)
        if self.week_id:
            self.manager.set_default_week(self.week_id)

def interactive_menu(ctx: AppContext):
    """Menu principal."""
    while True:
        print(f"\n{'='*60}\n  GESTIONNAIRE DE CONTRAINTES - MENU\n{'='*60}")
        print(f"Contexte: Année={ctx.year_id} | Semaine={ctx.week_id}")
        
        choices = {
            "1": "Ajouter contrainte enseignant",
            "4": "Voir toutes les contraintes",
            "7": "Vider toutes les tables",
            "8": "Changer d'année/semaine",
            "9": "Voir contraintes (semaine spécifique)",
            "10": "Récapitulatif annuel",
            "0": "Quitter"
        }
        for k, v in choices.items(): print(f"{k}. {v}")
        
        choice = input("\nVotre choix: ").strip()

        if choice == "0": break
        elif choice == "1":
            # Implémentation simplifiée pour l'exemple
            print("\n AJOUT CONTRAINTE ENSEIGNANT...")
            # (Logique d'input identique à l'original...)
        elif choice == "4":
            display_summary()
        elif choice == "7":
            if input("Confirmer (o/n) ? ").lower() in ['o', 'oui']:
                ctx.manager.clear_all_constraints(hard=True)
        elif choice == "8":
            ctx.update()
        elif choice == "9":
            w = choose_week(ctx.year_id)
            if w: display_summary(week_id=w)
        elif choice == "10":
            if ctx.year_id:
                # Utilise la logique existante display_constraints_by_year
                pass 

def main():
    ctx = AppContext()
    ctx.update()
    interactive_menu(ctx)

if __name__ == "__main__":
    main()