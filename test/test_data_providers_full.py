#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour data_provider.py et data_provider_id.py
Compatible avec pytest et SonarQube
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os
import pandas as pd

# Ajouter le chemin parent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def mock_engine():
    """Mock de l'engine SQLAlchemy"""
    return MagicMock()


@pytest.fixture
def sample_db_config():
    """Configuration de base de données de test"""
    return {
        'host': 'localhost',
        'port': 3306,
        'database': 'test_db',
        'user': 'test_user',
        'password': 'test_pass'
    }


@pytest.mark.unit
class TestDataProvider:
    """Tests pour DataProvider"""

    @patch('data_provider.create_engine')
    def test_init(self, mock_create_engine, sample_db_config):
        """Test initialisation DataProvider"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        assert provider.db_config == sample_db_config
        assert provider.engine == mock_engine
        mock_create_engine.assert_called_once()

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_time_to_slot(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test conversion temps vers slot"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # Test 8:00 -> slot 0
        assert provider._time_to_slot('08:00:00') == 0
        
        # Test 8:30 -> slot 1
        assert provider._time_to_slot('08:30:00') == 1
        
        # Test 13:30 -> slot 11
        assert provider._time_to_slot('13:30:00') == 11
        
        # Test NA
        assert provider._time_to_slot(pd.NA) == 0

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_build_course_structures_cm(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction des structures de cours pour CM"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # DataFrame de test pour un CM
        df = pd.DataFrame({
            'duration': [1.5],
            'type_id': [1],  # CM
            'promotion_name': ['BUT1'],
            'group_name': [None],
            'subgroup_name': [None],
            'teaching_title': ['Mathématiques'],
            'promo_size': [100],
            'group_size': [None],
            'subgroup_size': [None]
        }, index=[1])
        
        profs_par_slot = {1: ['Prof A']}
        profs = ['Prof A', 'Prof B']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'CM' in cours[0]['id']
        assert 'BUT1' in cours[0]['groups']

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_build_course_structures_td(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction des structures de cours pour TD"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # DataFrame de test pour un TD
        df = pd.DataFrame({
            'duration': [1.0],
            'type_id': [2],  # TD
            'promotion_name': ['BUT1'],
            'group_name': ['G1'],
            'subgroup_name': [None],
            'teaching_title': ['Algorithmique'],
            'promo_size': [100],
            'group_size': [30],
            'subgroup_size': [None]
        }, index=[2])
        
        profs_par_slot = {2: ['Prof B']}
        profs = ['Prof A', 'Prof B']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'TD' in cours[0]['id']
        assert 'G1' in cours[0]['groups']

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_build_course_structures_tp(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction des structures de cours pour TP"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # DataFrame de test pour un TP
        df = pd.DataFrame({
            'duration': [2.0],
            'type_id': [3],  # TP
            'promotion_name': ['BUT1'],
            'group_name': ['G1'],
            'subgroup_name': ['A'],
            'teaching_title': ['Python'],
            'promo_size': [100],
            'group_size': [30],
            'subgroup_size': [15]
        }, index=[3])
        
        profs_par_slot = {3: ['Prof A']}
        profs = ['Prof A', 'Prof B']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'TP' in cours[0]['id']
        assert 'G1A' in cours[0]['groups']

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_build_course_structures_sae(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction des structures de cours pour SAE"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # DataFrame de test pour une SAE
        df = pd.DataFrame({
            'duration': [3.0],
            'type_id': [4],  # SAE
            'promotion_name': ['BUT1'],
            'group_name': ['G1'],
            'subgroup_name': [None],
            'teaching_title': ['Projet SAE'],
            'promo_size': [100],
            'group_size': [30],
            'subgroup_size': [None]
        }, index=[4])
        
        profs_par_slot = {}  # Pas de prof assigné
        profs = ['Prof A', 'Prof B']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'SAE' in cours[0]['id']

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_build_course_structures_unknown_type(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test que les types inconnus sont ignorés"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider import DataProvider
        provider = DataProvider(sample_db_config)
        
        # DataFrame avec type inconnu
        df = pd.DataFrame({
            'duration': [1.0],
            'type_id': [99],  # Type inconnu
            'promotion_name': ['BUT1'],
            'group_name': ['G1'],
            'subgroup_name': [None],
            'teaching_title': ['Test'],
            'promo_size': [100],
            'group_size': [30],
            'subgroup_size': [None]
        }, index=[5])
        
        profs_par_slot = {}
        profs = ['Prof A']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 0  # Type inconnu ignoré


@pytest.mark.unit
class TestDataProviderID:
    """Tests pour DataProviderID"""

    @patch('data_provider_id.create_engine')
    def test_init(self, mock_create_engine, sample_db_config):
        """Test initialisation DataProviderID"""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        assert provider.db_config == sample_db_config
        assert provider.engine == mock_engine

    @patch('data_provider_id.create_engine')
    @patch('data_provider_id.pd.read_sql')
    def test_time_to_slot(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test conversion temps vers slot pour DataProviderID"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        # Test différentes heures
        assert provider._time_to_slot('08:00:00') == 0
        assert provider._time_to_slot('09:00:00') == 2
        assert provider._time_to_slot('12:00:00') == 8
        
        # Test NA
        assert provider._time_to_slot(pd.NA) == 0

    @patch('data_provider_id.create_engine')
    @patch('data_provider_id.pd.read_sql')
    def test_build_course_structures_cm(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction structures cours CM pour DataProviderID"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        df = pd.DataFrame({
            'duration': [1.5],
            'type_id': [1],
            'promotion_name': ['BUT2'],
            'group_name': [None],
            'subgroup_name': [None],
            'teaching_title': ['Réseaux'],
            'promo_size': [80],
            'group_size': [None],
            'subgroup_size': [None]
        }, index=[1])
        
        profs_par_slot = {1: ['Prof C']}
        profs = ['Prof C']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'CM' in cours[0]['id']
        assert 'BUT2' in cours[0]['groups']

    @patch('data_provider_id.create_engine')
    @patch('data_provider_id.pd.read_sql')
    def test_build_course_structures_but3(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction structures cours pour BUT3"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        df = pd.DataFrame({
            'duration': [1.0],
            'type_id': [1],  # CM
            'promotion_name': ['BUT3'],
            'group_name': [None],
            'subgroup_name': [None],
            'teaching_title': ['Stage'],
            'promo_size': [40],
            'group_size': [None],
            'subgroup_size': [None]
        }, index=[1])
        
        profs_par_slot = {}
        profs = ['Prof D']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        # Vérifier que les groupes G7, G8 sont associés à BUT3
        assert any('BUT3' in c['groups'] for c in cours)

    @patch('data_provider_id.create_engine')
    @patch('data_provider_id.pd.read_sql')
    def test_get_list_room(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test récupération liste des salles"""
        mock_create_engine.return_value = MagicMock()
        mock_read_sql.return_value = pd.DataFrame({'name': ['Salle A', 'Salle B', 'Amphi']})
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        rooms = provider.get_list_room()
        
        assert len(rooms) == 3
        assert 'Salle A' in rooms

    @patch('data_provider_id.create_engine')
    def test_get_end_time(self, mock_create_engine, sample_db_config):
        """Test get_end_time"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        row = {'end_time': '16:00:00'}
        assert provider.get_end_time(row) == '16:00:00'
        
        row_na = {'end_time': pd.NA}
        assert provider.get_end_time(row_na) == ""

    @patch('data_provider_id.create_engine')
    def test_get_start_time(self, mock_create_engine, sample_db_config):
        """Test get_start_time"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        row = {'start_time': '08:00:00'}
        assert provider.get_start_time(row) == '08:00:00'
        
        row_na = {'start_time': pd.NA}
        assert provider.get_start_time(row_na) == ""

    @patch('data_provider_id.create_engine')
    def test_convert_daystring_to_int(self, mock_create_engine, sample_db_config):
        """Test conversion jour string vers int"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        assert provider.convert_daystring_to_int('Lundi') == 0
        assert provider.convert_daystring_to_int('Vendredi') == 4

    @patch('data_provider_id.create_engine')
    def test_time_to_slot_id(self, mock_create_engine, sample_db_config):
        """Test conversion heure vers slot"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        assert provider._time_to_slot('08:00:00') == 0
        assert provider._time_to_slot('12:00:00') == 8
        assert provider._time_to_slot(pd.NA) == 0

    @patch('data_provider_id.create_engine')
    @patch('data_provider_id.pd.read_sql')
    def test_build_course_structures_sae_no_group(self, mock_read_sql, mock_create_engine, sample_db_config):
        """Test construction SAE sans groupe spécifique"""
        mock_create_engine.return_value = MagicMock()
        
        from data_provider_id import DataProviderID
        provider = DataProviderID(sample_db_config)
        
        # SAE avec group_name = None
        df = pd.DataFrame({
            'duration': [2.0],
            'type_id': [4],  # SAE
            'promotion_name': ['BUT1'],
            'group_name': [None],
            'subgroup_name': [None],
            'teaching_title': ['Projet SAE'],
            'promo_size': [100],
            'group_size': [None],
            'subgroup_size': [None]
        }, index=[10])
        
        profs_par_slot = {}
        profs = ['Prof E']
        
        cours, duree_cours, taille_groupes, map_groupe_cours = provider._build_course_structures(
            df, profs_par_slot, profs
        )
        
        assert len(cours) == 1
        assert 'SAE' in cours[0]['id']
