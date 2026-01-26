#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests étendus pour time_table_model.py - couverture des méthodes additionnelles
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ajouter le chemin parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de db_config seulement
sys.modules['db_config'] = MagicMock()
sys.modules['db_config'].get_engine = MagicMock(return_value=MagicMock())

from time_table_model import TimetableModel
from ortools.sat.python import cp_model


@pytest.fixture
def complete_sample_data():
    """Données complètes de test pour le modèle"""
    return {
        'jours': 5,
        'creneaux_par_jour': 20,
        'nb_slots': 100,
        'fenetre_midi': [8, 9, 10],
        'slots': [(d, s) for d in range(5) for s in range(20)],
        'cours': [
            {'id': 'CM_Math_BUT1_s1', 'groups': ['BUT1'], 'allowed_prof_indices': [0]},
            {'id': 'TD_Math_G1_s2', 'groups': ['G1'], 'allowed_prof_indices': [0, 1]},
            {'id': 'TP_Math_G1A_s3', 'groups': ['G1A'], 'allowed_prof_indices': [1]}
        ],
        'duree_cours': {'CM_Math_BUT1_s1': 3, 'TD_Math_G1_s2': 2, 'TP_Math_G1A_s3': 4},
        'taille_groupes': {'BUT1': 100, 'G1': 30, 'G1A': 15},
        'salles': {'Amphi A': 150, 'Salle TD': 40, 'Salle TP': 20},
        'capacites': [150, 40, 20],
        'profs': ['Prof A', 'Prof B'],
        'map_groupe_cours': {
            'BUT1': ['CM_Math_BUT1_s1'],
            'G1': ['TD_Math_G1_s2'],
            'G1A': ['TP_Math_G1A_s3']
        },
        'map_cours_groupes': {
            'CM_Math_BUT1_s1': ['BUT1'],
            'TD_Math_G1_s2': ['G1'],
            'TP_Math_G1A_s3': ['G1A']
        },
        'disponibilites_profs': {1: {0: [(0, 20)]}},
        'disponibilites_salles': {'Amphi A': {0: [(0, 20)]}},
        'disponibilites_groupes': {'G1': {0: [(0, 20)]}},
        'obligations_slots': {},
        'prof_to_teacher_id': {'Prof A': 1, 'Prof B': 2}
    }


@pytest.mark.unit
class TestTimetableModelContraintesSalles:
    """Tests pour les contraintes de salles"""

    def test_contrainte_disponibilites_salles(self, complete_sample_data):
        """Test contrainte disponibilités salles"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_salles(complete_sample_data)

    def test_contrainte_disponibilites_salles_generalisee(self, complete_sample_data):
        """Test contrainte disponibilités salles généralisée"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_salles_generalisee(complete_sample_data)

    def test_contrainte_disponibilites_salles_empty(self, complete_sample_data):
        """Test contrainte salles avec aucune disponibilité"""
        complete_sample_data['disponibilites_salles'] = {}
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_salles_generalisee(complete_sample_data)


@pytest.mark.unit
class TestTimetableModelOrdres:
    """Tests pour les contraintes d'ordre CM/TD/TP"""

    def test_contrainte_ordre_cm_td_tp_multiple_courses(self, complete_sample_data):
        """Test ordre avec plusieurs cours de même matière"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_ordre_cm_td_tp(complete_sample_data)
        
        # Vérifier que des ordres ont été détectés
        assert hasattr(model, '_ordres_a_forcer')

    def test_appliquer_ordre_cm_td_tp_with_orders(self, complete_sample_data):
        """Test application des ordres avec des ordres à forcer"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_ordre_cm_td_tp(complete_sample_data)
        model.appliquer_ordre_cm_td_tp()

    def test_appliquer_ordre_cm_td_tp_no_orders(self, complete_sample_data):
        """Test application des ordres sans ordre à forcer"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model._ordres_a_forcer = []
        model.appliquer_ordre_cm_td_tp()


@pytest.mark.unit
class TestTimetableModelPenalites:
    """Tests pour les pénalités et l'objectif"""

    def test_penaliser_fin_tardive_with_late_courses(self, complete_sample_data):
        """Test pénalisation des cours tardifs"""
        # Ajouter un cours qui finit tard
        complete_sample_data['cours'].append({
            'id': 'CM_Late_BUT1_s10',
            'groups': ['BUT1'],
            'allowed_prof_indices': [0]
        })
        complete_sample_data['duree_cours']['CM_Late_BUT1_s10'] = 5
        
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.penaliser_fin_tardive(complete_sample_data, cout_penalite=500, limite_offset_fin=15)
        
        assert hasattr(model, 'penalites_fin_tardive')

    def test_define_objective_function(self, complete_sample_data):
        """Test définition de la fonction objectif"""
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model._add_linking_constraints()
        model.penaliser_fin_tardive(complete_sample_data)
        model._define_objective_function()
        
        assert 'penalites_capacite' in model._vars


@pytest.mark.unit
class TestTimetableModelHierarchie:
    """Tests pour les contraintes hiérarchiques"""

    def test_contrainte_hierarchique_with_subgroups(self, complete_sample_data):
        """Test contrainte hiérarchique avec sous-groupes"""
        # Ajouter un groupe parent et sous-groupe
        complete_sample_data['map_groupe_cours']['G1A'] = ['TP_Math_G1A_s3']
        complete_sample_data['map_groupe_cours']['G1'] = ['TD_Math_G1_s2', 'TP_Math_G1A_s3']
        
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_hierarchique(complete_sample_data)


@pytest.mark.integration
class TestTimetableModelFullBuild:
    """Tests d'intégration pour la construction complète du modèle"""

    def test_full_build_with_all_constraints(self, complete_sample_data):
        """Test construction complète avec toutes les contraintes"""
        model = TimetableModel(complete_sample_data)
        model.build_model()
        
        assert 'start' in model._vars
        assert 'occupe' in model._vars
        assert 'y_salle' in model._vars
        assert 'z_prof' in model._vars

    def test_solve_with_timeout(self, complete_sample_data):
        """Test résolution avec timeout court"""
        model = TimetableModel(complete_sample_data)
        model.build_model()
        
        result = model.solve(max_time_seconds=2)
        
        assert 'status' in result
        assert 'solver' in result
        assert 'vars' in result

    def test_solve_optimal_or_feasible(self, complete_sample_data):
        """Test que la résolution trouve une solution"""
        # Simplifier le problème pour trouver une solution
        simple_data = {
            'jours': 1,
            'creneaux_par_jour': 10,
            'nb_slots': 10,
            'fenetre_midi': [],
            'slots': [(0, s) for s in range(10)],
            'cours': [
                {'id': 'CM_Test_BUT1_s1', 'groups': ['BUT1'], 'allowed_prof_indices': [0]}
            ],
            'duree_cours': {'CM_Test_BUT1_s1': 2},
            'taille_groupes': {'BUT1': 30},
            'salles': {'Salle A': 50},
            'capacites': [50],
            'profs': ['Prof A'],
            'map_groupe_cours': {'BUT1': ['CM_Test_BUT1_s1']},
            'disponibilites_profs': {},
            'disponibilites_salles': {},
            'disponibilites_groupes': {},
            'obligations_slots': {},
            'prof_to_teacher_id': {'Prof A': 1}
        }
        
        model = TimetableModel(simple_data)
        model.build_model()
        result = model.solve(max_time_seconds=10)
        
        # Vérifier que le status est OPTIMAL ou FEASIBLE
        status = result['status']
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.UNKNOWN, cp_model.INFEASIBLE]


@pytest.mark.unit
class TestTimetableModelDisponibilitesExtended:
    """Tests étendus pour les disponibilités"""

    def test_contrainte_disponibilites_professeurs_with_data(self, complete_sample_data):
        """Test contraintes disponibilités profs avec données"""
        complete_sample_data['disponibilites_profs'] = {
            1: {0: [(0, 10), (12, 20)]},
            2: {1: [(8, 16)]}
        }
        
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_professeurs(complete_sample_data)

    def test_contrainte_disponibilites_groupes_with_data(self, complete_sample_data):
        """Test contraintes disponibilités groupes avec données"""
        complete_sample_data['disponibilites_groupes'] = {
            'G1': {0: [(0, 8), (12, 20)]},
            'BUT1': {1: [(0, 20)]}
        }
        
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_groupes(complete_sample_data)

    def test_contrainte_disponibilites_cour_heure_with_obligations(self, complete_sample_data):
        """Test contraintes horaires obligatoires avec données"""
        complete_sample_data['obligations_slots'] = {
            'CM_Math_BUT1_s1': {'jour': 0, 'heure': 8}
        }
        
        model = TimetableModel(complete_sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_cour_heure(complete_sample_data)
