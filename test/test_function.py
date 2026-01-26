#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour function.py
Compatible avec pytest et SonarQube
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import pandas as pd

# Mock db_config avant import
sys.modules['db_config'] = MagicMock()
sys.modules['db_config'].get_engine = MagicMock(return_value=MagicMock())

# Import des fonctions à tester
from function import (
    get_end_time,
    get_start_time,
    convert_daystring_to_int,
    convert_days_int_to_string,
    _time_to_slot,
    get_availabilityProf_From_Unavailable,
    get_availabilityRoom_From_Unavailable,
    get_availabilityGroup_From_Unavailable,
    recuperation_indisponibilites,
    recuperation_disponibilites_profs,
    recuperation_indisponibilites_rooms,
    recuperation_disponibilites_rooms,
    recuperation_indisponibilites_group,
    recuperation_disponibilites_group,
    get_availabilitySlot_From_Unavailable,
    recuperation_indisponibilites_slot,
    recup_cours,
    recup_id_slot_from_str_to_int
)


@pytest.mark.unit
class TestFunctionHelpers:
    """Tests pour les fonctions utilitaires de base"""

    def test_get_end_time_valid(self):
        """Test get_end_time avec une valeur valide"""
        row = {'end_time': '10:30:00'}
        assert get_end_time(row) == '10:30:00'

    def test_get_end_time_na(self):
        """Test get_end_time avec NA"""
        row = {'end_time': pd.NA}
        assert get_end_time(row) == ""

    def test_get_end_time_none(self):
        """Test get_end_time avec None"""
        row = {'end_time': None}
        assert get_end_time(row) == ""

    def test_get_start_time_valid(self):
        """Test get_start_time avec une valeur valide"""
        row = {'start_time': '08:00:00'}
        assert get_start_time(row) == '08:00:00'

    def test_get_start_time_na(self):
        """Test get_start_time avec NA"""
        row = {'start_time': pd.NA}
        assert get_start_time(row) == ""

    def test_get_start_time_none(self):
        """Test get_start_time avec None"""
        row = {'start_time': None}
        assert get_start_time(row) == ""

    def test_convert_daystring_to_int(self):
        """Test conversion jour string -> int"""
        assert convert_daystring_to_int('Lundi') == 0
        assert convert_daystring_to_int('Mardi') == 1
        assert convert_daystring_to_int('Mercredi') == 2
        assert convert_daystring_to_int('Jeudi') == 3
        assert convert_daystring_to_int('Vendredi') == 4

    def test_convert_days_int_to_string(self):
        """Test conversion jour int -> string"""
        assert convert_days_int_to_string(0) == 'Lundi'
        assert convert_days_int_to_string(1) == 'Mardi'
        assert convert_days_int_to_string(2) == 'Mercredi'
        assert convert_days_int_to_string(3) == 'Jeudi'
        assert convert_days_int_to_string(4) == 'Vendredi'

    def test_time_to_slot(self):
        """Test conversion heure -> slot"""
        assert _time_to_slot('08:00:00') == 0
        assert _time_to_slot('08:30:00') == 1
        assert _time_to_slot('09:00:00') == 2
        assert _time_to_slot('13:30:00') == 11
        assert _time_to_slot('18:00:00') == 20

    def test_time_to_slot_na(self):
        """Test time_to_slot avec NA"""
        assert _time_to_slot(pd.NA) == 0

    def test_recup_cours(self):
        """Test extraction type et nom de cours"""
        result = recup_cours("CM_Math_BUT1_s1")
        assert result == ("CM", "Math")

    def test_recup_cours_complex(self):
        """Test extraction avec nom complexe"""
        result = recup_cours("TD_R1.01 Initiation_BUT1_s7")
        assert result[0] == "TD"
        assert result[1] == "R1.01 Initiation"

    def test_recup_id_slot_from_str_to_int(self):
        """Test extraction ID slot"""
        result = recup_id_slot_from_str_to_int("CM_Math_BUT1_s7000000")
        assert result == 7000000

    def test_recup_id_slot_from_str_to_int_simple(self):
        """Test extraction ID slot simple"""
        result = recup_id_slot_from_str_to_int("TD_Info_G1_s42")
        assert result == 42


@pytest.mark.unit
class TestAvailabilityProf:
    """Tests pour les fonctions de disponibilité des professeurs"""

    def test_get_availabilityProf_empty_dataframe(self):
        """Test avec DataFrame vide"""
        df = pd.DataFrame(columns=['teacher_id', 'day_of_week', 'start_time', 'end_time'])
        result = get_availabilityProf_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_get_availabilityProf_with_data(self):
        """Test avec données d'indisponibilité"""
        df = pd.DataFrame({
            'teacher_id': [1, 1],
            'day_of_week': ['Lundi', 'Mardi'],
            'start_time': ['08:00:00', '14:00:00'],
            'end_time': ['10:00:00', '16:00:00']
        })
        result = get_availabilityProf_From_Unavailable(df, 20)
        assert isinstance(result, dict)
        assert 1 in result

    def test_recuperation_indisponibilites(self):
        """Test récupération des indisponibilités"""
        df = pd.DataFrame({
            'teacher_id': [1],
            'day_of_week': ['Lundi'],
            'start_time': ['08:00:00'],
            'end_time': ['10:00:00']
        })
        result = recuperation_indisponibilites(df, {})
        assert 1 in result
        assert 'Lundi' in result[1]

    def test_recuperation_indisponibilites_empty_time(self):
        """Test avec heures vides"""
        df = pd.DataFrame({
            'teacher_id': [1],
            'day_of_week': ['Lundi'],
            'start_time': [pd.NA],
            'end_time': [pd.NA]
        })
        result = recuperation_indisponibilites(df, {})
        assert 1 in result
        assert result[1]['Lundi'][0] == ('', '')

    def test_recuperation_disponibilites_profs(self):
        """Test calcul des disponibilités"""
        indispos = {1: {'Lundi': [(0, 4)]}}
        result = recuperation_disponibilites_profs(20, {}, indispos)
        assert isinstance(result, dict)


@pytest.mark.unit
class TestAvailabilityRoom:
    """Tests pour les fonctions de disponibilité des salles"""

    def test_get_availabilityRoom_empty_dataframe(self):
        """Test avec DataFrame vide"""
        df = pd.DataFrame(columns=['room_id', 'day_of_week', 'start_time', 'end_time'])
        result = get_availabilityRoom_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_get_availabilityRoom_with_data(self):
        """Test avec données d'indisponibilité"""
        df = pd.DataFrame({
            'room_id': [10],
            'day_of_week': ['Mercredi'],
            'start_time': ['10:00:00'],
            'end_time': ['12:00:00']
        })
        result = get_availabilityRoom_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_recuperation_indisponibilites_rooms(self):
        """Test récupération indisponibilités salles"""
        df = pd.DataFrame({
            'room_id': [10],
            'day_of_week': ['Mercredi'],
            'start_time': ['10:00:00'],
            'end_time': ['12:00:00']
        })
        result = recuperation_indisponibilites_rooms(df, {})
        assert 10 in result

    def test_recuperation_disponibilites_rooms(self):
        """Test calcul disponibilités salles"""
        indispos = {10: {'Lundi': [(0, 4)]}}
        result = recuperation_disponibilites_rooms(20, {}, indispos)
        assert isinstance(result, dict)


@pytest.mark.unit
class TestAvailabilityGroup:
    """Tests pour les fonctions de disponibilité des groupes"""

    def test_get_availabilityGroup_empty_dataframe(self):
        """Test avec DataFrame vide"""
        df = pd.DataFrame(columns=['group_id', 'day_of_week', 'start_time', 'end_time'])
        result = get_availabilityGroup_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_get_availabilityGroup_with_data(self):
        """Test avec données d'indisponibilité"""
        df = pd.DataFrame({
            'group_id': [5],
            'day_of_week': ['Jeudi'],
            'start_time': ['12:00:00'],
            'end_time': ['14:00:00']
        })
        result = get_availabilityGroup_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_recuperation_indisponibilites_group(self):
        """Test récupération indisponibilités groupes"""
        df = pd.DataFrame({
            'group_id': [5],
            'day_of_week': ['Jeudi'],
            'start_time': ['12:00:00'],
            'end_time': ['14:00:00']
        })
        result = recuperation_indisponibilites_group(df, {})
        assert 5 in result

    def test_recuperation_disponibilites_group(self):
        """Test calcul disponibilités groupes"""
        indispos = {5: {'Lundi': [(8, 12)]}}
        result = recuperation_disponibilites_group(20, {}, indispos)
        assert isinstance(result, dict)


@pytest.mark.unit
class TestAvailabilitySlot:
    """Tests pour les fonctions de disponibilité des slots"""

    def test_get_availabilitySlot_empty_dataframe(self):
        """Test avec DataFrame vide"""
        df = pd.DataFrame(columns=['slot_id', 'day_of_week', 'start_time', 'end_time'])
        result = get_availabilitySlot_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_get_availabilitySlot_with_data(self):
        """Test avec données"""
        df = pd.DataFrame({
            'slot_id': [100],
            'day_of_week': ['Vendredi'],
            'start_time': ['09:00:00'],
            'end_time': ['11:00:00']
        })
        result = get_availabilitySlot_From_Unavailable(df, 20)
        assert isinstance(result, dict)

    def test_recuperation_indisponibilites_slot(self):
        """Test récupération indisponibilités slots"""
        df = pd.DataFrame({
            'slot_id': [100],
            'day_of_week': ['Vendredi'],
            'start_time': ['09:00:00'],
            'end_time': ['11:00:00']
        })
        result = recuperation_indisponibilites_slot(df, {})
        assert 100 in result


@pytest.mark.unit
class TestRecuperationDisponibilitesSlot:
    """Tests pour recuperation_disponibilites_slot"""

    def test_recuperation_disponibilites_slot_empty(self):
        """Test avec indisponibilités vides"""
        from function import recuperation_disponibilites_slot
        
        indispos = {}
        disponibilites = {}
        result = recuperation_disponibilites_slot(20, disponibilites, indispos)
        assert isinstance(result, dict)

    def test_recuperation_disponibilites_slot_with_data(self):
        """Test avec données d'indisponibilités"""
        from function import recuperation_disponibilites_slot
        
        indispos = {100: {'Lundi': [(4, 10)]}}
        disponibilites = {}
        result = recuperation_disponibilites_slot(20, disponibilites, indispos)
        assert isinstance(result, dict)

    def test_recuperation_disponibilites_slot_multiple_days(self):
        """Test avec plusieurs jours"""
        from function import recuperation_disponibilites_slot
        
        indispos = {
            100: {
                'Lundi': [(0, 8)],
                'Mardi': [(10, 20)]
            }
        }
        disponibilites = {}
        result = recuperation_disponibilites_slot(20, disponibilites, indispos)
        assert isinstance(result, dict)


@pytest.mark.unit
class TestEdgeCases:
    """Tests pour les cas limites"""

    def test_time_to_slot_early_morning(self):
        """Test conversion très tôt le matin"""
        result = _time_to_slot('07:00:00')
        assert result == -2  # Avant 8h

    def test_time_to_slot_late_evening(self):
        """Test conversion tard le soir"""
        result = _time_to_slot('22:00:00')
        assert result == 28  # Après les heures normales

    def test_recup_cours_short_id(self):
        """Test extraction cours avec ID court"""
        result = recup_cours("CM_Math")
        assert result == ("CM", "Math")

    def test_get_end_time_timedelta_format(self):
        """Test get_end_time avec format timedelta"""
        row = {'end_time': '2025-01-01 16:30:00'}
        result = get_end_time(row)
        assert '16:30:00' in result

    def test_get_start_time_timedelta_format(self):
        """Test get_start_time avec format timedelta"""
        row = {'start_time': '2025-01-01 08:00:00'}
        result = get_start_time(row)
        assert '08:00:00' in result
