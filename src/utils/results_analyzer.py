"""Results analysis and visualization for SynthID evaluation."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from loguru import logger


class ResultsAnalyzer:
    """Analyze and visualize SynthID detection test results."""

    def __init__(self, results_dir: str = "results"):
        """
        Initialize the results analyzer.

        Args:
            results_dir: Directory containing results files
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Set plotting style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 6)

    def load_detection_results(self, results_file: Path) -> List[Dict[str, Any]]:
        """
        Load detection results from JSON file.

        Args:
            results_file: Path to results JSON file

        Returns:
            List of detection results
        """
        with open(results_file, 'r') as f:
            return json.load(f)

    def create_summary_statistics(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """
        Create summary statistics comparing baseline and transformed results.

        Args:
            baseline_results: Detection results for baseline images
            transformed_results: Detection results for transformed images

        Returns:
            DataFrame with summary statistics
        """
        def calculate_stats(results: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
            successful = [r for r in results if r.get('success', False)]
            detected_as_ai = [r for r in successful if r.get('is_ai_generated') == True]
            confidences = [r.get('confidence') for r in successful if r.get('confidence') is not None]

            return {
                'Dataset': label,
                'Total Images': len(results),
                'Successful Detections': len(successful),
                'Detected as AI': len(detected_as_ai),
                'Detection Rate': len(detected_as_ai) / len(successful) if successful else 0,
                'Avg Confidence': np.mean(confidences) if confidences else None,
                'Std Confidence': np.std(confidences) if confidences else None
            }

        baseline_stats = calculate_stats(baseline_results, 'Baseline')
        transformed_stats = calculate_stats(transformed_results, 'Transformed')

        # Calculate evasion metrics
        baseline_rate = baseline_stats['Detection Rate']
        transformed_rate = transformed_stats['Detection Rate']

        evasion_stats = {
            'Dataset': 'Comparison',
            'Total Images': '-',
            'Successful Detections': '-',
            'Detected as AI': '-',
            'Detection Rate': f"{(baseline_rate - transformed_rate):.2%} decrease",
            'Avg Confidence': '-',
            'Std Confidence': '-'
        }

        df = pd.DataFrame([baseline_stats, transformed_stats, evasion_stats])
        return df

    def analyze_by_transformation(
        self,
        results: List[Dict[str, Any]],
        metadata_file: Optional[Path] = None
    ) -> pd.DataFrame:
        """
        Analyze results grouped by transformation type.

        Args:
            results: Detection results
            metadata_file: Optional transformation metadata file

        Returns:
            DataFrame with transformation-based analysis
        """
        # Load metadata if provided
        transformation_map = {}
        if metadata_file and metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                for entry in metadata:
                    img_path = entry.get('transformed_image')
                    transform = entry.get('transformation', {})
                    transformation_map[img_path] = transform

        # Group results by transformation
        transform_groups = {}
        for result in results:
            if not result.get('success'):
                continue

            img_path = result.get('image_path')
            transform_info = transformation_map.get(img_path, {})
            transform_type = transform_info.get('type', 'unknown')

            if transform_type not in transform_groups:
                transform_groups[transform_type] = []
            transform_groups[transform_type].append(result)

        # Calculate statistics per transformation
        stats = []
        for transform_type, group_results in transform_groups.items():
            detected = sum(1 for r in group_results if r.get('is_ai_generated') == True)
            confidences = [r.get('confidence') for r in group_results if r.get('confidence') is not None]

            stats.append({
                'Transformation': transform_type,
                'Count': len(group_results),
                'Detected as AI': detected,
                'Detection Rate': detected / len(group_results) if group_results else 0,
                'Avg Confidence': np.mean(confidences) if confidences else None,
                'Evasion Rate': 1 - (detected / len(group_results)) if group_results else 0
            })

        df = pd.DataFrame(stats)
        df = df.sort_values('Evasion Rate', ascending=False)
        return df

    def plot_detection_rates(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]],
        output_file: Optional[Path] = None
    ):
        """
        Plot detection rates comparison.

        Args:
            baseline_results: Baseline detection results
            transformed_results: Transformed detection results
            output_file: Optional path to save the plot
        """
        # Calculate detection rates
        baseline_detected = sum(1 for r in baseline_results if r.get('success') and r.get('is_ai_generated'))
        baseline_total = sum(1 for r in baseline_results if r.get('success'))

        transformed_detected = sum(1 for r in transformed_results if r.get('success') and r.get('is_ai_generated'))
        transformed_total = sum(1 for r in transformed_results if r.get('success'))

        baseline_rate = baseline_detected / baseline_total if baseline_total > 0 else 0
        transformed_rate = transformed_detected / transformed_total if transformed_total > 0 else 0

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        categories = ['Baseline\n(Original Images)', 'Transformed\n(Modified Images)']
        rates = [baseline_rate * 100, transformed_rate * 100]
        colors = ['#4CAF50', '#FF5722']

        bars = ax.bar(categories, rates, color=colors, alpha=0.7, edgecolor='black')

        # Add value labels on bars
        for bar, rate in zip(bars, rates):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{rate:.1f}%',
                   ha='center', va='bottom', fontsize=12, fontweight='bold')

        ax.set_ylabel('Detection Rate (%)', fontsize=12)
        ax.set_title('SynthID Detection Rate: Baseline vs Transformed Images', fontsize=14, fontweight='bold')
        ax.set_ylim(0, 110)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Saved detection rate plot to {output_file}")
        else:
            plt.savefig(self.results_dir / 'detection_rates.png', dpi=300, bbox_inches='tight')

        plt.close()

    def plot_transformation_effectiveness(
        self,
        transformation_df: pd.DataFrame,
        output_file: Optional[Path] = None
    ):
        """
        Plot effectiveness of different transformations.

        Args:
            transformation_df: DataFrame with transformation analysis
            output_file: Optional path to save the plot
        """
        if transformation_df.empty:
            logger.warning("No transformation data to plot")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

        # Plot 1: Evasion rates by transformation
        df_sorted = transformation_df.sort_values('Evasion Rate', ascending=True)

        ax1.barh(df_sorted['Transformation'], df_sorted['Evasion Rate'] * 100,
                color='coral', alpha=0.7, edgecolor='black')
        ax1.set_xlabel('Evasion Rate (%)', fontsize=12)
        ax1.set_title('Evasion Rate by Transformation Type', fontsize=14, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)

        # Plot 2: Detection rates by transformation
        ax2.barh(df_sorted['Transformation'], df_sorted['Detection Rate'] * 100,
                color='skyblue', alpha=0.7, edgecolor='black')
        ax2.set_xlabel('Detection Rate (%)', fontsize=12)
        ax2.set_title('Detection Rate by Transformation Type', fontsize=14, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Saved transformation effectiveness plot to {output_file}")
        else:
            plt.savefig(self.results_dir / 'transformation_effectiveness.png', dpi=300, bbox_inches='tight')

        plt.close()

    def plot_confidence_distribution(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]],
        output_file: Optional[Path] = None
    ):
        """
        Plot confidence score distributions.

        Args:
            baseline_results: Baseline detection results
            transformed_results: Transformed detection results
            output_file: Optional path to save the plot
        """
        # Extract confidence scores
        baseline_conf = [r.get('confidence') for r in baseline_results
                        if r.get('success') and r.get('confidence') is not None]
        transformed_conf = [r.get('confidence') for r in transformed_results
                           if r.get('success') and r.get('confidence') is not None]

        if not baseline_conf and not transformed_conf:
            logger.warning("No confidence scores available to plot")
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        if baseline_conf:
            ax.hist(baseline_conf, bins=20, alpha=0.6, label='Baseline', color='green', edgecolor='black')
        if transformed_conf:
            ax.hist(transformed_conf, bins=20, alpha=0.6, label='Transformed', color='red', edgecolor='black')

        ax.set_xlabel('Confidence Score', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title('Distribution of Detection Confidence Scores', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            logger.info(f"Saved confidence distribution plot to {output_file}")
        else:
            plt.savefig(self.results_dir / 'confidence_distribution.png', dpi=300, bbox_inches='tight')

        plt.close()

    def generate_html_report(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]],
        transformation_df: Optional[pd.DataFrame] = None,
        output_file: Optional[Path] = None
    ):
        """
        Generate an HTML report with all results.

        Args:
            baseline_results: Baseline detection results
            transformed_results: Transformed detection results
            transformation_df: Optional transformation analysis DataFrame
            output_file: Optional path to save the report
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.results_dir / f"report_{timestamp}.html"

        # Calculate summary statistics
        summary_df = self.create_summary_statistics(baseline_results, transformed_results)

        # Build HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>SynthID Evaluation Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #4CAF50;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #555;
                    margin-top: 30px;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #4CAF50;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .metric {{
                    background-color: #e3f2fd;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #2196F3;
                }}
                .warning {{
                    background-color: #fff3e0;
                    padding: 15px;
                    margin: 10px 0;
                    border-left: 4px solid #FF9800;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>SynthID Image Watermark Evaluation Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

                <div class="warning">
                    <strong>Purpose:</strong> This report presents findings from security research testing
                    the robustness of Google's SynthID image watermarking technology. Results are intended
                    for responsible disclosure to Google.
                </div>

                <h2>Executive Summary</h2>
                {summary_df.to_html(index=False, classes='summary-table')}

                <h2>Key Findings</h2>
                <div class="metric">
                    <strong>Baseline Detection Rate:</strong>
                    {summary_df.iloc[0]['Detection Rate']:.2%}
                </div>
                <div class="metric">
                    <strong>Transformed Detection Rate:</strong>
                    {summary_df.iloc[1]['Detection Rate']:.2%}
                </div>
        """

        if transformation_df is not None and not transformation_df.empty:
            html += f"""
                <h2>Transformation Analysis</h2>
                {transformation_df.to_html(index=False)}
            """

        html += """
            </div>
        </body>
        </html>
        """

        with open(output_file, 'w') as f:
            f.write(html)

        logger.info(f"Generated HTML report: {output_file}")

    def run_full_analysis(
        self,
        baseline_results_file: Path,
        transformed_results_file: Path,
        transformation_metadata_file: Optional[Path] = None
    ):
        """
        Run complete analysis pipeline.

        Args:
            baseline_results_file: Path to baseline results JSON
            transformed_results_file: Path to transformed results JSON
            transformation_metadata_file: Optional transformation metadata JSON
        """
        logger.info("Starting full results analysis")

        # Load results
        baseline_results = self.load_detection_results(baseline_results_file)
        transformed_results = self.load_detection_results(transformed_results_file)

        # Create summary statistics
        summary_df = self.create_summary_statistics(baseline_results, transformed_results)
        print("\n=== Summary Statistics ===")
        print(summary_df.to_string(index=False))

        # Analyze by transformation
        transformation_df = None
        if transformation_metadata_file:
            transformation_df = self.analyze_by_transformation(
                transformed_results,
                transformation_metadata_file
            )
            print("\n=== Transformation Analysis ===")
            print(transformation_df.to_string(index=False))

        # Generate plots
        logger.info("Generating visualization plots")
        self.plot_detection_rates(baseline_results, transformed_results)
        self.plot_confidence_distribution(baseline_results, transformed_results)

        if transformation_df is not None and not transformation_df.empty:
            self.plot_transformation_effectiveness(transformation_df)

        # Generate HTML report
        self.generate_html_report(
            baseline_results,
            transformed_results,
            transformation_df
        )

        logger.info("Analysis complete!")


def main():
    """CLI interface for results analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze SynthID detection results")
    parser.add_argument('--baseline', required=True, help='Baseline results JSON file')
    parser.add_argument('--transformed', required=True, help='Transformed results JSON file')
    parser.add_argument('--metadata', help='Transformation metadata JSON file')
    parser.add_argument('--output-dir', default='results', help='Output directory')

    args = parser.parse_args()

    analyzer = ResultsAnalyzer(results_dir=args.output_dir)
    analyzer.run_full_analysis(
        baseline_results_file=Path(args.baseline),
        transformed_results_file=Path(args.transformed),
        transformation_metadata_file=Path(args.metadata) if args.metadata else None
    )


if __name__ == "__main__":
    main()
