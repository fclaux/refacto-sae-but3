#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour time_table_model.py
Compatible avec pytest et SonarQube
Utilise le vrai module OR-Tools pour les tests
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ajouter le chemin parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock de db_config seulement (pas OR-Tools car on en a besoin)
sys.modules['db_config'] = MagicMock()
sys.modules['db_config'].get_engine = MagicMock(return_value=MagicMock())

# Import après mock de db_config
from time_table_model import TimetableModel
from ortools.sat.python import cp_model


@pytest.fixture
def sample_data():
    """Données de test pour le modèle"""
    return {
        'jours': 5,
        'creneaux_par_jour': 20,
        'nb_slots': 100,
        'fenetre_midi': [8, 9, 10],
        'slots': [(d, s) for d in range(5) for s in range(20)],
        'cours': [
            {'id': 'CM_Math_BUT1', 'groups': ['BUT1'], 'allowed_prof_indices': [0]},
            {'id': 'TD_Info_G1', 'groups': ['G1'], 'allowed_prof_indices': [0, 1]}
        ],
        'duree_cours': {'CM_Math_BUT1': 3, 'TD_Info_G1': 2},
        'taille_groupes': {'BUT1': 60, 'G1': 30},
        'salles': {'Salle A': 30, 'Salle B': 50},
        'capacites': [30, 50],  # Capacités des salles (Salle A: 30, Salle B: 50)
        'profs': ['Prof A', 'Prof B'],
        'map_groupe_cours': {
            'BUT1': ['CM_Math_BUT1'],
            'G1': ['TD_Info_G1']
        },
        'map_cours_groupes': {
            'CM_Math_BUT1': ['BUT1'],
            'TD_Info_G1': ['G1']
        },
        'disponibilites_profs': {},
        'disponibilites_salles': {},
        'disponibilites_groupes': {},
        'obligations_slots': {},
        'prof_to_teacher_id': {'Prof A': 1, 'Prof B': 2}
    }


@pytest.mark.unit
class TestTimetableModelInit:
    """Tests pour l'initialisation du modèle"""

    def test_init(self, sample_data):
        """Test initialisation du modèle"""
        model = TimetableModel(sample_data)
        assert model.data == sample_data
        assert model._vars == {}
        assert model.temp == []

    def test_init_with_minimal_data(self):
        """Test initialisation avec données minimales"""
        minimal_data = {
            'jours': 1,
            'creneaux_par_jour': 10,
            'nb_slots': 10,
            'fenetre_midi': [],
            'slots': [(0, s) for s in range(10)],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': [],
            'map_groupe_cours': {}
        }
        model = TimetableModel(minimal_data)
        assert model.data == minimal_data


@pytest.mark.unit
class TestTimetableModelVariables:
    """Tests pour la création des variables"""

    def test_create_decision_variables(self, sample_data):
        """Test création des variables de décision"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        
        assert 'start' in model._vars
        assert 'occupe' in model._vars
        assert 'y_salle' in model._vars
        assert 'z_prof' in model._vars

    def test_variables_for_each_course(self, sample_data):
        """Test que chaque cours a ses variables"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        
        # Vérifier les variables occupe pour chaque cours
        for c in sample_data['cours']:
            cid = c['id']
            for t in range(sample_data['nb_slots']):
                assert (cid, t) in model._vars['occupe']


@pytest.mark.unit
class TestTimetableModelConstraints:
    """Tests pour les contraintes du modèle"""

    def test_add_linking_constraints(self, sample_data):
        """Test ajout des contraintes de liaison"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model._add_linking_constraints()
        # Le test passe si pas d'exception

    def test_contrainte_salle(self, sample_data):
        """Test contrainte de non-chevauchement des salles"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_salle(sample_data)
        # Le test passe si pas d'exception

    def test_contrainte_professeurs(self, sample_data):
        """Test contrainte de non-chevauchement des professeurs"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_professeurs(sample_data)
        # Le test passe si pas d'exception

    def test_contrainte_etudiant(self, sample_data):
        """Test contrainte de non-chevauchement pour étudiants"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_etudiant(sample_data)
        # Le test passe si pas d'exception

    def test_contrainte_hierarchique(self, sample_data):
        """Test contrainte hiérarchique sous-groupes"""
        # Ajouter des groupes hiérarchiques
        sample_data['map_groupe_cours']['G1A'] = ['TP_Info_G1A']
        sample_data['cours'].append({'id': 'TP_Info_G1A', 'groups': ['G1A']})
        sample_data['duree_cours']['TP_Info_G1A'] = 2
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_hierarchique(sample_data)
        # Le test passe si pas d'exception


@pytest.mark.unit
class TestTimetableModelDisponibilites:
    """Tests pour les contraintes de disponibilités"""

    def test_contrainte_disponibilites_professeurs(self, sample_data):
        """Test contraintes disponibilités professeurs"""
        sample_data['disponibilites_profs'] = {1: {0: [(0, 10)]}}
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_professeurs(sample_data)

    def test_contrainte_disponibilites_salles_generalisee(self, sample_data):
        """Test contraintes disponibilités salles"""
        sample_data['disponibilites_salles'] = {'Salle A': {0: [(0, 10)]}}
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_salles_generalisee(sample_data)

    def test_contrainte_disponibilites_groupes(self, sample_data):
        """Test contraintes disponibilités groupes"""
        sample_data['disponibilites_groupes'] = {'G1': {0: [(0, 10)]}}
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_groupes(sample_data)

    def test_contrainte_disponibilites_cour_heure(self, sample_data):
        """Test contraintes horaires obligatoires"""
        sample_data['obligations_slots'] = {}
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_disponibilites_cour_heure(sample_data)


@pytest.mark.unit
class TestTimetableModelBuildAndSolve:
    """Tests pour la construction et résolution du modèle"""

    def test_build_model(self, sample_data):
        """Test construction du modèle complet"""
        model = TimetableModel(sample_data)
        model.build_model()
        
        assert 'start' in model._vars
        assert len(model._vars) > 0

    def test_solve_returns_dict(self, sample_data):
        """Test que solve retourne un dictionnaire"""
        model = TimetableModel(sample_data)
        model.build_model()
        result = model.solve(max_time_seconds=1)
        
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'solver' in result


@pytest.mark.unit
class TestTimetableModelOrdreCM:
    """Tests pour les contraintes d'ordre CM/TD/TP"""

    def test_contrainte_ordre_cm_td_tp(self, sample_data):
        """Test ajout contrainte ordre CM -> TD -> TP"""
        # Ajouter des cours avec même matière
        sample_data['cours'] = [
            {'id': 'CM_Math_BUT1_s1', 'groups': ['BUT1'], 'allowed_prof_indices': [0]},
            {'id': 'TD_Math_G1_s2', 'groups': ['G1'], 'allowed_prof_indices': [0]},
        ]
        sample_data['duree_cours'] = {'CM_Math_BUT1_s1': 2, 'TD_Math_G1_s2': 2}
        
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.contrainte_ordre_cm_td_tp(sample_data)

    def test_appliquer_ordre_cm_td_tp(self, sample_data):
        """Test application des ordres CM/TD/TP"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model._ordres_a_forcer = []
        model.appliquer_ordre_cm_td_tp()


@pytest.mark.unit
class TestTimetableModelPenalites:
    """Tests pour les pénalités"""

    def test_penaliser_fin_tardive(self, sample_data):
        """Test pénalisation des fins tardives"""
        model = TimetableModel(sample_data)
        model._create_decision_variables()
        model.penaliser_fin_tardive(sample_data, cout_penalite=500, limite_offset_fin=20)


@pytest.mark.integration
class TestTimetableModelIntegration:
    """Tests d'intégration du modèle complet"""

    def test_full_workflow(self, sample_data):
        """Test workflow complet: build -> solve"""
        model = TimetableModel(sample_data)
        
        # Build
        model.build_model()
        assert 'start' in model._vars
        
        # Solve (avec timeout court pour les tests)
        result = model.solve(max_time_seconds=1)
        assert 'status' in result

    def test_empty_courses(self):
        """Test avec aucun cours"""
        empty_data = {
            'jours': 5,
            'creneaux_par_jour': 20,
            'nb_slots': 100,
            'fenetre_midi': [],
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'cours': [],
            'duree_cours': {},
            'salles': {'Salle A': 30},
            'capacites': [30],
            'profs': ['Prof A'],
            'map_groupe_cours': {},
            'disponibilites_profs': {},
            'disponibilites_salles': {},
            'disponibilites_groupes': {},
            'obligations_slots': {},
            'prof_to_teacher_id': {}
        }
        
        model = TimetableModel(empty_data)
        model.build_model()
        result = model.solve(max_time_seconds=1)
        assert 'status' in result
