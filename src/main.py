"""Main orchestration script for SynthID-Image-Eval."""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from generators.image_generator import ImageGenerator
from transformers.image_transformer import ImageTransformer
from detectors.synthid_detector import SynthIDDetector
from utils.config_loader import get_config
from utils.results_analyzer import ResultsAnalyzer


class SynthIDEvaluationPipeline:
    """Complete pipeline for SynthID evaluation."""

    def __init__(self, config_path: str = None):
        """
        Initialize the evaluation pipeline.

        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = get_config(config_path)

        # Setup logging
        log_level = self.config.get('output.log_level', 'INFO')
        logger.remove()
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        )

        # Add file logging
        log_file = Path(self.config.get('output.results_dir', 'results')) / 'pipeline.log'
        logger.add(log_file, level=log_level, rotation="10 MB")

        logger.info("Initialized SynthID Evaluation Pipeline")

    def run_image_generation(self) -> List[Path]:
        """
        Generate baseline images.

        Returns:
            List of paths to generated images
        """
        logger.info("=== Phase 1: Image Generation ===")

        # Get configuration
        gcloud_config = self.config.get_google_cloud_config()
        gen_config = self.config.get_generation_config()
        api_keys = self.config.get_api_keys()

        # Initialize generator
        generator = ImageGenerator(
            project_id=gcloud_config.get('project_id'),
            location=gcloud_config.get('location', 'us-central1'),
            model_name=gen_config.get('model', 'gemini-3-pro-image-preview'),
            output_dir=f"{self.config.get('output.data_dir', 'data')}/generated",
            credentials_path=gcloud_config.get('credentials_path'),
            api_key=api_keys.get('gemini_api_key')
        )

        # Generate images
        prompts = gen_config.get('default_prompts', [])
        images_per_prompt = gen_config.get('images_per_prompt', 5)

        logger.info(f"Generating {len(prompts)} prompts × {images_per_prompt} images")

        all_generated = []
        results = generator.generate_batch(
            prompts=prompts,
            images_per_prompt=images_per_prompt,
            guidance_scale=15
        )

        for prompt, files in results.items():
            all_generated.extend(files)
            logger.info(f"Generated {len(files)} images for: '{prompt}'")

        # Save metadata
        generator.save_metadata()

        logger.info(f"Total images generated: {len(all_generated)}")
        return all_generated

    def run_baseline_detection(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        Run baseline detection on original images.

        Args:
            image_paths: List of image paths to test

        Returns:
            List of detection results
        """
        logger.info("=== Phase 2: Baseline Detection ===")

        # Get configuration
        gcloud_config = self.config.get_google_cloud_config()
        detection_config = self.config.get_detection_config()

        # Initialize detector (using Vertex AI WatermarkVerificationModel)
        detector = SynthIDDetector(
            project_id=gcloud_config.get('project_id'),
            location=gcloud_config.get('location', 'us-central1'),
            output_dir=f"{self.config.get('output.results_dir', 'results')}/baseline",
            credentials_path=gcloud_config.get('credentials_path')
        )

        # Run detection
        results = detector.detect_batch(
            image_paths,
            batch_size=detection_config.get('batch_size', 10)
        )

        # Save results
        detector.save_results()

        detected = sum(1 for r in results if r.get('watermark_detected') == True)
        logger.info(f"Baseline detection: {detected}/{len(results)} watermarks detected")

        return results

    def run_transformations(self, image_paths: List[Path]) -> Dict[str, List[Path]]:
        """
        Apply transformations to images.

        Args:
            image_paths: List of image paths to transform

        Returns:
            Dictionary mapping transformation types to transformed image paths
        """
        logger.info("=== Phase 3: Image Transformation ===")

        # Get configuration
        transform_config = self.config.get_transformation_config()
        output_dir = f"{self.config.get('output.data_dir', 'data')}/transformed"

        # Initialize transformer
        transformer = ImageTransformer(output_dir=output_dir)

        # Build transformation list
        transformations = []

        # Compression
        if transform_config.get('compression', {}).get('enabled', True):
            for quality in transform_config['compression'].get('quality_levels', [85, 50]):
                transformations.append({'type': 'compression', 'quality': quality})

        # Resize
        if transform_config.get('resize', {}).get('enabled', True):
            for scale in transform_config['resize'].get('scale_factors', [0.5, 1.5]):
                transformations.append({'type': 'resize', 'scale_factor': scale})

        # Rotation
        if transform_config.get('rotation', {}).get('enabled', True):
            for angle in transform_config['rotation'].get('angles', [5, 45]):
                transformations.append({'type': 'rotation', 'angle': angle})

        # Noise
        if transform_config.get('noise', {}).get('enabled', True):
            for intensity in transform_config['noise'].get('intensity_levels', [0.05]):
                transformations.append({'type': 'gaussian_noise', 'intensity': intensity})

        # Blur
        if transform_config.get('blur', {}).get('enabled', True):
            for kernel in transform_config['blur'].get('kernel_sizes', [5]):
                transformations.append({'type': 'blur', 'kernel_size': kernel})

        # Crop
        if transform_config.get('crop', {}).get('enabled', True):
            for pct in transform_config['crop'].get('crop_percentages', [0.1]):
                transformations.append({'type': 'crop', 'crop_percentage': pct})

        # Color adjustments
        if transform_config.get('color_adjust', {}).get('enabled', True):
            for factor in transform_config['color_adjust'].get('brightness_factors', [0.7, 1.3]):
                transformations.append({'type': 'brightness', 'factor': factor})

        logger.info(f"Applying {len(transformations)} transformations to {len(image_paths)} images")

        # Apply transformations
        all_transformed = {}
        for image_path in image_paths:
            results = transformer.transform_image(image_path, transformations)
            for transformed_path, metadata in results:
                transform_type = metadata['transformation']['type']
                if transform_type not in all_transformed:
                    all_transformed[transform_type] = []
                all_transformed[transform_type].append(transformed_path)

        # Save metadata
        transformer.save_metadata()

        total = sum(len(v) for v in all_transformed.values())
        logger.info(f"Total transformed images: {total}")

        return all_transformed

    def run_transformed_detection(
        self,
        transformed_images: Dict[str, List[Path]]
    ) -> List[Dict[str, Any]]:
        """
        Run detection on transformed images.

        Args:
            transformed_images: Dictionary of transformed image paths

        Returns:
            List of detection results
        """
        logger.info("=== Phase 4: Transformed Image Detection ===")

        # Get configuration
        gcloud_config = self.config.get_google_cloud_config()
        detection_config = self.config.get_detection_config()

        # Initialize detector (using Vertex AI WatermarkVerificationModel)
        detector = SynthIDDetector(
            project_id=gcloud_config.get('project_id'),
            location=gcloud_config.get('location', 'us-central1'),
            output_dir=f"{self.config.get('output.results_dir', 'results')}/transformed",
            credentials_path=gcloud_config.get('credentials_path')
        )

        # Flatten all transformed images
        all_images = []
        for images in transformed_images.values():
            all_images.extend(images)

        # Run detection
        results = detector.detect_batch(
            all_images,
            batch_size=detection_config.get('batch_size', 10)
        )

        # Save results
        detector.save_results()

        detected = sum(1 for r in results if r.get('watermark_detected') == True)
        logger.info(f"Transformed detection: {detected}/{len(results)} watermarks detected")

        return results

    def run_analysis(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]]
    ):
        """
        Analyze and visualize results.

        Args:
            baseline_results: Baseline detection results
            transformed_results: Transformed detection results
        """
        logger.info("=== Phase 5: Results Analysis ===")

        # Get configuration
        output_config = self.config.get_output_config()
        results_dir = output_config.get('results_dir', 'results')

        # Initialize analyzer
        analyzer = ResultsAnalyzer(results_dir=results_dir)

        # Generate summary
        summary_df = analyzer.create_summary_statistics(baseline_results, transformed_results)
        logger.info("\nSummary Statistics:")
        print(summary_df.to_string(index=False))

        # Generate visualizations
        if output_config.get('generate_visualizations', True):
            logger.info("Generating visualizations")
            analyzer.plot_detection_rates(baseline_results, transformed_results)
            analyzer.plot_confidence_distribution(baseline_results, transformed_results)

        # Generate report
        if output_config.get('generate_report', True):
            logger.info("Generating HTML report")
            analyzer.generate_html_report(baseline_results, transformed_results)

    def run_full_pipeline(self):
        """Run the complete evaluation pipeline."""
        logger.info("Starting SynthID Evaluation Pipeline")
        start_time = datetime.now()

        try:
            # Phase 1: Generate images
            generated_images = self.run_image_generation()

            # Phase 2: Baseline detection
            baseline_results = self.run_baseline_detection(generated_images)

            # Phase 3: Transform images
            transformed_images = self.run_transformations(generated_images)

            # Phase 4: Detection on transformed images
            transformed_results = self.run_transformed_detection(transformed_images)

            # Phase 5: Analysis and reporting
            self.run_analysis(baseline_results, transformed_results)

            # Final summary
            elapsed = datetime.now() - start_time
            logger.info(f"\n{'='*60}")
            logger.info(f"Pipeline completed successfully in {elapsed}")
            logger.info(f"{'='*60}")

            # Print key metrics
            baseline_rate = sum(1 for r in baseline_results if r.get('watermark_detected')) / len(baseline_results)
            transformed_rate = sum(1 for r in transformed_results if r.get('watermark_detected')) / len(transformed_results)

            print(f"\n=== Final Results ===")
            print(f"Baseline Watermark Detection Rate: {baseline_rate:.2%}")
            print(f"Transformed Watermark Detection Rate: {transformed_rate:.2%}")
            print(f"Watermark Evasion Rate: {1 - transformed_rate:.2%}")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            raise


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="SynthID Image Watermark Evaluation Pipeline"
    )
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--phase',
        choices=['generate', 'baseline', 'transform', 'detect', 'analyze', 'full'],
        default='full',
        help='Pipeline phase to run'
    )

    args = parser.parse_args()

    # Create and run pipeline
    pipeline = SynthIDEvaluationPipeline(config_path=args.config)

    if args.phase == 'full':
        pipeline.run_full_pipeline()
    else:
        logger.error(f"Individual phases not yet implemented. Use --phase full")
        sys.exit(1)


if __name__ == "__main__":
    main()
