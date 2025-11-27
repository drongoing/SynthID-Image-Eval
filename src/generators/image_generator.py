"""Image generation module using Google's Imagen and other models."""

import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel
from loguru import logger
from PIL import Image
import io


class ImageGenerator:
    """Generate images using Google's image generation models."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "imagegeneration@006",
        output_dir: str = "data/generated",
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the image generator.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud location/region
            model_name: Name of the image generation model
            output_dir: Directory to save generated images
            credentials_path: Path to service account credentials JSON (optional)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set credentials if provided
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

        # Load the model
        try:
            self.model = ImageGenerationModel.from_pretrained(model_name)
            logger.info(f"Loaded image generation model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

        # Metadata storage
        self.metadata: List[Dict[str, Any]] = []

    def generate_images(
        self,
        prompt: str,
        num_images: int = 1,
        negative_prompt: Optional[str] = None,
        guidance_scale: float = 15,
        seed: Optional[int] = None,
        save_metadata: bool = True
    ) -> List[Path]:
        """
        Generate images from a text prompt.

        Args:
            prompt: Text description of the image to generate
            num_images: Number of images to generate
            negative_prompt: Things to avoid in the generated image
            guidance_scale: How closely to follow the prompt (1-20, higher = more strict)
            seed: Random seed for reproducibility
            save_metadata: Whether to save metadata about the generation

        Returns:
            List of paths to generated image files
        """
        logger.info(f"Generating {num_images} images for prompt: '{prompt}'")

        generated_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        try:
            # Generate images
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=num_images,
                guidance_scale=guidance_scale,
                seed=seed,
                negative_prompt=negative_prompt
            )

            # Save each generated image
            for idx, image in enumerate(response.images):
                # Create filename
                safe_prompt = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in prompt)
                safe_prompt = safe_prompt[:50]  # Limit length
                filename = f"{timestamp}_{safe_prompt}_{idx}.png"
                filepath = self.output_dir / filename

                # Save image
                image._pil_image.save(filepath, "PNG")
                generated_files.append(filepath)

                logger.info(f"Saved generated image to {filepath}")

                # Store metadata
                if save_metadata:
                    metadata = {
                        "filename": str(filepath),
                        "prompt": prompt,
                        "negative_prompt": negative_prompt,
                        "guidance_scale": guidance_scale,
                        "seed": seed,
                        "model": self.model_name,
                        "timestamp": timestamp,
                        "image_index": idx,
                        "has_synthid": True  # Assume Google's models apply SynthID
                    }
                    self.metadata.append(metadata)

        except Exception as e:
            logger.error(f"Error generating images: {e}")
            raise

        return generated_files

    def generate_batch(
        self,
        prompts: List[str],
        images_per_prompt: int = 1,
        **kwargs
    ) -> Dict[str, List[Path]]:
        """
        Generate images for multiple prompts.

        Args:
            prompts: List of text prompts
            images_per_prompt: Number of images to generate per prompt
            **kwargs: Additional arguments passed to generate_images()

        Returns:
            Dictionary mapping prompts to lists of generated image paths
        """
        results = {}

        for prompt in prompts:
            logger.info(f"Processing prompt: '{prompt}'")
            try:
                generated = self.generate_images(
                    prompt=prompt,
                    num_images=images_per_prompt,
                    **kwargs
                )
                results[prompt] = generated

                # Small delay to avoid rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Failed to generate images for prompt '{prompt}': {e}")
                results[prompt] = []

        return results

    def save_metadata(self, output_file: Optional[str] = None):
        """
        Save generation metadata to JSON file.

        Args:
            output_file: Path to output JSON file (optional)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"metadata_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Saved metadata to {output_file}")

    def get_metadata(self) -> List[Dict[str, Any]]:
        """Get all generation metadata."""
        return self.metadata


def main():
    """CLI interface for image generation."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate images using Google's models")
    parser.add_argument('--project-id', required=True, help='Google Cloud project ID')
    parser.add_argument('--location', default='us-central1', help='Google Cloud location')
    parser.add_argument('--prompt', required=True, help='Text prompt for image generation')
    parser.add_argument('--count', type=int, default=1, help='Number of images to generate')
    parser.add_argument('--output-dir', default='data/generated', help='Output directory')
    parser.add_argument('--model', default='imagegeneration@006', help='Model name')
    parser.add_argument('--guidance-scale', type=float, default=15, help='Guidance scale (1-20)')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--credentials', help='Path to credentials JSON file')

    args = parser.parse_args()

    # Create generator
    generator = ImageGenerator(
        project_id=args.project_id,
        location=args.location,
        model_name=args.model,
        output_dir=args.output_dir,
        credentials_path=args.credentials
    )

    # Generate images
    generated = generator.generate_images(
        prompt=args.prompt,
        num_images=args.count,
        guidance_scale=args.guidance_scale,
        seed=args.seed
    )

    # Save metadata
    generator.save_metadata()

    print(f"\nGenerated {len(generated)} images:")
    for filepath in generated:
        print(f"  - {filepath}")


if __name__ == "__main__":
    main()
