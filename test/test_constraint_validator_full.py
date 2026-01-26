#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour constraint_validator.py
Couverture étendue des méthodes de validation
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import time
import sys
import os

# Ajouter le chemin parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
bouton_dir = os.path.join(parent_dir, 'bouton')
sys.path.insert(0, parent_dir)
sys.path.insert(0, bouton_dir)

try:
    from constraint_validator import ConstraintValidator
    from constraint_manager import ConstraintManager
except ImportError as e:
    pytest.skip(f"Modules de contraintes non disponibles: {e}", allow_module_level=True)


@pytest.fixture
def mock_manager():
    """Mock du ConstraintManager"""
    with patch('constraint_manager.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)
        mock_cursor.fetchall.return_value = []
        
        manager = ConstraintManager()
        yield manager


@pytest.fixture
def validator_with_constraints():
    """Validator avec des contraintes mockées"""
    with patch('constraint_manager.get_db_connection') as mock_conn:
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (0,)
        
        # Simuler des contraintes
        mock_cursor.fetchall.side_effect = [
            # teachers
            [{'id': 1, 'teacher_id': 1, 'day_of_week': 'Lundi', 
              'start_time': '08:00', 'end_time': '10:00', 
              'reason': 'Reunion', 'priority': 'hard',
              'first_name': 'Jean', 'last_name': 'Dupont'}],
            # rooms
            [{'id': 2, 'room_id': 10, 'day_of_week': 'Mardi',
              'start_time': '14:00', 'end_time': '16:00',
              'reason': 'Maintenance', 'priority': 'soft',
              'room_name': 'Salle A'}],
            # groups
            [{'id': 3, 'group_id': 5, 'day_of_week': 'Mercredi',
              'start_time': '12:00', 'end_time': '14:00',
              'reason': 'Pause', 'priority': 'medium',
              'group_name': 'G1'}]
        ]
        
        validator = ConstraintValidator()
        yield validator


@pytest.mark.unit
class TestConstraintValidatorTimeConversion:
    """Tests pour les conversions de temps"""

    def test_time_to_slot_index_standard(self, mock_manager):
        """Test conversion heure standard vers index"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._time_to_slot_index('8:00') == 0
            assert validator._time_to_slot_index('9:00') == 2
            assert validator._time_to_slot_index('12:00') == 8

    def test_time_to_slot_index_with_seconds(self, mock_manager):
        """Test conversion heure avec secondes"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._time_to_slot_index('08:30:00')
            assert result == 1

    def test_time_to_slot_index_non_standard(self, mock_manager):
        """Test conversion heure non standard"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._time_to_slot_index('07:45')
            assert result >= 0

    def test_slot_index_to_time_standard(self, mock_manager):
        """Test conversion index vers heure"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._slot_index_to_time(0) == '8:00'
            assert validator._slot_index_to_time(1) == '8:30'

    def test_slot_index_to_time_out_of_range(self, mock_manager):
        """Test conversion index hors plage"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._slot_index_to_time(50)
            assert ':' in result


@pytest.mark.unit
class TestConstraintValidatorOverlap:
    """Tests pour la détection de chevauchement"""

    def test_check_time_overlap_overlapping(self, mock_manager):
        """Test chevauchement détecté"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._check_time_overlap('8:00', '10:00', '9:00', '11:00')
            assert result is True

    def test_check_time_overlap_adjacent(self, mock_manager):
        """Test créneaux adjacents (pas de chevauchement)"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._check_time_overlap('8:00', '10:00', '10:00', '12:00')
            assert result is False

    def test_check_time_overlap_no_overlap(self, mock_manager):
        """Test sans chevauchement"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._check_time_overlap('8:00', '10:00', '14:00', '16:00')
            assert result is False

    def test_check_time_overlap_contained(self, mock_manager):
        """Test créneau contenu dans l'autre"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator._check_time_overlap('8:00', '12:00', '9:00', '11:00')
            assert result is True


@pytest.mark.unit
class TestConstraintValidatorPriority:
    """Tests pour la gestion des priorités"""

    def test_priority_level_hard(self, mock_manager):
        """Test niveau priorité hard"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._priority_level('hard') == 3
            assert validator._priority_level('HARD') == 3

    def test_priority_level_medium(self, mock_manager):
        """Test niveau priorité medium"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._priority_level('medium') == 2

    def test_priority_level_soft(self, mock_manager):
        """Test niveau priorité soft"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._priority_level('soft') == 1

    def test_priority_level_unknown(self, mock_manager):
        """Test niveau priorité inconnu"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            assert validator._priority_level('unknown') == 0


@pytest.mark.unit
class TestConstraintValidatorValidation:
    """Tests pour les méthodes de validation"""

    def test_validate_teacher_availability_no_constraint(self, mock_manager):
        """Test validation enseignant sans contrainte"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            is_valid, priority, message = validator.validate_teacher_availability(
                999, 'Lundi', '08:00', '10:00'
            )
            
            assert is_valid is True
            assert priority is None
            assert message == "OK"

    def test_validate_room_availability_no_constraint(self, mock_manager):
        """Test validation salle sans contrainte"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            is_valid, priority, message = validator.validate_room_availability(
                999, 'Mardi', '14:00', '16:00'
            )
            
            assert is_valid is True

    def test_validate_group_availability_no_constraint(self, mock_manager):
        """Test validation groupe sans contrainte"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            is_valid, priority, message = validator.validate_group_availability(
                999, 'Mercredi', '10:00', '12:00'
            )
            
            assert is_valid is True


@pytest.mark.unit
class TestConstraintValidatorBlockedSlots:
    """Tests pour la récupération des slots bloqués"""

    def test_get_blocked_slots_for_teacher_empty(self, mock_manager):
        """Test slots bloqués enseignant - vide"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            blocked = validator.get_blocked_slots_for_teacher(999)
            assert isinstance(blocked, dict)
            assert len(blocked) == 0

    def test_get_blocked_slots_for_room_empty(self, mock_manager):
        """Test slots bloqués salle - vide"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            blocked = validator.get_blocked_slots_for_room(999)
            assert isinstance(blocked, dict)

    def test_get_blocked_slots_for_group_empty(self, mock_manager):
        """Test slots bloqués groupe - vide"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            blocked = validator.get_blocked_slots_for_group(999)
            assert isinstance(blocked, dict)


@pytest.mark.unit
class TestConstraintValidatorCourseSlot:
    """Tests pour la validation de créneaux de cours"""

    def test_validate_course_slot_all_valid(self, mock_manager):
        """Test validation créneau cours - tout valide"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator.validate_course_slot(
                teacher_id=1,
                room_id=10,
                group_ids=[5],
                day='Lundi',
                start_time='08:00',
                end_time='10:00'
            )
            
            assert result['is_valid'] is True
            assert result['can_proceed'] is True
            assert result['violations'] == []

    def test_validate_course_slot_with_multiple_groups(self, mock_manager):
        """Test validation créneau avec plusieurs groupes"""
        with patch('constraint_manager.get_db_connection'):
            validator = ConstraintValidator(manager=mock_manager)
            
            result = validator.validate_course_slot(
                teacher_id=1,
                room_id=10,
                group_ids=[5, 6, 7],
                day='Lundi',
                start_time='08:00',
                end_time='10:00'
            )
            
            assert 'is_valid' in result
            assert 'violations' in result


@pytest.mark.unit
class TestConstraintValidatorWithRealConstraints:
    """Tests avec des contraintes réelles dans le validator"""

    def test_validate_teacher_with_hard_constraint(self):
        """Test validation enseignant avec contrainte hard"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            # Ajouter manuellement une contrainte
            validator.teacher_constraints_by_id = {
                1: [{
                    'day_of_week': 'Lundi',
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'priority': 'hard',
                    'reason': 'Reunion',
                    'first_name': 'Jean',
                    'last_name': 'Dupont'
                }]
            }
            
            is_valid, priority, message = validator.validate_teacher_availability(
                1, 'Lundi', '09:00', '11:00'
            )
            
            assert is_valid is False
            assert priority == 'hard'
            assert 'indisponible' in message.lower()

    def test_validate_room_with_soft_constraint(self):
        """Test validation salle avec contrainte soft"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.room_constraints_by_id = {
                10: [{
                    'day_of_week': 'Mardi',
                    'start_time': '14:00',
                    'end_time': '16:00',
                    'priority': 'soft',
                    'reason': 'Maintenance prévue',
                    'room_name': 'Salle A'
                }]
            }
            
            is_valid, priority, message = validator.validate_room_availability(
                10, 'Mardi', '15:00', '17:00'
            )
            
            assert is_valid is False
            assert priority == 'soft'
            assert 'Salle A' in message

    def test_validate_group_with_medium_constraint(self):
        """Test validation groupe avec contrainte medium"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.group_constraints_by_id = {
                5: [{
                    'day_of_week': 'Mercredi',
                    'start_time': '12:00',
                    'end_time': '14:00',
                    'priority': 'medium',
                    'reason': 'Pause déjeuner',
                    'group_name': 'Groupe A'
                }]
            }
            
            is_valid, priority, message = validator.validate_group_availability(
                5, 'Mercredi', '12:30', '13:30'
            )
            
            assert is_valid is False
            assert priority == 'medium'
            assert 'Groupe A' in message

    def test_get_blocked_slots_with_hard_constraints(self):
        """Test récupération slots bloqués avec contraintes hard"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.teacher_constraints_by_id = {
                1: [
                    {
                        'day_of_week': 'Lundi',
                        'start_time': '08:00',
                        'end_time': '10:00',
                        'priority': 'hard',
                        'reason': 'Reunion'
                    },
                    {
                        'day_of_week': 'Lundi',
                        'start_time': '14:00',
                        'end_time': '16:00',
                        'priority': 'soft',  # Ne devrait pas être inclus
                        'reason': 'Preference'
                    }
                ]
            }
            
            blocked = validator.get_blocked_slots_for_teacher(1)
            
            assert 'Lundi' in blocked
            assert len(blocked['Lundi']) == 1  # Seulement la contrainte hard
            assert ('08:00', '10:00') in blocked['Lundi']

    def test_get_blocked_slots_for_room_with_constraints(self):
        """Test récupération slots bloqués pour salle"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.room_constraints_by_id = {
                10: [{
                    'day_of_week': 'Mardi',
                    'start_time': '08:00',
                    'end_time': '12:00',
                    'priority': 'hard',
                    'reason': 'Travaux'
                }]
            }
            
            blocked = validator.get_blocked_slots_for_room(10)
            
            assert 'Mardi' in blocked
            assert ('08:00', '12:00') in blocked['Mardi']

    def test_get_blocked_slots_for_group_with_constraints(self):
        """Test récupération slots bloqués pour groupe"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.group_constraints_by_id = {
                5: [{
                    'day_of_week': 'Vendredi',
                    'start_time': '16:00',
                    'end_time': '18:00',
                    'priority': 'hard',
                    'reason': 'Examen'
                }]
            }
            
            blocked = validator.get_blocked_slots_for_group(5)
            
            assert 'Vendredi' in blocked
            assert ('16:00', '18:00') in blocked['Vendredi']

    def test_validate_course_slot_with_violations(self):
        """Test validation créneau avec violations"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.teacher_constraints_by_id = {
                1: [{
                    'day_of_week': 'Lundi',
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'priority': 'hard',
                    'reason': 'Reunion',
                    'first_name': 'Jean',
                    'last_name': 'Dupont'
                }]
            }
            
            result = validator.validate_course_slot(
                teacher_id=1,
                room_id=10,
                group_ids=[5],
                day='Lundi',
                start_time='09:00',
                end_time='11:00'
            )
            
            assert result['is_valid'] is False
            assert result['can_proceed'] is False
            assert len(result['violations']) > 0
            assert result['violations'][0]['type'] == 'teacher'

    def test_validate_course_slot_with_soft_violations(self):
        """Test validation créneau avec violations soft"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.room_constraints_by_id = {
                10: [{
                    'day_of_week': 'Mardi',
                    'start_time': '14:00',
                    'end_time': '16:00',
                    'priority': 'soft',
                    'reason': 'Preference',
                    'room_name': 'Salle B'
                }]
            }
            
            result = validator.validate_course_slot(
                teacher_id=1,
                room_id=10,
                group_ids=[5],
                day='Mardi',
                start_time='15:00',
                end_time='17:00'
            )
            
            # Soft violations n'empêchent pas de procéder
            assert result['is_valid'] is True
            assert result['can_proceed'] is True
            assert result['has_soft_violations'] is True

    def test_validate_teacher_with_no_reason(self):
        """Test validation enseignant sans raison fournie"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.teacher_constraints_by_id = {
                1: [{
                    'day_of_week': 'Lundi',
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'priority': 'hard',
                    'reason': None,  # Pas de raison
                    'first_name': 'Jean',
                    'last_name': 'Dupont'
                }]
            }
            
            is_valid, priority, message = validator.validate_teacher_availability(
                1, 'Lundi', '09:00', '11:00'
            )
            
            assert is_valid is False
            assert 'Indisponibilité' in message

    def test_validate_multiple_constraints_same_day(self):
        """Test avec plusieurs contraintes le même jour"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.teacher_constraints_by_id = {
                1: [
                    {
                        'day_of_week': 'Lundi',
                        'start_time': '08:00',
                        'end_time': '10:00',
                        'priority': 'soft',
                        'reason': 'Pref matin',
                        'first_name': 'Jean',
                        'last_name': 'Dupont'
                    },
                    {
                        'day_of_week': 'Lundi',
                        'start_time': '09:00',
                        'end_time': '11:00',
                        'priority': 'hard',
                        'reason': 'Reunion importante',
                        'first_name': 'Jean',
                        'last_name': 'Dupont'
                    }
                ]
            }
            
            is_valid, priority, message = validator.validate_teacher_availability(
                1, 'Lundi', '09:30', '10:30'
            )
            
            # La priorité la plus haute devrait être retournée
            assert is_valid is False
            assert priority == 'hard'

    def test_validate_different_day_no_conflict(self):
        """Test contrainte sur jour différent - pas de conflit"""
        with patch('constraint_manager.get_db_connection') as mock_conn:
            mock_connection = MagicMock()
            mock_cursor = MagicMock()
            mock_conn.return_value = mock_connection
            mock_connection.cursor.return_value = mock_cursor
            mock_cursor.fetchone.return_value = (0,)
            mock_cursor.fetchall.return_value = []
            
            validator = ConstraintValidator()
            validator.teacher_constraints_by_id = {
                1: [{
                    'day_of_week': 'Lundi',
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'priority': 'hard',
                    'reason': 'Reunion',
                    'first_name': 'Jean',
                    'last_name': 'Dupont'
                }]
            }
            
            # Tester sur un autre jour
            is_valid, priority, message = validator.validate_teacher_availability(
                1, 'Mardi', '08:00', '10:00'
            )
            
            assert is_valid is True
            assert message == "OK"
