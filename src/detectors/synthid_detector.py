"""SynthID watermark detection using Vertex AI WatermarkVerificationModel.

IMPORTANT: This uses the actual SynthID watermark detection API, not visual analysis.
SynthID watermarks are invisible and embedded at the pixel level - they cannot be
detected by asking an LLM to visually analyze images.
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import vertexai
from vertexai.preview.vision_models import Image, WatermarkVerificationModel
from loguru import logger
from tqdm import tqdm


class SynthIDDetector:
    """Detect SynthID watermarks using Vertex AI WatermarkVerificationModel.

    This detector uses Google's official watermark verification API to detect
    invisible SynthID watermarks embedded in AI-generated images.

    Note: This only detects watermarks from Google's AI tools (Imagen, Gemini image generation).
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        output_dir: str = "results",
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the SynthID watermark detector.

        Args:
            project_id: Google Cloud project ID
            location: GCP region (default: us-central1)
            output_dir: Directory to save detection results
            credentials_path: Path to GCP service account credentials JSON (optional)
        """
        self.project_id = project_id
        self.location = location
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set credentials if provided
        if credentials_path:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        # Initialize Vertex AI
        logger.info(f"Initializing Vertex AI in project {project_id}, location {location}")
        vertexai.init(project=project_id, location=location)

        # Load the watermark verification model
        logger.info("Loading WatermarkVerificationModel (imageverification@001)")
        self.model = WatermarkVerificationModel.from_pretrained("imageverification@001")

        self.results: List[Dict[str, Any]] = []

    def detect_single_image(
        self,
        image_path: Path,
        retries: int = 3
    ) -> Dict[str, Any]:
        """
        Detect SynthID watermark in a single image.

        Args:
            image_path: Path to the image file
            retries: Number of retry attempts

        Returns:
            Detection result dictionary with watermark_detected and confidence
        """
        logger.info(f"Detecting watermark in: {image_path.name}")

        for attempt in range(retries):
            try:
                # Load image using Vertex AI Image class
                image = Image.load_from_file(str(image_path))

                # Verify watermark using the dedicated API
                response = self.model.verify_image(image=image)

                # Extract results from response
                watermark_detected = response.watermark_detected
                confidence = response.confidence if hasattr(response, 'confidence') else None

                result = {
                    "image_path": str(image_path),
                    "success": True,
                    "watermark_detected": watermark_detected,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"Watermark detected: {watermark_detected}, Confidence: {confidence}")
                return result

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed for {image_path.name}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All attempts failed for {image_path.name}")
                    return {
                        "image_path": str(image_path),
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

    def detect_batch(
        self,
        image_paths: List[Path],
        batch_size: int = 10,
        delay: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Detect SynthID watermarks in multiple images.

        Args:
            image_paths: List of image paths
            batch_size: Number of images to process before a longer pause
            delay: Delay between requests in seconds

        Returns:
            List of detection results
        """
        results = []

        logger.info(f"Processing {len(image_paths)} images")

        for idx, image_path in enumerate(tqdm(image_paths, desc="Detecting SynthID watermarks")):
            result = self.detect_single_image(image_path)
            results.append(result)
            self.results.append(result)

            # Rate limiting
            if (idx + 1) % batch_size == 0:
                logger.info(f"Processed {idx + 1} images, pausing...")
                time.sleep(delay * 5)
            else:
                time.sleep(delay)

        return results

    def detect_directory(
        self,
        input_dir: Path,
        file_pattern: str = "*.png",
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Detect SynthID watermarks in all images in a directory.

        Args:
            input_dir: Input directory containing images
            file_pattern: Glob pattern for matching files
            **kwargs: Additional arguments passed to detect_batch()

        Returns:
            List of detection results
        """
        input_dir = Path(input_dir)
        image_files = list(input_dir.glob(file_pattern))

        if not image_files:
            logger.warning(f"No images found in {input_dir} matching {file_pattern}")
            return []

        return self.detect_batch(image_files, **kwargs)

    def compare_with_baseline(
        self,
        baseline_results: List[Dict[str, Any]],
        transformed_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare watermark detection between baseline and transformed images.

        Args:
            baseline_results: Detection results for original images
            transformed_results: Detection results for transformed images

        Returns:
            Comparison statistics
        """
        baseline_detected = sum(
            1 for r in baseline_results
            if r.get('success') and r.get('watermark_detected') == True
        )
        transformed_detected = sum(
            1 for r in transformed_results
            if r.get('success') and r.get('watermark_detected') == True
        )

        baseline_total = len([r for r in baseline_results if r.get('success')])
        transformed_total = len([r for r in transformed_results if r.get('success')])

        comparison = {
            "baseline": {
                "total": baseline_total,
                "watermark_detected": baseline_detected,
                "detection_rate": baseline_detected / baseline_total if baseline_total > 0 else 0
            },
            "transformed": {
                "total": transformed_total,
                "watermark_detected": transformed_detected,
                "detection_rate": transformed_detected / transformed_total if transformed_total > 0 else 0
            },
            "evasion_rate": 1 - (transformed_detected / transformed_total) if transformed_total > 0 else 0,
            "robustness_score": transformed_detected / baseline_detected if baseline_detected > 0 else 0
        }

        return comparison

    def save_results(self, output_file: Optional[str] = None):
        """
        Save detection results to JSON file.

        Args:
            output_file: Path to output JSON file (optional)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"watermark_detection_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Saved watermark detection results to {output_file}")

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all detection results."""
        return self.results


def main():
    """CLI interface for SynthID watermark detection."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect SynthID watermarks using Vertex AI WatermarkVerificationModel"
    )
    parser.add_argument('--project-id', required=True, help='Google Cloud project ID')
    parser.add_argument('--input', required=True, help='Input image or directory')
    parser.add_argument('--output', default='results', help='Output directory')
    parser.add_argument('--location', default='us-central1', help='GCP region')
    parser.add_argument('--credentials', help='Path to GCP service account JSON')
    parser.add_argument('--pattern', default='*.png', help='File pattern for directory input')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')

    args = parser.parse_args()

    # Create detector
    detector = SynthIDDetector(
        project_id=args.project_id,
        location=args.location,
        output_dir=args.output,
        credentials_path=args.credentials
    )

    # Process input
    input_path = Path(args.input)
    if input_path.is_file():
        result = detector.detect_single_image(input_path)
        print(f"\nWatermark detection result for {input_path.name}:")
        print(json.dumps(result, indent=2))
    elif input_path.is_dir():
        results = detector.detect_directory(
            input_path,
            file_pattern=args.pattern,
            batch_size=args.batch_size
        )
        print(f"\nProcessed {len(results)} images")

        # Summary statistics
        detected = sum(1 for r in results if r.get('watermark_detected') == True)
        print(f"Watermarks detected: {detected}/{len(results)}")
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return

    # Save results
    detector.save_results()


if __name__ == "__main__":
    main()
