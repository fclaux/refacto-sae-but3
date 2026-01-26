#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests complets pour local_generator.py
Compatible avec pytest et SonarQube
"""

import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock des dépendances externes avant import
sys.modules['db_config'] = MagicMock()
sys.modules['db_config'].engine = MagicMock()
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.simpledialog'] = MagicMock()
sys.modules['Front'] = MagicMock()
sys.modules['Front.schedule_generator'] = MagicMock()

# Import des constantes
from local_generator import JOURS, TYPES_COURS


@pytest.mark.unit
class TestLocalGeneratorConstants:
    """Tests pour les constantes de local_generator"""

    def test_jours(self):
        """Test liste des jours"""
        assert len(JOURS) == 7
        assert JOURS[0] == "Lundi"
        assert JOURS[4] == "Vendredi"
        assert JOURS[6] == "Dimanche"

    def test_types_cours(self):
        """Test dictionnaire des types de cours"""
        assert TYPES_COURS[1] == "CM"
        assert TYPES_COURS[2] == "TD"
        assert TYPES_COURS[3] == "TP"
        assert TYPES_COURS[4] == "Examen"
        assert TYPES_COURS[5] == "Autre"


@pytest.mark.unit
class TestEDTViewerApp:
    """Tests pour la classe EDTViewerApp"""

    @pytest.fixture
    def mock_root(self):
        """Fixture pour créer un root Tk mocké"""
        mock = MagicMock()
        mock.title = MagicMock()
        mock.geometry = MagicMock()
        return mock

    def test_app_creation(self, mock_root):
        """Test création de l'application"""
        with patch('local_generator.pd.read_sql') as mock_read:
            mock_read.return_value = MagicMock()
            mock_read.return_value.groupby.return_value.agg.return_value.reset_index.return_value = MagicMock()
            
            from local_generator import EDTViewerApp
            # Le test vérifie que l'import fonctionne
            assert EDTViewerApp is not None

    def test_jours_list(self):
        """Test que JOURS contient les bons jours"""
        assert "Lundi" in JOURS
        assert "Mardi" in JOURS
        assert "Mercredi" in JOURS
        assert "Jeudi" in JOURS
        assert "Vendredi" in JOURS
        assert "Samedi" in JOURS
        assert "Dimanche" in JOURS

    def test_types_cours_mapping(self):
        """Test mapping des types de cours"""
        assert 1 in TYPES_COURS
        assert 2 in TYPES_COURS
        assert 3 in TYPES_COURS
        assert len(TYPES_COURS) == 5
