#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests pour les DataProviders (data_provider.py et data_provider_id.py)
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

sys.modules['sqlalchemy'] = MagicMock()

try:
    from data_provider import DataProvider
    from data_provider_id import DataProviderID
    print("✅ DataProviders importés avec succès")
except ImportError as e:
    print(f"❌ Erreur d'import: {e}")
    sys.exit(1)


class TestDataProvider(unittest.TestCase):
    """Tests pour DataProvider"""

    def setUp(self):
        """Initialisation avant chaque test"""
        self.db_config = {
            'host': '127.0.0.1',
            'port': 33066,
            'database': 'edt_app',
            'user': 'edt_user',
            'password': 'userpassword'
        }

        # Mock create_engine
        with patch('data_provider.create_engine') as mock_engine:
            self.mock_engine = MagicMock()
            mock_engine.return_value = self.mock_engine
            self.provider = DataProvider(self.db_config)

    def test_init(self):
        """Test initialisation du DataProvider"""
        self.assertEqual(self.provider.db_config, self.db_config)
        self.assertIsNotNone(self.provider.engine)

    def test_time_to_slot(self):
        """Test conversion heure -> slot"""
        # 8h00 = slot 0
        self.assertEqual(self.provider._time_to_slot('08:00:00'), 0)

        # 8h30 = slot 1
        self.assertEqual(self.provider._time_to_slot('08:30:00'), 1)

        # 13h30 = slot 11
        self.assertEqual(self.provider._time_to_slot('13:30:00'), 11)

        # Test avec NaN
        self.assertEqual(self.provider._time_to_slot(pd.NA), 0)

    @patch('data_provider.pd.read_sql')
    def test_load_and_prepare_data(self, mock_read_sql):
        """Test chargement des données"""
        # Mock des DataFrames
        mock_read_sql.side_effect = [
            # df_salles
            pd.DataFrame({
                'name': ['Salle A', 'Salle B'],
                'seat_capacity': [30, 50]
            }),
            # df_profs_with_id
            pd.DataFrame({
                'teacher_id': [1, 2],
                'prof_name': ['Prof A', 'Prof B']
            }),
            # df_planning
            pd.DataFrame({
                'id': [1],
                'duration': [1.5],
                'teaching_title': ['Math'],
                'promotion_name': ['BUT1'],
                'group_name': ['G1'],
                'subgroup_name': ['A'],
                'promo_size': [60],
                'group_size': [30],
                'subgroup_size': [15],
                'type_id': [2],
                'promotion_id': [1]
            }),
            # df_prof_slot
            pd.DataFrame({
                'slot_id': [1],
                'prof_name': ['Prof A']
            }),
            # df_dispos
            pd.DataFrame({
                'teacher_id': [1],
                'day_id': [0],
                'date_from': ['08:00:00'],
                'date_to': ['10:00:00']
            })
        ]

        data = self.provider.load_and_prepare_data()

        # Vérifications
        self.assertIn('jours', data)
        self.assertIn('cours', data)
        self.assertIn('salles', data)
        self.assertIn('profs', data)
        self.assertEqual(data['jours'], 5)

    def test_build_course_structures_CM(self):
        """Test construction des cours - CM"""
        df_planning = pd.DataFrame({
            'duration': [1.5],
            'teaching_title': ['Math'],
            'promotion_name': ['BUT1'],
            'group_name': [None],
            'subgroup_name': [None],
            'promo_size': [60],
            'group_size': [None],
            'subgroup_size': [None],
            'type_id': [1],
            'promotion_id': [1]
        }, index=[1])

        profs_par_slot = {1: ['Prof A']}
        profs = ['Prof A', 'Prof B']

        cours, duree, taille, map_groupe = self.provider._build_course_structures(
            df_planning, profs_par_slot, profs
        )

        # Vérifications
        self.assertEqual(len(cours), 1)
        self.assertIn('BUT1', cours[0]['groups'])
        self.assertEqual(duree[cours[0]['id']], 3)  # 1.5h * 2 slots

    def test_build_course_structures_TD(self):
        """Test construction des cours - TD"""
        df_planning = pd.DataFrame({
            'duration': [1.0],
            'teaching_title': ['Info'],
            'promotion_name': ['BUT1'],
            'group_name': ['G1'],
            'subgroup_name': [None],
            'promo_size': [60],
            'group_size': [30],
            'subgroup_size': [None],
            'type_id': [2],
            'promotion_id': [1]
        }, index=[2])

        profs_par_slot = {2: ['Prof B']}
        profs = ['Prof A', 'Prof B']

        cours, duree, taille, map_groupe = self.provider._build_course_structures(
            df_planning, profs_par_slot, profs
        )

        # Vérifications
        self.assertEqual(len(cours), 1)
        self.assertEqual(cours[0]['groups'], ['G1'])
        self.assertEqual(taille['G1'], 30)


class TestDataProviderID(unittest.TestCase):
    """Tests pour DataProviderID"""

    def setUp(self):
        """Initialisation avant chaque test"""
        self.db_config = {
            'host': '127.0.0.1',
            'port': 33066,
            'database': 'edt_app',
            'user': 'edt_user',
            'password': 'userpassword'
        }

        with patch('data_provider_id.create_engine') as mock_engine:
            self.mock_engine = MagicMock()
            mock_engine.return_value = self.mock_engine
            self.provider = DataProviderID(self.db_config)

    def test_init(self):
        """Test initialisation du DataProviderID"""
        self.assertEqual(self.provider.db_config, self.db_config)
        self.assertIsNotNone(self.provider.engine)

    def test_convert_daystring_to_int(self):
        """Test conversion jour string -> int"""
        self.assertEqual(self.provider.convert_daystring_to_int('Lundi'), 0)
        self.assertEqual(self.provider.convert_daystring_to_int('Mardi'), 1)
        self.assertEqual(self.provider.convert_daystring_to_int('Vendredi'), 4)

    def test_get_start_time(self):
        """Test récupération heure de début"""
        row = {'start_time': '08:00:00'}
        self.assertEqual(self.provider.get_start_time(row), '08:00:00')

        row_na = {'start_time': pd.NA}
        self.assertEqual(self.provider.get_start_time(row_na), '')

    def test_get_end_time(self):
        """Test récupération heure de fin"""
        row = {'end_time': '10:00:00'}
        self.assertEqual(self.provider.get_end_time(row), '10:00:00')

        row_na = {'end_time': pd.NA}
        self.assertEqual(self.provider.get_end_time(row_na), '')

    @patch('data_provider_id.pd.read_sql')
    def test_get_list_room(self, mock_read_sql):
        """Test récupération liste des salles"""
        mock_read_sql.return_value = pd.DataFrame({
            'name': ['Salle A', 'Salle B', 'Salle C']
        })

        rooms = self.provider.get_list_room()

        self.assertEqual(len(rooms), 3)
        self.assertIn('Salle A', rooms)

    def test_time_to_slot(self):
        """Test conversion heure -> slot"""
        # 8h00 = slot 0
        self.assertEqual(self.provider._time_to_slot('08:00:00'), 0)

        # 9h30 = slot 3
        self.assertEqual(self.provider._time_to_slot('09:30:00'), 3)

    @patch('data_provider_id.convert_days_int_to_string')
    def test_convert_courses_dict_to_list_insert(self, mock_convert):
        """Test conversion des cours pour insertion"""
        mock_convert.return_value = 'Lundi'

        courses = [{
            'name': 'CM_Math_BUT1_s1',
            'day': 0,
            'start_hour': '08:00',
            'room': 'Salle A'
        }]

        with patch.object(self.provider, 'insert_data_with_pandas'):
            result = self.provider.convert_courses_dict_to_list_insert(courses)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], 'Lundi')


class TestDataProviderIntegration(unittest.TestCase):
    """Tests d'intégration des DataProviders"""

    @patch('data_provider.create_engine')
    @patch('data_provider.pd.read_sql')
    def test_full_data_pipeline(self, mock_read_sql, mock_engine):
        """Test du pipeline complet de chargement"""
        # Setup
        mock_engine.return_value = MagicMock()

        # Mock toutes les requêtes SQL
        mock_read_sql.side_effect = [
            pd.DataFrame({'name': ['S1'], 'seat_capacity': [30]}),
            pd.DataFrame({'teacher_id': [1], 'prof_name': ['Prof A']}),
            pd.DataFrame({
                'id': [1], 'duration': [1.0], 'teaching_title': ['Math'],
                'promotion_name': ['BUT1'], 'group_name': ['G1'], 'subgroup_name': [None],
                'promo_size': [60], 'group_size': [30], 'subgroup_size': [None],
                'type_id': [2], 'promotion_id': [1]
            }),
            pd.DataFrame({'slot_id': [1], 'prof_name': ['Prof A']}),
            pd.DataFrame(columns=['teacher_id', 'day_id', 'date_from', 'date_to'])
        ]

        db_config = {
            'host': '127.0.0.1', 'port': 33066, 'database': 'edt_app',
            'user': 'edt_user', 'password': 'userpassword'
        }

        provider = DataProvider(db_config)
        data = provider.load_and_prepare_data()

        # Assertions
        self.assertIsInstance(data, dict)
        self.assertIn('cours', data)
        self.assertIn('salles', data)
        self.assertGreater(len(data['cours']), 0)


def run_tests():
    """Execute tous les tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ajouter toutes les classes de test
    suite.addTests(loader.loadTestsFromTestCase(TestDataProvider))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProviderID))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProviderIntegration))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("="*70)
    print("  SUITE DE TESTS - DATA PROVIDERS")
    print("="*70)
    print()

    result = run_tests()

    print()
    print("="*70)
    print("  RÉSUMÉ DES TESTS")
    print("="*70)
    print(f"Tests exécutés: {result.testsRun}")
    print(f"Succès: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Échecs: {len(result.failures)}")
    print(f"Erreurs: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✅ TOUS LES TESTS SONT PASSÉS!")
        sys.exit(0)
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        sys.exit(1)