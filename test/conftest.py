#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration pytest pour le projet EDT
Fixtures et configuration partagées pour tous les tests
"""

import sys
import os
from unittest.mock import MagicMock
import pytest

# Ajouter les répertoires au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
bouton_dir = os.path.join(parent_dir, 'bouton')

sys.path.insert(0, parent_dir)
sys.path.insert(0, bouton_dir)

# Mock mysql.connector avant d'importer les modules qui en dépendent
mock_mysql = MagicMock()
mock_mysql.connect = MagicMock()
mock_mysql.Error = Exception
sys.modules['mysql'] = MagicMock()
sys.modules['mysql.connector'] = mock_mysql
sys.modules['mysql.connector.errors'] = MagicMock()

# Mock SQLAlchemy
sys.modules['sqlalchemy'] = MagicMock()


@pytest.fixture
def db_config():
    """Configuration de base de données de test"""
    return {
        'host': '127.0.0.1',
        'port': 33066,
        'database': 'edt_app',
        'user': 'edt_user',
        'password': 'userpassword'
    }


@pytest.fixture
def mock_db_connection():
    """Mock de connexion à la base de données"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = {'cnt': 0}
    mock_cursor.fetchall.return_value = []
    mock_cursor.lastrowid = 42
    mock_cursor.rowcount = 1
    return mock_conn, mock_cursor


@pytest.fixture
def valid_schedule_data():
    """Données valides pour un emploi du temps"""
    return {
        'jours': 5,
        'creneaux_par_jour': 20,
        'slots': [(d, s) for d in range(5) for s in range(20)],
        'nb_slots': 100,
        'fenetre_midi': [8, 9, 10],
        'salles': {'Salle A': 30, 'Salle B': 50, 'Amphi': 100},
        'cours': [
            {'id': 'CM_Math_BUT1', 'groups': ['BUT1']},
            {'id': 'TD_Info_G1', 'groups': ['G1']}
        ],
        'duree_cours': {
            'CM_Math_BUT1': 3,
            'TD_Info_G1': 2
        },
        'taille_groupes': {
            'BUT1': 60,
            'G1': 30
        },
        'map_groupe_cours': {
            'BUT1': ['CM_Math_BUT1'],
            'G1': ['TD_Info_G1']
        }
    }


@pytest.fixture
def teacher_mapping():
    """Mapping enseignants pour les tests"""
    return {1: 0, 2: 1}


@pytest.fixture
def room_mapping():
    """Mapping salles pour les tests"""
    return {10: 0, 20: 1}


@pytest.fixture
def group_mapping():
    """Mapping groupes pour les tests"""
    return {5: 0, 6: 1}


@pytest.fixture
def slot_mapping():
    """Mapping créneaux pour les tests"""
    return {
        0: ('Lundi', '08:00'),
        1: ('Lundi', '10:00'),
        2: ('Mardi', '14:00')
    }


@pytest.fixture
def course_groups():
    """Association cours-groupes pour les tests"""
    return {
        1: [5],
        2: [6]
    }


def pytest_configure(config):
    """Configuration au démarrage de pytest"""
    config.addinivalue_line("markers", "slow: Tests lents")
    config.addinivalue_line("markers", "integration: Tests d'intégration")
    config.addinivalue_line("markers", "unit: Tests unitaires")


def pytest_collection_modifyitems(config, items):
    """Modifie les items de test collectés"""
    # Ajouter automatiquement le marker 'unit' aux tests qui n'ont pas de marker
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)
