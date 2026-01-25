#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from constraint_manager import ConstraintManager, ConstraintPriority

# Configuration globale
WORKING_DAYS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]

def resolve_week_context(manager: ConstraintManager, week_id: int = None, force_permanent: bool = False):
    """
    Détermine l'ID de semaine réel et son libellé associé.
    Centralise la logique de décision du contexte temporel.
    """
    if force_permanent:
        return None, "PERMANENTE"
    
    actual_id = week_id if week_id is not None else manager.default_week_id
    label = f"semaine {actual_id}" if actual_id else "PERMANENTE"
    return actual_id, label

def get_all_group_ids(manager: ConstraintManager):
    """Récupère la liste des groupes via le manager pour éviter le SQL brut ici."""
    # On suppose que le manager a une méthode pour lister les entités 
    # ou on utilise une requête simple via sa connexion interne
    conn = manager._get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, name FROM `groups` ORDER BY name")
        return cursor.fetchall()
    finally:
        cursor.close()

def add_no_course_slot(manager: ConstraintManager, start_time: str, end_time: str, reason: str, week_id=None, force_permanent=False):
    """
    Ajoute une contrainte de créneau bloqué pour tous les groupes sur tous les jours ouvrés.
    """
    groups = get_all_group_ids(manager)
    if not groups:
        print("⚠ Aucun groupe trouvé dans la base.")
        return

    actual_week_id, week_label = resolve_week_context(manager, week_id, force_permanent)
    
    print(f"\n🚀 Blocage global ({start_time}-{end_time}) | Contexte: {week_label}")
    print(f"   Raison: {reason}")

    success_count = 0
    for group in groups:
        for day in WORKING_DAYS:
            try:
                manager.add_group_unavailability(
                    group_id=group['id'],
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    reason=reason,
                    priority=ConstraintPriority.HARD,
                    week_id=actual_week_id
                )
                success_count += 1
            except Exception as e:
                print(f"  ❌ Erreur [{group['name']} - {day}]: {e}")

    print(f"\n✅ Opération terminée : {success_count} contraintes créées.")
    print(f"   Groupes impactés : {', '.join([g['name'] for g in groups])}")

def main():
    manager = ConstraintManager()
    
    print(f"\n{'='*60}\n  GESTIONNAIRE DE CRÉNEAUX BLOQUÉS\n{'='*60}")
    print("1. Ajouter un blocage global (ex: Pause déjeuner)")
    print("0. Quitter")

    if input("\nVotre choix: ").strip() != "1":
        return print("Au revoir !")

    # Collecte des informations
    start = input("Début (HH:MM): ").strip()
    end = input("Fin (HH:MM): ").strip()
    reason = input("Raison: ").strip()
    
    is_perm = input("Permanent ? (o/n) [o]: ").strip().lower() != 'n'
    w_id = None
    if not is_perm:
        w_input = input("ID Semaine spécifique (vide pour défaut) : ").strip()
        w_id = int(w_input) if w_input else None

    if input(f"\nConfirmer le blocage {start}-{end} pour TOUS les groupes ? (o/n): ").lower() == 'o':
        add_no_course_slot(manager, start, end, reason, week_id=w_id, force_permanent=is_perm)
    else:
        print("🚫 Opération annulée.")

if __name__ == "__main__":
    main()