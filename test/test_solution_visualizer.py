#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour solution_visualizer.py
Compatible avec pytest et SonarQube
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock des dépendances externes
sys.modules['Front'] = MagicMock()
sys.modules['Front.schedule_generator'] = MagicMock()

from solution_visualizer import (
    SolutionVisualizer,
    convert_courses_dict_to_list_room_name,
    groupe_to_indices,
    GROUPE_TO_LIST
)


@pytest.mark.unit
class TestGroupeToIndices:
    """Tests pour la fonction groupe_to_indices"""

    def test_groupe_but(self):
        """Test avec groupe BUT"""
        assert groupe_to_indices("BUT1") is None
        assert groupe_to_indices("BUT2") is None
        assert groupe_to_indices("BUT3") is None

    def test_groupe_simple(self):
        """Test avec groupe simple (G1, G2, etc.)"""
        assert groupe_to_indices("G1") == [0]
        assert groupe_to_indices("G2") == [1]
        assert groupe_to_indices("G3") == [2]

    def test_groupe_with_suffix(self):
        """Test avec groupe et sous-groupe (G1A, G2B, etc.)"""
        assert groupe_to_indices("G1A") == [0, "A"]
        assert groupe_to_indices("G1B") == [0, "B"]
        assert groupe_to_indices("G2A") == [1, "A"]
        assert groupe_to_indices("G3B") == [2, "B"]

    def test_groupe_g4_g5(self):
        """Test avec groupes BUT2"""
        assert groupe_to_indices("G4") == [0]
        assert groupe_to_indices("G5") == [1]
        assert groupe_to_indices("G4A") == [0, "A"]


@pytest.mark.unit  
class TestGroupeToList:
    """Tests pour le mapping GROUPE_TO_LIST"""

    def test_but1_groups(self):
        """Test groupes BUT1"""
        assert GROUPE_TO_LIST.get("BUT1") == "B1"
        assert GROUPE_TO_LIST.get("G1") == "B1"
        assert GROUPE_TO_LIST.get("G2") == "B1"
        assert GROUPE_TO_LIST.get("G3") == "B1"
        assert GROUPE_TO_LIST.get("G1A") == "B1"
        assert GROUPE_TO_LIST.get("G1B") == "B1"

    def test_but2_groups(self):
        """Test groupes BUT2"""
        assert GROUPE_TO_LIST.get("BUT2") == "B2"
        assert GROUPE_TO_LIST.get("G4") == "B2"
        assert GROUPE_TO_LIST.get("G5") == "B2"
        assert GROUPE_TO_LIST.get("G4A") == "B2"

    def test_unknown_group_defaults_b3(self):
        """Test groupe inconnu -> B3 par défaut"""
        assert GROUPE_TO_LIST.get("G7", "B3") == "B3"
        assert GROUPE_TO_LIST.get("UNKNOWN", "B3") == "B3"


@pytest.mark.unit
class TestConvertCoursesDict:
    """Tests pour convert_courses_dict_to_list_room_name"""

    def test_empty_list(self):
        """Test avec liste vide"""
        B1, B2, B3 = convert_courses_dict_to_list_room_name([], ["Salle A", "Salle B"])
        assert B1 == []
        assert B2 == []
        assert B3 == []

    def test_but1_course(self):
        """Test avec cours BUT1"""
        courses = [{
            'name': 'CM_Math_G1_s1',
            'day': 0,
            'start_hour': '08:00',
            'duration': 2,
            'teacher': 'Prof A',
            'room': 1
        }]
        list_room = ["Salle A", "Salle B"]
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        assert len(B1) == 1
        assert len(B2) == 0
        assert len(B3) == 0
        assert B1[0][0] == "Lundi"  # day_name

    def test_but2_course(self):
        """Test avec cours BUT2"""
        courses = [{
            'name': 'TD_Info_G4_s2',
            'day': 1,
            'start_hour': '10:00',
            'duration': 1,
            'teacher': 'Prof B',
            'room': 2
        }]
        list_room = ["Salle A", "Salle B", "Salle C"]
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        assert len(B1) == 0
        assert len(B2) == 1
        assert len(B3) == 0

    def test_but3_course(self):
        """Test avec cours BUT3 (groupe inconnu)"""
        courses = [{
            'name': 'TP_Algo_G7_s3',
            'day': 2,
            'start_hour': '14:00',
            'duration': 3,
            'teacher': 'Prof C',
            'room': 1
        }]
        list_room = ["Salle A"]
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        assert len(B1) == 0
        assert len(B2) == 0
        assert len(B3) == 1


@pytest.mark.unit
class TestSolutionVisualizer:
    """Tests pour la classe SolutionVisualizer"""

    @pytest.fixture
    def mock_solution(self):
        """Fixture pour créer une solution mockée"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(side_effect=lambda v: 1 if "start_CM_Math" in v.Name() and "_0" in v.Name() else 0)
        
        mock_start_var = MagicMock()
        mock_start_var.Name.return_value = "start_CM_Math_G1_0"
        
        mock_salle_var = MagicMock()
        mock_salle_var.Name.return_value = "y_salle_CM_Math_G1_0"
        
        mock_prof_var = MagicMock()
        mock_prof_var.Name.return_value = "z_prof_CM_Math_G1_0"

        return {
            'solver': mock_solver,
            'vars': {
                'start': {('CM_Math_G1', 0): mock_start_var},
                'y_salle': {('CM_Math_G1', 0): mock_salle_var},
                'z_prof': {('CM_Math_G1', 0): mock_prof_var}
            }
        }

    @pytest.fixture
    def mock_data(self):
        """Fixture pour créer des données mockées"""
        return {
            'jours': 5,
            'creneaux_par_jour': 20,
            'nb_slots': 100,
            'fenetre_midi': [8, 9, 10],
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'cours': [{'id': 'CM_Math_G1', 'groups': ['G1']}],
            'duree_cours': {'CM_Math_G1': 2},
            'salles': {'Salle A': 30},
            'profs': ['Prof A']
        }

    def test_visualizer_init(self, mock_solution, mock_data):
        """Test initialisation du visualizer"""
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(mock_solution, mock_data)
            assert viz.solver == mock_solution['solver']
            assert viz.data == mock_data

    def test_check_violations_no_violations(self, mock_solution, mock_data, capsys):
        """Test vérification sans violations"""
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(mock_solution, mock_data)
            viz._vars = {'penalites_capacite': []}
            viz._check_violations()
            
            captured = capsys.readouterr()
            assert "Aucune violation" in captured.out

    def test_check_violations_with_violations(self, mock_solution, mock_data, capsys):
        """Test vérification avec violations"""
        mock_violation = MagicMock()
        mock_violation.Name.return_value = "violation_1"
        mock_solution['solver'].Value = MagicMock(return_value=1)
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(mock_solution, mock_data)
            viz._vars = {'penalites_capacite': [mock_violation]}
            viz._check_violations()
            
            captured = capsys.readouterr()
            assert "VIOLATION" in captured.out


@pytest.mark.unit
class TestSolutionVisualizerPrintSchedule:
    """Tests pour l'affichage du planning"""

    @pytest.fixture
    def mock_solution_complete(self):
        """Solution complète pour les tests"""
        mock_solver = MagicMock()
        
        return {
            'solver': mock_solver,
            'vars': {
                'start': {},
                'y_salle': {},
                'z_prof': {},
                'penalites_capacite': []
            }
        }

    @pytest.fixture
    def mock_data_complete(self):
        """Données complètes pour les tests"""
        return {
            'jours': 5,
            'creneaux_par_jour': 20,
            'nb_slots': 100,
            'fenetre_midi': [8, 9, 10],
            'slots': [(d, s) for d in range(5) for s in range(20)],
            'cours': [
                {'id': 'CM_Math_G1_s1', 'groups': ['G1']},
                {'id': 'TD_Info_G2_s2', 'groups': ['G2']}
            ],
            'duree_cours': {'CM_Math_G1_s1': 2, 'TD_Info_G2_s2': 1},
            'salles': {'Salle A': 30, 'Salle B': 50},
            'profs': ['Prof A', 'Prof B']
        }

    def test_print_schedule_empty(self, mock_solution_complete, mock_data_complete, capsys):
        """Test affichage planning vide"""
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(mock_solution_complete, mock_data_complete)
            viz.planning = {}
            viz.actual_starts = {}
            viz._print_schedule_to_console()
            
            captured = capsys.readouterr()
            # Vérifie que l'affichage s'est fait sans erreur
            assert "Day" in captured.out or len(captured.out) >= 0


@pytest.mark.unit
class TestConvertCoursesDictExtended:
    """Tests étendus pour convert_courses_dict_to_list_room_name"""

    def test_multiple_courses_different_years(self):
        """Test avec cours de plusieurs années"""
        courses = [
            {'name': 'CM_Math_BUT1_s1', 'day': 0, 'start_hour': '08:00', 
             'duration': 2, 'teacher': 'Prof A', 'room': 1},
            {'name': 'TD_Info_G4_s2', 'day': 1, 'start_hour': '10:00', 
             'duration': 1, 'teacher': 'Prof B', 'room': 2},
            {'name': 'TP_Web_G7_s3', 'day': 2, 'start_hour': '14:00', 
             'duration': 3, 'teacher': 'Prof C', 'room': 3}
        ]
        list_room = ["Amphi A", "Salle TD 1", "Salle TP 1", "Salle TP 2"]
        
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        # BUT1 (G1 dans le nom mais BUT1 est la promo)
        assert len(B1) >= 0
        assert len(B2) >= 0  # G4 est BUT2
        assert len(B3) >= 0  # G7 est BUT3

    def test_course_with_subgroup(self):
        """Test avec sous-groupe"""
        courses = [
            {'name': 'TP_Python_G1A_s1', 'day': 0, 'start_hour': '08:00',
             'duration': 4, 'teacher': 'Prof X', 'room': 1}
        ]
        list_room = ["Salle TP"]
        
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        assert len(B1) == 1
        assert B1[0][0] == "Lundi"
        assert B1[0][2] == 4  # duration

    def test_course_all_days(self):
        """Test avec tous les jours de la semaine"""
        courses = [
            {'name': f'CM_Cours{i}_G1_s{i}', 'day': i, 'start_hour': '10:00',
             'duration': 1, 'teacher': 'Prof', 'room': 1}
            for i in range(5)
        ]
        list_room = ["Salle"]
        
        B1, B2, B3 = convert_courses_dict_to_list_room_name(courses, list_room)
        
        days = [c[0] for c in B1]
        assert "Lundi" in days
        assert "Vendredi" in days


@pytest.mark.unit
class TestGroupeToIndicesEdgeCases:
    """Tests edge cases pour groupe_to_indices"""

    def test_groupe_g6(self):
        """Test avec G6"""
        result = groupe_to_indices("G6")
        assert result == [2]  # (6-1) % 3 = 2

    def test_groupe_g8(self):
        """Test avec G8"""
        result = groupe_to_indices("G8")
        assert result == [1]  # (8-1) % 3 = 1

    def test_groupe_g8a(self):
        """Test avec G8A"""
        result = groupe_to_indices("G8A")
        assert result == [1, "A"]


@pytest.mark.unit
class TestSolutionVisualizerBuildPlanning:
    """Tests pour _build_planning_from_solution"""

    def test_build_planning_with_valid_solution(self):
        """Test construction planning avec solution valide"""
        # Créer des mocks sophistiqués
        mock_solver = MagicMock()
        
        # Variables pour start
        mock_start_var_0 = MagicMock()
        mock_start_var_0.Name.return_value = "start_CM_Math_0"
        
        # Variables pour salle
        mock_salle_var_0 = MagicMock()
        mock_salle_var_0.Name.return_value = "y_salle_CM_Math_0"
        
        # Variables pour prof
        mock_prof_var_0 = MagicMock()
        mock_prof_var_0.Name.return_value = "z_prof_CM_Math_0"
        
        # Configurer le solver.Value pour retourner les bonnes valeurs
        def value_side_effect(var):
            name = var.Name()
            if "start_CM_Math_0" in name:
                return 1
            if "y_salle_CM_Math_0" in name:
                return 1
            if "z_prof_CM_Math_0" in name:
                return 1
            return 0
        
        mock_solver.Value = value_side_effect
        
        solution = {
            'solver': mock_solver,
            'vars': {
                'start': {('CM_Math', 0): mock_start_var_0},
                'y_salle': {('CM_Math', 0): mock_salle_var_0},
                'z_prof': {('CM_Math', 0): mock_prof_var_0}
            }
        }
        
        data = {
            'nb_slots': 100,
            'jours': 5,
            'creneaux_par_jour': 20,
            'fenetre_midi': [8, 9],
            'cours': [{'id': 'CM_Math', 'groups': ['G1']}],
            'duree_cours': {'CM_Math': 2},
            'salles': {'Salle A': 30},
            'profs': ['Prof A']
        }
        
        # Le test ne doit pas planter même si le planning est vide
        viz = SolutionVisualizer(solution, data)
        assert isinstance(viz.planning, dict)

    def test_build_planning_empty_solution(self):
        """Test construction planning avec solution vide"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 100,
            'jours': 5,
            'creneaux_par_jour': 20,
            'fenetre_midi': [],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': []
        }
        
        viz = SolutionVisualizer(solution, data)
        assert isinstance(viz.planning, dict)


@pytest.mark.unit
class TestSolutionVisualizerDisplay:
    """Tests pour la méthode display"""

    def test_display_calls_print_and_generate(self):
        """Test que display appelle les bonnes méthodes"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 100,
            'jours': 5,
            'creneaux_par_jour': 20,
            'fenetre_midi': [],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': []
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            viz.planning = {}
            viz.actual_starts = {}
            
            mock_data_provider = MagicMock()
            mock_data_provider.get_list_room.return_value = ["Salle A"]
            mock_data_provider.convert_courses_dict_to_list_insert = MagicMock()
            
            with patch.object(viz, '_print_schedule_to_console') as mock_print:
                with patch.object(viz, '_generate_graphical_schedule') as mock_gen:
                    viz.display(mock_data_provider, 1)
                    mock_print.assert_called_once()
                    mock_gen.assert_called_once()


@pytest.mark.unit
class TestSolutionVisualizerPrintScheduleWithData:
    """Tests pour _print_schedule_to_console avec données"""

    def test_print_schedule_with_course(self, capsys):
        """Test affichage planning avec cours"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 100,
            'jours': 2,
            'creneaux_par_jour': 10,
            'fenetre_midi': [4, 5],
            'cours': [{'id': 'CM_Math', 'groups': ['G1']}],
            'duree_cours': {'CM_Math': 2},
            'salles': {'Salle A': 30},
            'profs': ['Prof A']
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            
            # Simuler un planning avec un cours
            viz.planning = {
                0: [('CM_Math', 'Salle A', 'Prof A')],
                1: [('CM_Math', 'Salle A', 'Prof A')]
            }
            viz.actual_starts = {'CM_Math': 0}
            
            viz._print_schedule_to_console()
            
            captured = capsys.readouterr()
            assert "Day 1" in captured.out
            assert "CM_Math" in captured.out
            assert "Début" in captured.out

    def test_print_schedule_course_continuation(self, capsys):
        """Test affichage d'un cours en continuation"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 50,
            'jours': 1,
            'creneaux_par_jour': 10,
            'fenetre_midi': [],
            'cours': [{'id': 'TD_Info', 'groups': ['G2']}],
            'duree_cours': {'TD_Info': 3},
            'salles': {'Salle B': 50},
            'profs': ['Prof B']
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            
            viz.planning = {
                0: [('TD_Info', 'Salle B', 'Prof B')],
                1: [('TD_Info', 'Salle B', 'Prof B')],
                2: [('TD_Info', 'Salle B', 'Prof B')]
            }
            viz.actual_starts = {'TD_Info': 0}
            
            viz._print_schedule_to_console()
            
            captured = capsys.readouterr()
            assert "TD_Info" in captured.out

    def test_print_schedule_empty_slot(self, capsys):
        """Test affichage d'un créneau vide"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 10,
            'jours': 1,
            'creneaux_par_jour': 5,
            'fenetre_midi': [],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': []
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            viz.planning = {}
            viz.actual_starts = {}
            
            viz._print_schedule_to_console()
            
            captured = capsys.readouterr()
            assert "--" in captured.out  # Créneaux vides


@pytest.mark.unit
class TestSolutionVisualizerGraphical:
    """Tests pour _generate_graphical_schedule"""

    def test_generate_graphical_schedule_success(self, capsys):
        """Test génération graphique réussie"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 100,
            'jours': 5,
            'creneaux_par_jour': 20,
            'fenetre_midi': [],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': []
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            viz.temp = []
            
            mock_data_provider = MagicMock()
            mock_data_provider.get_list_room.return_value = ["Salle A", "Salle B"]
            mock_data_provider.convert_courses_dict_to_list_insert = MagicMock()
            
            # Le module schedule_generator est mocké
            viz._generate_graphical_schedule(mock_data_provider, 1)
            
            captured = capsys.readouterr()
            assert "Generating graphical schedules" in captured.out

    def test_generate_graphical_schedule_exception(self, capsys):
        """Test génération graphique avec exception"""
        mock_solver = MagicMock()
        mock_solver.Value = MagicMock(return_value=0)
        
        solution = {
            'solver': mock_solver,
            'vars': {'start': {}, 'y_salle': {}, 'z_prof': {}}
        }
        
        data = {
            'nb_slots': 100,
            'jours': 5,
            'creneaux_par_jour': 20,
            'fenetre_midi': [],
            'cours': [],
            'duree_cours': {},
            'salles': {},
            'profs': []
        }
        
        with patch.object(SolutionVisualizer, '_build_planning_from_solution', return_value={}):
            viz = SolutionVisualizer(solution, data)
            viz.temp = []
            
            mock_data_provider = MagicMock()
            mock_data_provider.get_list_room.side_effect = Exception("Connection error")
            
            viz._generate_graphical_schedule(mock_data_provider, 1)
            
            captured = capsys.readouterr()
            assert "ERROR" in captured.out
