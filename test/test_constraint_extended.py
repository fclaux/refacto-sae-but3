#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests additionnels pour le système de contraintes
Couverture étendue pour constraint_manager, constraint_validator, constraint_integration
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
    from constraint_manager import ConstraintManager, ConstraintPriority, ConstraintType
    from constraint_validator import ConstraintValidator
    from constraint_integration import ConstraintIntegration
except ImportError as e:
    pytest.skip(f"Modules de contraintes non disponibles: {e}", allow_module_level=True)


@pytest.mark.unit
class TestConstraintManagerExtended:
    """Tests étendus pour le ConstraintManager"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration avant chaque test"""
        self.patcher = patch('constraint_manager.get_db_connection')
        self.mock_get_conn = self.patcher.start()
        
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_get_conn.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (1,)  # Simule qu'une ligne existe
        self.mock_cursor.fetchall.return_value = []
        self.mock_cursor.lastrowid = 100
        self.mock_cursor.rowcount = 1
        
        self.manager = ConstraintManager()
        yield
        self.patcher.stop()

    def test_constraint_type_enum(self):
        """Test des valeurs de l'enum ConstraintType"""
        assert ConstraintType.TEACHER_UNAVAILABLE.value == "teacher_unavailable"
        assert ConstraintType.ROOM_UNAVAILABLE.value == "room_unavailable"
        assert ConstraintType.GROUP_UNAVAILABLE.value == "group_unavailable"
        assert ConstraintType.MAX_HOURS_PER_DAY.value == "max_hours_per_day"
        assert ConstraintType.MIN_BREAK.value == "min_break"
        assert ConstraintType.PREFERRED_SLOT.value == "preferred_slot"
        assert ConstraintType.NO_CONSECUTIVE.value == "no_consecutive"
        assert ConstraintType.SAME_DAY_REQUIRED.value == "same_day_required"

    def test_constraint_priority_enum(self):
        """Test des valeurs de l'enum ConstraintPriority"""
        assert ConstraintPriority.HARD.value == "hard"
        assert ConstraintPriority.SOFT.value == "soft"
        assert ConstraintPriority.MEDIUM.value == "medium"

    def test_set_default_week(self):
        """Test définition semaine par défaut"""
        self.manager.set_default_week(10)
        assert self.manager.default_week_id == 10

    def test_column_exists_true(self):
        """Test vérification colonne existante"""
        self.mock_cursor.fetchone.return_value = (1,)
        result = self.manager._column_exists(self.mock_cursor, 'test_table', 'test_column')
        assert result is True

    def test_column_exists_false(self):
        """Test vérification colonne inexistante"""
        self.mock_cursor.fetchone.return_value = (0,)
        result = self.manager._column_exists(self.mock_cursor, 'test_table', 'test_column')
        assert result is False

    def test_column_exists_dict_result(self):
        """Test vérification colonne avec résultat dict"""
        self.mock_cursor.fetchone.return_value = {'cnt': 1}
        result = self.manager._column_exists(self.mock_cursor, 'test_table', 'test_column')
        assert result is True

    def test_get_teacher_constraints(self):
        """Test récupération contraintes enseignant"""
        self.mock_cursor.fetchall.return_value = [
            {'id': 1, 'teacher_id': 1, 'day_of_week': 'Lundi'}
        ]
        
        constraints = self.manager.get_teacher_constraints(1)
        assert len(constraints) == 1

    def test_get_teacher_constraints_with_week(self):
        """Test récupération contraintes enseignant avec semaine"""
        self.mock_cursor.fetchall.return_value = [
            {'id': 1, 'teacher_id': 1, 'day_of_week': 'Lundi', 'week_id': 5}
        ]
        
        constraints = self.manager.get_teacher_constraints(1, week_id=5)
        assert len(constraints) == 1

    def test_get_room_constraints(self):
        """Test récupération contraintes salle"""
        self.mock_cursor.fetchall.return_value = [
            {'id': 1, 'room_id': 10, 'day_of_week': 'Mardi'}
        ]
        
        constraints = self.manager.get_room_constraints(10)
        assert len(constraints) == 1

    def test_get_group_constraints(self):
        """Test récupération contraintes groupe"""
        self.mock_cursor.fetchall.return_value = [
            {'id': 1, 'group_id': 5, 'day_of_week': 'Mercredi'}
        ]
        
        constraints = self.manager.get_group_constraints(5)
        assert len(constraints) == 1

    def test_delete_constraint(self):
        """Test suppression contrainte"""
        self.mock_cursor.rowcount = 1
        
        result = self.manager.delete_constraint('teacher', 1)
        assert result is True

    def test_delete_constraint_not_found(self):
        """Test suppression contrainte inexistante"""
        self.mock_cursor.rowcount = 0
        
        result = self.manager.delete_constraint('teacher', 999)
        assert result is False

    def test_update_constraint_priority(self):
        """Test mise à jour priorité"""
        self.mock_cursor.rowcount = 1
        
        result = self.manager.update_constraint_priority('teacher', 1, ConstraintPriority.SOFT)
        assert result is True

    def test_add_teacher_unavailability_teacher_not_found(self):
        """Test ajout contrainte enseignant non trouvé"""
        # Première fois retourne colonne existe, ensuite teacher non trouvé
        self.mock_cursor.fetchone.side_effect = [(1,), (1,), (1,), None]
        
        with pytest.raises(ValueError, match="Enseignant .* non trouvé"):
            self.manager.add_teacher_unavailability(
                teacher_id=999,
                day='Lundi',
                start_time='08:00',
                end_time='10:00'
            )

    def test_add_room_unavailability_room_not_found(self):
        """Test ajout contrainte salle non trouvée"""
        # Première fois retourne colonne existe, ensuite room non trouvé
        self.mock_cursor.fetchone.side_effect = [(1,), (1,), (1,), None]
        
        with pytest.raises(ValueError, match="Salle .* non trouvée"):
            self.manager.add_room_unavailability(
                room_id=999,
                day='Lundi',
                start_time='08:00',
                end_time='10:00'
            )

    def test_add_group_unavailability_group_not_found(self):
        """Test ajout contrainte groupe non trouvé"""
        # Première fois retourne colonne existe, ensuite group non trouvé
        self.mock_cursor.fetchone.side_effect = [(1,), (1,), (1,), None]
        
        with pytest.raises(ValueError, match="Groupe .* non trouvé"):
            self.manager.add_group_unavailability(
                group_id=999,
                day='Lundi',
                start_time='08:00',
                end_time='10:00'
            )


@pytest.mark.unit
class TestConstraintValidatorExtended:
    """Tests étendus pour le ConstraintValidator"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration avant chaque test"""
        self.patcher = patch('constraint_manager.get_db_connection')
        self.mock_get_conn = self.patcher.start()
        
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_get_conn.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (0,)
        self.mock_cursor.fetchall.return_value = []
        
        self.validator = ConstraintValidator()
        yield
        self.patcher.stop()

    def test_days_map(self):
        """Test du mapping des jours"""
        assert ConstraintValidator.DAYS_MAP['Lundi'] == 0
        assert ConstraintValidator.DAYS_MAP['Vendredi'] == 4

    def test_time_slots(self):
        """Test des créneaux horaires"""
        assert '8:00' in ConstraintValidator.TIME_SLOTS
        assert '12:00' in ConstraintValidator.TIME_SLOTS
        assert '19:30' in ConstraintValidator.TIME_SLOTS

    def test_time_to_slot_index(self):
        """Test conversion heure vers index slot"""
        assert self.validator._time_to_slot_index('8:00') == 0
        assert self.validator._time_to_slot_index('8:30') == 1
        assert self.validator._time_to_slot_index('12:00') == 8

    def test_time_to_slot_index_with_seconds(self):
        """Test conversion heure avec secondes"""
        assert self.validator._time_to_slot_index('08:00:00') == 0
        assert self.validator._time_to_slot_index('10:30:00') == 5

    def test_slot_index_to_time(self):
        """Test conversion index vers heure"""
        assert self.validator._slot_index_to_time(0) == '8:00'
        assert self.validator._slot_index_to_time(1) == '8:30'

    def test_slot_index_to_time_out_of_range(self):
        """Test conversion index hors plage"""
        result = self.validator._slot_index_to_time(30)
        assert ':' in result  # Doit retourner un format HH:MM

    def test_check_time_overlap_true(self):
        """Test chevauchement d'horaires - positif"""
        assert self.validator._check_time_overlap('8:00', '10:00', '9:00', '11:00') is True

    def test_check_time_overlap_false(self):
        """Test pas de chevauchement d'horaires"""
        assert self.validator._check_time_overlap('8:00', '10:00', '10:00', '12:00') is False

    def test_validate_teacher_availability_no_constraints(self):
        """Test validation enseignant sans contraintes"""
        available, priority, message = self.validator.validate_teacher_availability(
            999, 'Lundi', '08:00', '10:00'
        )
        assert available is True
        assert priority is None
        assert message == "OK"

    def test_validate_room_availability_no_constraints(self):
        """Test validation salle sans contraintes"""
        available, priority, message = self.validator.validate_room_availability(
            999, 'Mardi', '14:00', '16:00'
        )
        assert available is True

    def test_validate_group_availability_no_constraints(self):
        """Test validation groupe sans contraintes"""
        available, priority, message = self.validator.validate_group_availability(
            999, 'Mercredi', '10:00', '12:00'
        )
        assert available is True

    def test_get_blocked_slots_for_teacher(self):
        """Test récupération slots bloqués enseignant"""
        blocked = self.validator.get_blocked_slots_for_teacher(1)
        assert isinstance(blocked, dict)

    def test_get_blocked_slots_for_room(self):
        """Test récupération slots bloqués salle"""
        blocked = self.validator.get_blocked_slots_for_room(1)
        assert isinstance(blocked, dict)

    def test_get_blocked_slots_for_group(self):
        """Test récupération slots bloqués groupe"""
        blocked = self.validator.get_blocked_slots_for_group(1)
        assert isinstance(blocked, dict)


@pytest.mark.unit
class TestConstraintIntegrationExtended:
    """Tests étendus pour ConstraintIntegration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration avant chaque test"""
        self.patcher = patch('constraint_manager.get_db_connection')
        self.mock_get_conn = self.patcher.start()
        
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_get_conn.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (0,)
        self.mock_cursor.fetchall.return_value = []
        
        self.mock_model = MagicMock()
        self.integration = ConstraintIntegration(self.mock_model, week_id=1)
        
        yield
        self.patcher.stop()

    def test_init(self):
        """Test initialisation"""
        assert self.integration.model == self.mock_model
        assert self.integration.week_id == 1
        assert self.integration.validator is not None

    def test_is_time_in_range(self):
        """Test vérification heure dans plage"""
        result = self.integration._is_time_in_range('09:00', '08:00', '10:00')
        assert result is True
        
        result = self.integration._is_time_in_range('11:00', '08:00', '10:00')
        assert result is False

    def test_find_blocked_slots_empty(self):
        """Test recherche slots bloqués - vide"""
        slot_mapping = {0: ('Lundi', '08:00')}
        time_ranges = []
        
        result = self.integration._find_blocked_slots('Lundi', time_ranges, slot_mapping)
        # Peut retourner une liste vide ou un set vide selon l'implémentation
        assert len(result) == 0

    def test_find_blocked_slots_with_matches(self):
        """Test recherche slots bloqués avec correspondances"""
        slot_mapping = {
            0: ('Lundi', '08:00'),
            1: ('Lundi', '08:30'),
            2: ('Lundi', '09:00'),
            3: ('Mardi', '08:00')
        }
        time_ranges = [('08:00', '09:00')]
        
        result = self.integration._find_blocked_slots('Lundi', time_ranges, slot_mapping)
        assert 0 in result or 1 in result

    def test_add_teacher_unavailability_constraints_empty(self):
        """Test ajout contraintes enseignant - vide"""
        course_vars = {}
        teacher_mapping = {}
        slot_mapping = {}
        
        count = self.integration.add_teacher_unavailability_constraints(
            course_vars, teacher_mapping, slot_mapping
        )
        assert count == 0

    def test_add_room_unavailability_constraints_empty(self):
        """Test ajout contraintes salle - vide"""
        course_vars = {}
        room_mapping = {}
        slot_mapping = {}
        
        count = self.integration.add_room_unavailability_constraints(
            course_vars, room_mapping, slot_mapping
        )
        assert count == 0

    def test_add_group_unavailability_constraints_empty(self):
        """Test ajout contraintes groupe - vide"""
        course_vars = {}
        group_mapping = {}
        course_groups = {}
        slot_mapping = {}
        
        count = self.integration.add_group_unavailability_constraints(
            course_vars, group_mapping, course_groups, slot_mapping
        )
        assert count == 0

    def test_add_all_constraints(self):
        """Test ajout de toutes les contraintes"""
        stats = self.integration.add_all_constraints(
            course_vars={},
            teacher_mapping={},
            room_mapping={},
            group_mapping={},
            course_groups={},
            slot_mapping={}
        )
        
        assert 'teachers' in stats
        assert 'rooms' in stats
        assert 'groups' in stats
        assert 'total' in stats
        assert stats['total'] == stats['teachers'] + stats['rooms'] + stats['groups']


@pytest.mark.unit
class TestConstraintIntegrationMethods:
    """Tests supplémentaires pour ConstraintIntegration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Configuration avant chaque test"""
        self.patcher = patch('constraint_manager.get_db_connection')
        self.mock_get_conn = self.patcher.start()
        
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_get_conn.return_value = self.mock_conn
        self.mock_conn.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (0,)
        self.mock_cursor.fetchall.return_value = []
        
        self.mock_model = MagicMock()
        self.integration = ConstraintIntegration(self.mock_model, week_id=1)
        
        yield
        self.patcher.stop()

    def test_is_time_in_range_true(self):
        """Test heure dans la plage"""
        result = self.integration._is_time_in_range('09:00', '08:00', '10:00')
        assert result is True

    def test_is_time_in_range_false_before(self):
        """Test heure avant la plage"""
        result = self.integration._is_time_in_range('07:00', '08:00', '10:00')
        assert result is False

    def test_is_time_in_range_false_after(self):
        """Test heure après la plage"""
        result = self.integration._is_time_in_range('11:00', '08:00', '10:00')
        assert result is False

    def test_is_time_in_range_edge_start(self):
        """Test heure égale au début de la plage"""
        result = self.integration._is_time_in_range('08:00', '08:00', '10:00')
        assert result is True

    def test_is_time_in_range_edge_end(self):
        """Test heure égale à la fin de la plage (exclusive)"""
        result = self.integration._is_time_in_range('10:00', '08:00', '10:00')
        assert result is False

    def test_is_time_in_range_with_seconds(self):
        """Test avec format HH:MM:SS"""
        result = self.integration._is_time_in_range('09:30:00', '08:00:00', '10:00:00')
        assert result is True

    def test_find_blocked_slots_with_data(self):
        """Test recherche slots bloqués avec données"""
        slot_mapping = {
            0: ('Lundi', '08:00'),
            1: ('Lundi', '08:30'),
            2: ('Lundi', '09:00'),
            3: ('Lundi', '09:30'),
            4: ('Mardi', '08:00')
        }
        time_ranges = [('08:00', '10:00')]
        
        result = self.integration._find_blocked_slots('Lundi', time_ranges, slot_mapping)
        
        # Les slots 0, 1, 2, 3 devraient être bloqués (08:00 à 09:30)
        assert 0 in result
        assert 1 in result
        assert 2 in result
        assert 3 in result
        assert 4 not in result  # Mardi

    def test_find_blocked_slots_wrong_day(self):
        """Test recherche slots bloqués - mauvais jour"""
        slot_mapping = {
            0: ('Lundi', '08:00'),
            1: ('Lundi', '09:00')
        }
        time_ranges = [('08:00', '10:00')]
        
        result = self.integration._find_blocked_slots('Mardi', time_ranges, slot_mapping)
        
        assert len(result) == 0

    def test_find_blocked_slots_multiple_ranges(self):
        """Test recherche slots bloqués - plusieurs plages"""
        slot_mapping = {
            0: ('Lundi', '08:00'),
            1: ('Lundi', '09:00'),
            2: ('Lundi', '14:00'),
            3: ('Lundi', '15:00')
        }
        time_ranges = [('08:00', '10:00'), ('14:00', '16:00')]
        
        result = self.integration._find_blocked_slots('Lundi', time_ranges, slot_mapping)
        
        assert 0 in result  # 08:00
        assert 1 in result  # 09:00
        assert 2 in result  # 14:00
        assert 3 in result  # 15:00
