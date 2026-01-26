#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour exécuter les tests avec pytest et générer les rapports pour SonarQube
"""

import subprocess
import sys
import os
from pathlib import Path

# Répertoires du projet
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DIR = PROJECT_ROOT / 'test'


def run_pytest_with_coverage():
    """
    Exécute pytest avec coverage et génère les rapports pour SonarQube
    
    Génère:
    - coverage.xml: Rapport de couverture au format Cobertura pour SonarQube
    - pytest-report.xml: Rapport de tests au format JUnit pour SonarQube
    """
    print("=" * 80)
    print("  EXÉCUTION DES TESTS AVEC PYTEST + COVERAGE")
    print("=" * 80)
    print()

    # Commande pytest avec tous les rapports nécessaires pour SonarQube
    cmd = [
        sys.executable, '-m', 'pytest',
        str(TEST_DIR),
        '-v',
        '--tb=short',
        # Rapport JUnit pour SonarQube
        f'--junitxml={PROJECT_ROOT / "pytest-report.xml"}',
        # Coverage avec pytest-cov
        f'--cov={PROJECT_ROOT}',
        '--cov-report=term-missing',
        # Rapport XML Cobertura pour SonarQube
        f'--cov-report=xml:{PROJECT_ROOT / "coverage.xml"}',
        # Rapport HTML pour consultation locale
        f'--cov-report=html:{PROJECT_ROOT / "htmlcov"}',
        # Exclure certains fichiers du coverage
        '--cov-config=.coveragerc',
        # Ignorer les warnings
        '-W', 'ignore::DeprecationWarning',
    ]

    print(f"📂 Répertoire de test: {TEST_DIR}")
    print(f"📊 Rapport coverage: {PROJECT_ROOT / 'coverage.xml'}")
    print(f"📋 Rapport tests: {PROJECT_ROOT / 'pytest-report.xml'}")
    print()

    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT)
        
        print()
        print("=" * 80)
        
        if result.returncode == 0:
            print("✅ TOUS LES TESTS SONT PASSÉS!")
        else:
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        
        print("=" * 80)
        print()
        print("📁 Fichiers générés pour SonarQube:")
        print(f"   • coverage.xml (couverture de code)")
        print(f"   • pytest-report.xml (résultats des tests)")
        print(f"   • htmlcov/index.html (rapport HTML)")
        print()
        
        return result.returncode == 0
        
    except FileNotFoundError:
        print("❌ pytest n'est pas installé. Installez-le avec:")
        print("   pip install pytest pytest-cov")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        return False


def run_quick_tests():
    """Exécute les tests rapidement sans coverage"""
    cmd = [
        sys.executable, '-m', 'pytest',
        str(TEST_DIR),
        '-v',
        '--tb=short',
        '-x',  # Arrêter au premier échec
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def run_specific_test(test_name: str):
    """Exécute un test spécifique"""
    cmd = [
        sys.executable, '-m', 'pytest',
        str(TEST_DIR),
        '-v',
        '-k', test_name,
        '--tb=long',
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode == 0


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Exécute les tests avec pytest et génère les rapports pour SonarQube',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python run_pytest.py              # Tests complets avec coverage
  python run_pytest.py --quick      # Tests rapides sans coverage
  python run_pytest.py -k "test_connection"  # Test spécifique
        """
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Exécution rapide sans coverage'
    )

    parser.add_argument(
        '-k', '--keyword',
        type=str,
        help='Exécuter uniquement les tests correspondant au mot-clé'
    )

    args = parser.parse_args()

    if args.keyword:
        success = run_specific_test(args.keyword)
    elif args.quick:
        success = run_quick_tests()
    else:
        success = run_pytest_with_coverage()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
