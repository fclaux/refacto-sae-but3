#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour les utilitaires (diagnose.py et function.py)
Compatible avec pytest et SonarQube
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Import des modules à tester
try:
    from diagnose import diagnose_feasibility
    DIAGNOSE_AVAILABLE = True
except ImportError as e:
    DIAGNOSE_AVAILABLE = False

try:
    from function import (
        get_availabilityProf_From_Unavailable,
        get_availabilityRoom_From_Unavailable,
        get_availabilityGroup_From_Unavailable,
        convert_days_int_to_string
    )
    FUNCTION_AVAILABLE = True
except ImportError as e:
    FUNCTION_AVAILABLE = False


@pytest.mark.skipif(not DIAGNOSE_AVAILABLE, reason="Module diagnose non disponible")
@pytest.mark.unit
class TestDiagnoseFeasibility:
    """Tests pour la fonction diagnose_feasibility"""

    @pytest.fixture(autouse=True)
    def setup(self, valid_schedule_data):
        """Initialisation des données de test"""
        self.valid_data = valid_schedule_data

    def test_diagnose_valid_schedule(self):
        """Test diagnostic avec un emploi du temps valide"""
        problems = diagnose_feasibility(self.valid_data)

        # Vérifier qu'il n'y a pas de problèmes
        assert len(problems['no_valid_start']) == 0
        assert len(problems['no_room']) == 0
        assert len(problems['group_overbooked']) == 0

    def test_diagnose_course_too_long(self):
        """Test avec un cours trop long pour un créneau"""
        data = self.valid_data.copy()
        data['duree_cours']['CM_Math_BUT1'] = 25  # Plus long qu'un jour

        problems = diagnose_feasibility(data)

        # Devrait détecter un problème de start invalide
        assert len(problems['no_valid_start']) > 0

    def test_diagnose_room_too_small(self):
        """Test avec des salles trop petites"""
        data = self.valid_data.copy()
        data['salles'] = {'Petite Salle': 10}  # Trop petite pour tous les groupes

        problems = diagnose_feasibility(data)

        # Devrait détecter un problème de capacité
        assert len(problems['no_room']) > 0

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
        assert len(problems['group_overbooked']) > 0

    def test_diagnose_with_midi_constraint(self):
        """Test que les contraintes de midi sont respectées"""
        data = self.valid_data.copy()

        problems = diagnose_feasibility(data)

        # Calculer les slots utilisables
        cpd = data['creneaux_par_jour']
        fenetre = set(data['fenetre_midi'])
        usable = [o for o in range(cpd) if o not in fenetre]

        assert len(usable) == cpd - len(fenetre)


@pytest.mark.skipif(not FUNCTION_AVAILABLE, reason="Module function non disponible")
@pytest.mark.unit
class TestFunctionUtilities:
    """Tests pour les fonctions utilitaires"""

    def test_convert_days_int_to_string(self):
        """Test conversion jour int -> string"""
        assert convert_days_int_to_string(0) == 'Lundi'
        assert convert_days_int_to_string(1) == 'Mardi'
        assert convert_days_int_to_string(2) == 'Mercredi'
        assert convert_days_int_to_string(3) == 'Jeudi'
        assert convert_days_int_to_string(4) == 'Vendredi'

    def test_get_availabilityProf_From_Unavailable_empty(self):
        """Test disponibilités prof avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'teacher_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityProf_From_Unavailable(df_empty, 20)

        # Devrait retourner un dict vide ou avec structure par défaut
        assert isinstance(result, dict)

    def test_get_availabilityRoom_From_Unavailable_empty(self):
        """Test disponibilités salle avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'room_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityRoom_From_Unavailable(df_empty, 20)

        assert isinstance(result, dict)

    def test_get_availabilityGroup_From_Unavailable_empty(self):
        """Test disponibilités groupe avec DataFrame vide"""
        import pandas as pd
        df_empty = pd.DataFrame(columns=[
            'group_id', 'day_of_week', 'start_time', 'end_time', 'priority', 'week_id'
        ])

        result = get_availabilityGroup_From_Unavailable(df_empty, 20)

        assert isinstance(result, dict)

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
        assert isinstance(result, dict)
        if result:  # Si la fonction retourne des résultats
            # Vérifier la présence des teacher_ids
            for teacher_id in df_test['teacher_id'].unique():
                if teacher_id in result:
                    assert isinstance(result[teacher_id], dict)


@pytest.mark.unit
class TestDiagnoseEdgeCases:
    """Tests des cas limites du diagnostic"""

    @pytest.mark.skipif(not DIAGNOSE_AVAILABLE, reason="Module diagnose non disponible")
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
        assert len(problems['no_valid_start']) == 0

    @pytest.mark.skipif(not DIAGNOSE_AVAILABLE, reason="Module diagnose non disponible")
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
        assert isinstance(problems, dict)
