
"""
Script principal pour lancer tous les tests du projet
"""

import unittest
import sys
import os
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, os.path.join(parent_dir, 'bouton'))

test_modules = []

try:
    import test_constraint_system
    test_modules.append(('Contraintes', test_constraint_system))
except ImportError as e:
    print(f"⚠️  Impossible d'importer test_constraint_system: {e}")

try:
    import test_data_providers
    test_modules.append(('Data Providers', test_data_providers))
except ImportError as e:
    print(f"⚠️  Impossible d'importer test_data_providers: {e}")

try:
    import test_utilities
    test_modules.append(('Utilitaires', test_utilities))
except ImportError as e:
    print(f"⚠️  Impossible d'importer test_utilities: {e}")


def print_banner(text, char='=', width=80):
    """Affiche une bannière"""
    print(char * width)
    print(f"  {text}")
    print(char * width)


def print_section(text, char='-', width=80):
    """Affiche une section"""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)


def run_all_tests(verbose=2):
    """
    Lance tous les tests du projet

    Args:
        verbose: Niveau de verbosité (0=minimal, 1=normal, 2=détaillé)

    Returns:
        bool: True si tous les tests passent, False sinon
    """
    start_time = datetime.now()

    print_banner("SUITE COMPLÈTE DE TESTS - PROJET EDT", '=')
    print(f"\nDate: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Modules de test chargés: {len(test_modules)}")

    if not test_modules:
        print("\n❌ ERREUR: Aucun module de test n'a pu être chargé!")
        return False

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    module_results = {}

    for module_name, module in test_modules:
        print_section(f"Module: {module_name}")

        # Charger les tests du module
        module_suite = loader.loadTestsFromModule(module)
        suite.addTests(module_suite)

        # Lancer les tests du module
        runner = unittest.TextTestRunner(verbosity=verbose)
        result = runner.run(module_suite)

        # Stocker les résultats
        module_results[module_name] = {
            'total': result.testsRun,
            'success': result.testsRun - len(result.failures) - len(result.errors),
            'failures': len(result.failures),
            'errors': len(result.errors),
            'passed': result.wasSuccessful()
        }

    # Résumé global
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print_banner("RÉSUMÉ GLOBAL", '=')

    total_tests = sum(r['total'] for r in module_results.values())
    total_success = sum(r['success'] for r in module_results.values())
    total_failures = sum(r['failures'] for r in module_results.values())
    total_errors = sum(r['errors'] for r in module_results.values())

    print(f"\n📊 Statistiques globales:")
    print(f"   Tests exécutés: {total_tests}")
    print(f"   ✅ Succès: {total_success} ({total_success/total_tests*100:.1f}%)" if total_tests > 0 else "   ✅ Succès: 0")
    print(f"   ❌ Échecs: {total_failures}")
    print(f"   💥 Erreurs: {total_errors}")
    print(f"   ⏱️  Durée: {duration:.2f}s")

    print("\n📋 Résultats par module:")
    for module_name, results in module_results.items():
        status = "✅" if results['passed'] else "❌"
        success_rate = results['success']/results['total']*100 if results['total'] > 0 else 0
        print(f"   {status} {module_name}: {results['success']}/{results['total']} ({success_rate:.0f}%)")

    # Verdict final
    all_passed = all(r['passed'] for r in module_results.values())

    print()
    if all_passed:
        print("="*80)
        print("🎉 FÉLICITATIONS! TOUS LES TESTS SONT PASSÉS! 🎉")
        print("="*80)
        return True
    else:
        print("="*80)
        print("⚠️  ATTENTION: CERTAINS TESTS ONT ÉCHOUÉ")
        print("="*80)
        print("\n💡 Conseils:")
        print("   - Vérifiez les messages d'erreur ci-dessus")
        print("   - Lancez les tests individuels pour plus de détails")
        print("   - Exemple: python test/test_constraint_system.py")
        return False


def run_specific_module(module_name, verbose=2):
    """
    Lance les tests d'un module spécifique

    Args:
        module_name: Nom du module (ex: 'constraint', 'data', 'utilities')
        verbose: Niveau de verbosité
    """
    module_map = {
        'constraint': 'test_constraint_system',
        'data': 'test_data_providers',
        'utilities': 'test_utilities'
    }

    if module_name not in module_map:
        print(f"❌ Module inconnu: {module_name}")
        print(f"   Modules disponibles: {', '.join(module_map.keys())}")
        return False

    try:
        module = __import__(module_map[module_name])
        print_banner(f"Tests du module: {module_name.upper()}")

        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        runner = unittest.TextTestRunner(verbosity=verbose)
        result = runner.run(suite)

        return result.wasSuccessful()
    except ImportError as e:
        print(f"❌ Impossible de charger le module: {e}")
        return False


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Lance les tests du projet EDT',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python run_all_tests.py              # Lance tous les tests
  python run_all_tests.py -m constraint # Lance uniquement les tests de contraintes
  python run_all_tests.py -v 1         # Mode moins verbeux
  python run_all_tests.py --quick      # Mode rapide (verbosité minimale)
        """
    )

    parser.add_argument(
        '-m', '--module',
        choices=['constraint', 'data', 'utilities', 'all'],
        default='all',
        help='Module à tester (défaut: all)'
    )

    parser.add_argument(
        '-v', '--verbose',
        type=int,
        choices=[0, 1, 2],
        default=2,
        help='Niveau de verbosité (0=minimal, 1=normal, 2=détaillé)'
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Mode rapide (équivalent à -v 0)'
    )

    args = parser.parse_args()

    # Ajuster la verbosité si mode quick
    verbose = 0 if args.quick else args.verbose

    # Lancer les tests
    if args.module == 'all':
        success = run_all_tests(verbose)
    else:
        success = run_specific_module(args.module, verbose)

    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()