#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de coverage pour le projet EDT
Analyse la couverture de tests pour tous les modules du projet
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple

# Ajouter le répertoire parent au path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class CoverageAnalyzer:
    """Analyseur de couverture de tests"""

    # Structure du projet basée sur votre tree
    PROJECT_STRUCTURE = {
        'root': {
            'data_provider.py': 'DataProvider principal',
            'data_provider_id.py': 'DataProvider avec IDs',
            'diagnose.py': 'Diagnostic de faisabilité',
            'function.py': 'Fonctions utilitaires',
            'local_generator.py': 'Générateur local',
            'solution_visualizer.py': 'Visualiseur de solutions',
            'test.py': 'Tests manuels',
            'test_bdd.py': 'Tests BDD',
            'time_table_model.py': 'Modèle OR-Tools',
        },
        'bouton': {
            'add_time_constraints.py': 'Ajout contraintes temporelles',
            'constraint_api.py': 'API des contraintes',
            'constraint_integration.py': 'Intégration OR-Tools',
            'constraint_manager.py': 'Gestionnaire de contraintes',
            'constraint_validator.py': 'Validateur de contraintes',
        },
        'Front': {
            'schedule_generator.py': 'Générateur UI',
        }
    }

    def __init__(self):
        self.coverage_data = {}
        self.test_dir = Path(current_dir)
        self.project_root = Path(parent_dir)

    def check_coverage_installed(self) -> bool:
        """Vérifie si coverage.py est installé"""
        try:
            import coverage
            return True
        except ImportError:
            return False

    def install_coverage(self):
        """Installe coverage.py"""
        print("📦 Installation de coverage.py...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'coverage'])
            print("✅ coverage.py installé avec succès")
            return True
        except subprocess.CalledProcessError:
            print("❌ Échec de l'installation de coverage.py")
            return False

    def run_coverage(self, test_file: str = None) -> bool:
        """Lance les tests avec coverage"""
        if not self.check_coverage_installed():
            if not self.install_coverage():
                return False

        print("\n🔍 Lancement des tests avec coverage...\n")

        # Commande coverage
        if test_file:
            cmd = [
                sys.executable, '-m', 'coverage', 'run',
                '--source', str(self.project_root),
                test_file
            ]
        else:
            cmd = [
                sys.executable, '-m', 'coverage', 'run',
                '--source', str(self.project_root),
                'run_all_tests.py'
            ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("⚠️  Certains tests ont échoué, mais le coverage a été collecté")

            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution: {e}")
            return False

    def generate_report(self, output_format: str = 'term') -> str:
        """Génère un rapport de coverage"""
        formats = {
            'term': [],  # Terminal (par défaut)
            'html': ['--format', 'html'],
            'xml': ['--format', 'xml'],
            'json': ['--format', 'json']
        }

        cmd = [sys.executable, '-m', 'coverage', 'report'] + formats.get(output_format, [])

        try:
            result = subprocess.run(
                cmd,
                cwd=self.test_dir,
                capture_output=True,
                text=True
            )
            return result.stdout
        except Exception as e:
            return f"Erreur: {e}"

    def generate_html_report(self) -> bool:
        """Génère un rapport HTML détaillé"""
        print("\n📊 Génération du rapport HTML...")

        cmd = [sys.executable, '-m', 'coverage', 'html', '-d', 'htmlcov']

        try:
            subprocess.run(cmd, cwd=self.test_dir, check=True)
            print("✅ Rapport HTML généré dans: test/htmlcov/index.html")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False

    def analyze_module_coverage(self) -> Dict[str, Dict]:
        """Analyse la couverture par module"""
        print("\n📈 Analyse de la couverture par module...\n")

        cmd = [sys.executable, '-m', 'coverage', 'json', '-o', 'coverage.json']

        try:
            subprocess.run(cmd, cwd=self.test_dir, check=True, capture_output=True)

            json_path = self.test_dir / 'coverage.json'
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Organiser par structure du projet
                organized = self._organize_by_structure(data)
                return organized

        except Exception as e:
            print(f"⚠️  Impossible de générer l'analyse JSON: {e}")

        return {}

    def _organize_by_structure(self, coverage_data: Dict) -> Dict:
        """Organise les données de coverage selon la structure du projet"""
        organized = {}

        files = coverage_data.get('files', {})

        for category, modules in self.PROJECT_STRUCTURE.items():
            organized[category] = {}

            for module_name, description in modules.items():
                # Chercher le fichier dans les données de coverage
                for file_path, file_data in files.items():
                    if module_name in file_path:
                        coverage_percent = file_data['summary']['percent_covered']
                        organized[category][module_name] = {
                            'description': description,
                            'coverage': coverage_percent,
                            'lines_covered': file_data['summary']['covered_lines'],
                            'lines_total': file_data['summary']['num_statements'],
                            'missing_lines': file_data['summary']['missing_lines']
                        }
                        break
                else:
                    # Module non trouvé dans coverage
                    organized[category][module_name] = {
                        'description': description,
                        'coverage': 0,
                        'lines_covered': 0,
                        'lines_total': 0,
                        'missing_lines': 0,
                        'status': 'non_testé'
                    }

        return organized

    def print_coverage_tree(self, organized_data: Dict):
        """Affiche un arbre de couverture"""
        print("="*80)
        print("  ARBRE DE COUVERTURE DES TESTS")
        print("="*80)
        print()

        # Statistiques globales
        total_coverage = 0
        total_modules = 0
        tested_modules = 0

        for category, modules in organized_data.items():
            if category == 'root':
                print("📁 Racine du projet")
            else:
                print(f"📁 {category}/")

            for module_name, data in modules.items():
                coverage = data['coverage']
                total_coverage += coverage
                total_modules += 1

                if coverage > 0:
                    tested_modules += 1

                # Icône selon le niveau de couverture
                if coverage >= 90:
                    icon = "🟢"
                elif coverage >= 70:
                    icon = "🟡"
                elif coverage >= 50:
                    icon = "🟠"
                elif coverage > 0:
                    icon = "🔴"
                else:
                    icon = "⚫"

                status = data.get('status', '')
                status_text = f" ({status})" if status else ""

                print(f"   {icon} {module_name:<30} {coverage:>6.1f}%  {data['description']}{status_text}")

            print()

        # Résumé
        avg_coverage = total_coverage / total_modules if total_modules > 0 else 0

        print("="*80)
        print("  RÉSUMÉ")
        print("="*80)
        print(f"📊 Couverture moyenne: {avg_coverage:.1f}%")
        print(f"📦 Modules analysés: {total_modules}")
        print(f"✅ Modules testés: {tested_modules}")
        print(f"⚫ Modules non testés: {total_modules - tested_modules}")
        print()

        # Légende
        print("🟢 ≥90%  |  🟡 70-89%  |  🟠 50-69%  |  🔴 1-49%  |  ⚫ 0%")
        print()

    def identify_untested_modules(self, organized_data: Dict) -> List[Tuple[str, str]]:
        """Identifie les modules non testés"""
        untested = []

        for category, modules in organized_data.items():
            for module_name, data in modules.items():
                if data['coverage'] == 0:
                    untested.append((f"{category}/{module_name}", data['description']))

        return untested

    def generate_recommendations(self, organized_data: Dict):
        """Génère des recommandations pour améliorer la couverture"""
        print("="*80)
        print("  RECOMMANDATIONS")
        print("="*80)
        print()

        untested = self.identify_untested_modules(organized_data)

        if untested:
            print("🎯 Modules prioritaires à tester:")
            print()
            for i, (path, desc) in enumerate(untested[:5], 1):
                print(f"{i}. {path}")
                print(f"   📝 {desc}")
                print()

        # Recommandations par niveau
        low_coverage = []
        medium_coverage = []

        for category, modules in organized_data.items():
            for module_name, data in modules.items():
                coverage = data['coverage']
                if 0 < coverage < 50:
                    low_coverage.append((f"{category}/{module_name}", coverage))
                elif 50 <= coverage < 90:
                    medium_coverage.append((f"{category}/{module_name}", coverage))

        if low_coverage:
            print("🔴 Modules avec faible couverture (<50%):")
            for path, cov in sorted(low_coverage, key=lambda x: x[1]):
                print(f"   • {path}: {cov:.1f}%")
            print()

        if medium_coverage:
            print("🟡 Modules à améliorer (50-90%):")
            for path, cov in sorted(medium_coverage, key=lambda x: x[1]):
                print(f"   • {path}: {cov:.1f}%")
            print()

        print("💡 Actions recommandées:")
        print("   1. Créer des tests pour les modules non testés")
        print("   2. Améliorer la couverture des modules <90%")
        print("   3. Ajouter des tests pour les cas limites")
        print("   4. Tester les chemins d'erreur")
        print()


def main():
    """Fonction principale"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Analyse la couverture de tests du projet EDT',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--run',
        action='store_true',
        help='Lance les tests avec coverage'
    )

    parser.add_argument(
        '--html',
        action='store_true',
        help='Génère un rapport HTML'
    )

    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Analyse détaillée par module'
    )

    parser.add_argument(
        '--test-file',
        type=str,
        help='Fichier de test spécifique à analyser'
    )

    parser.add_argument(
        '--full',
        action='store_true',
        help='Analyse complète (run + html + analyze)'
    )

    args = parser.parse_args()

    analyzer = CoverageAnalyzer()

    # Mode complet par défaut si aucune option
    if not any([args.run, args.html, args.analyze, args.full]):
        args.full = True

    # Exécution
    if args.full or args.run:
        if not analyzer.run_coverage(args.test_file):
            print("\n❌ Échec de l'exécution du coverage")
            sys.exit(1)

    if args.full or args.analyze:
        organized = analyzer.analyze_module_coverage()
        if organized:
            analyzer.print_coverage_tree(organized)
            analyzer.generate_recommendations(organized)

    if args.full or args.html:
        analyzer.generate_html_report()

    # Toujours afficher le rapport terminal
    print("\n" + "="*80)
    print("  RAPPORT DE COUVERTURE DÉTAILLÉ")
    print("="*80)
    print()
    report = analyzer.generate_report('term')
    print(report)


if __name__ == '__main__':
    main()