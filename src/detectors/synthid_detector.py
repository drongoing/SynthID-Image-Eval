"""SynthID detection testing module using Google's Gemini API."""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

import google.generativeai as genai
from PIL import Image
from loguru import logger
from tqdm import tqdm


class SynthIDDetector:
    """Test SynthID detection using Google's Gemini models."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-3-pro-preview",
        output_dir: str = "results",
        detection_prompt: Optional[str] = None
    ):
        """
        Initialize the SynthID detector.

        Args:
            api_key: Google Gemini API key
            model_name: Name of the Gemini model to use
            output_dir: Directory to save detection results
            detection_prompt: Custom prompt for detection (optional)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configure Gemini API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

        # Default detection prompt
        if detection_prompt is None:
            self.detection_prompt = """Analyze this image carefully and determine if it appears to be AI-generated.

Please consider:
1. Does this image show signs of being created by AI/machine learning models?
2. Can you detect any watermarking or identification markers (like Google's SynthID)?
3. Are there any visual artifacts typical of AI-generated images?
4. What is your confidence level in this assessment?

Provide your response in the following JSON format:
{
    "is_ai_generated": true/false,
    "confidence": 0.0-1.0,
    "has_synthid_markers": true/false/unknown,
    "reasoning": "Brief explanation of your assessment",
    "visual_artifacts": ["list of observed artifacts if any"]
}"""
        else:
            self.detection_prompt = detection_prompt

        self.results: List[Dict[str, Any]] = []

    def detect_single_image(
        self,
        image_path: Path,
        retries: int = 3,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Test SynthID detection on a single image.

        Args:
            image_path: Path to the image file
            retries: Number of retry attempts
            timeout: Timeout in seconds

        Returns:
            Detection result dictionary
        """
        logger.info(f"Analyzing image: {image_path.name}")

        for attempt in range(retries):
            try:
                # Load image
                image = Image.open(image_path)

                # Generate response
                response = self.model.generate_content(
                    [self.detection_prompt, image],
                    request_options={"timeout": timeout}
                )

                # Parse response
                result = self._parse_response(response.text, image_path)
                logger.info(f"Detection result: AI-generated={result.get('is_ai_generated')}, "
                          f"Confidence={result.get('confidence')}")

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

    def _parse_response(self, response_text: str, image_path: Path) -> Dict[str, Any]:
        """
        Parse Gemini API response.

        Args:
            response_text: Raw response text from Gemini
            image_path: Path to the analyzed image

        Returns:
            Parsed result dictionary
        """
        result = {
            "image_path": str(image_path),
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "raw_response": response_text
        }

        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)

            if json_match:
                parsed = json.loads(json_match.group())
                result.update({
                    "is_ai_generated": parsed.get("is_ai_generated", None),
                    "confidence": parsed.get("confidence", None),
                    "has_synthid_markers": parsed.get("has_synthid_markers", None),
                    "reasoning": parsed.get("reasoning", ""),
                    "visual_artifacts": parsed.get("visual_artifacts", [])
                })
            else:
                # Fallback: analyze response text
                result["is_ai_generated"] = self._infer_ai_generated(response_text)
                result["confidence"] = None
                result["has_synthid_markers"] = "unknown"
                result["reasoning"] = response_text

        except Exception as e:
            logger.warning(f"Error parsing response: {e}")
            result["parse_error"] = str(e)

        return result

    def _infer_ai_generated(self, text: str) -> Optional[bool]:
        """
        Infer if image is AI-generated from response text.

        Args:
            text: Response text

        Returns:
            True if likely AI-generated, False if not, None if uncertain
        """
        text_lower = text.lower()

        positive_indicators = [
            "ai-generated", "ai generated", "artificial intelligence",
            "machine learning", "synthid", "watermark"
        ]
        negative_indicators = [
            "not ai", "not artificial", "natural", "photograph",
            "real photo", "human-created"
        ]

        positive_count = sum(1 for ind in positive_indicators if ind in text_lower)
        negative_count = sum(1 for ind in negative_indicators if ind in text_lower)

        if positive_count > negative_count:
            return True
        elif negative_count > positive_count:
            return False
        else:
            return None

    def detect_batch(
        self,
        image_paths: List[Path],
        batch_size: int = 10,
        delay: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Test SynthID detection on multiple images.

        Args:
            image_paths: List of image paths
            batch_size: Number of images to process before a longer pause
            delay: Delay between requests in seconds

        Returns:
            List of detection results
        """
        results = []

        logger.info(f"Processing {len(image_paths)} images")

        for idx, image_path in enumerate(tqdm(image_paths, desc="Detecting SynthID")):
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
        Test SynthID detection on all images in a directory.

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
        Compare detection results between baseline and transformed images.

        Args:
            baseline_results: Detection results for original images
            transformed_results: Detection results for transformed images

        Returns:
            Comparison statistics
        """
        baseline_detected = sum(
            1 for r in baseline_results
            if r.get('success') and r.get('is_ai_generated') == True
        )
        transformed_detected = sum(
            1 for r in transformed_results
            if r.get('success') and r.get('is_ai_generated') == True
        )

        baseline_total = len([r for r in baseline_results if r.get('success')])
        transformed_total = len([r for r in transformed_results if r.get('success')])

        comparison = {
            "baseline": {
                "total": baseline_total,
                "detected_as_ai": baseline_detected,
                "detection_rate": baseline_detected / baseline_total if baseline_total > 0 else 0
            },
            "transformed": {
                "total": transformed_total,
                "detected_as_ai": transformed_detected,
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
            output_file = self.output_dir / f"detection_results_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"Saved detection results to {output_file}")

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all detection results."""
        return self.results


def main():
    """CLI interface for SynthID detection testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Test SynthID detection with Gemini")
    parser.add_argument('--api-key', required=True, help='Google Gemini API key')
    parser.add_argument('--input', required=True, help='Input image or directory')
    parser.add_argument('--output', default='results', help='Output directory')
    parser.add_argument('--model', default='gemini-3-pro-preview', help='Gemini model name')
    parser.add_argument('--pattern', default='*.png', help='File pattern for directory input')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for processing')

    args = parser.parse_args()

    # Create detector
    detector = SynthIDDetector(
        api_key=args.api_key,
        model_name=args.model,
        output_dir=args.output
    )

    # Process input
    input_path = Path(args.input)
    if input_path.is_file():
        result = detector.detect_single_image(input_path)
        print(f"\nDetection result for {input_path.name}:")
        print(json.dumps(result, indent=2))
    elif input_path.is_dir():
        results = detector.detect_directory(
            input_path,
            file_pattern=args.pattern,
            batch_size=args.batch_size
        )
        print(f"\nProcessed {len(results)} images")

        # Summary statistics
        detected = sum(1 for r in results if r.get('is_ai_generated') == True)
        print(f"Detected as AI-generated: {detected}/{len(results)}")
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return

    # Save results
    detector.save_results()


if __name__ == "__main__":
    main()
