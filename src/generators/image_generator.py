"""Image generation module using Google's Imagen and Gemini models."""

import os
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import io

import google.generativeai as genai
from google.cloud import aiplatform
from loguru import logger
from PIL import Image

# Try to import Vertex AI models (for legacy Imagen support)
try:
    from vertexai.preview.vision_models import ImageGenerationModel
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False
    logger.warning("Vertex AI not available, only Gemini models will be supported")


class ImageGenerator:
    """Generate images using Google's image generation models."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-3-pro-image-preview",
        output_dir: str = "data/generated",
        credentials_path: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the image generator.

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud location/region
            model_name: Name of the image generation model
            output_dir: Directory to save generated images
            credentials_path: Path to service account credentials JSON (optional)
            api_key: Gemini API key (required for Gemini models)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Determine if this is a Gemini or Imagen model
        self.is_gemini_model = "gemini" in model_name.lower()

        # Set credentials if provided
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        # Initialize the appropriate API
        if self.is_gemini_model:
            # Use Gemini API
            if api_key:
                genai.configure(api_key=api_key)
            elif os.getenv('GEMINI_API_KEY'):
                genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            else:
                raise ValueError("Gemini API key required. Set GEMINI_API_KEY or pass api_key parameter")

            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Loaded Gemini image generation model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load Gemini model {model_name}: {e}")
                raise
        else:
            # Use Vertex AI for Imagen models
            if not VERTEX_AI_AVAILABLE:
                raise ImportError("Vertex AI not available. Install with: pip install google-cloud-aiplatform")

            aiplatform.init(project=project_id, location=location)

            try:
                self.model = ImageGenerationModel.from_pretrained(model_name)
                logger.info(f"Loaded Imagen model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load Imagen model {model_name}: {e}")
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
            if self.is_gemini_model:
                # Use Gemini API for image generation
                for i in range(num_images):
                    # Build the generation prompt
                    full_prompt = f"Generate an image: {prompt}"
                    if negative_prompt:
                        full_prompt += f". Avoid: {negative_prompt}"

                    # Generate image
                    response = self.model.generate_content(full_prompt)

                    # Extract image from response
                    pil_image = None

                    # Try different extraction methods
                    if hasattr(response, 'image'):
                        # Direct image attribute (uncommon)
                        pil_image = response.image
                        logger.debug("Extracted image from response.image")

                    elif hasattr(response, 'candidates') and response.candidates:
                        # Navigate through candidates structure (Gemini 3 format)
                        candidate = response.candidates[0]
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'inline_data'):
                                    inline_data = part.inline_data

                                    # The data is already bytes, not base64 encoded
                                    try:
                                        # Try as raw bytes first
                                        pil_image = Image.open(io.BytesIO(inline_data.data))
                                        logger.debug(f"Extracted image as raw bytes (mime: {inline_data.mime_type if hasattr(inline_data, 'mime_type') else 'unknown'})")
                                        break
                                    except Exception as e1:
                                        # Fallback: try base64 decoding
                                        try:
                                            import base64
                                            decoded_data = base64.b64decode(inline_data.data)
                                            pil_image = Image.open(io.BytesIO(decoded_data))
                                            logger.debug("Extracted image after base64 decode")
                                            break
                                        except Exception as e2:
                                            logger.error(f"Failed to extract image: raw={e1}, base64={e2}")
                                            continue

                    elif hasattr(response, 'parts'):
                        # Fallback: try parts directly
                        for part in response.parts:
                            if hasattr(part, 'inline_data'):
                                inline_data = part.inline_data
                                try:
                                    pil_image = Image.open(io.BytesIO(inline_data.data))
                                    logger.debug("Extracted image from response.parts")
                                    break
                                except Exception as e:
                                    logger.error(f"Failed to extract from parts: {e}")
                                    continue

                    if pil_image is None:
                        logger.error(f"Could not extract image from Gemini response")
                        continue

                    # Create filename
                    safe_prompt = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in prompt)
                    safe_prompt = safe_prompt[:50]
                    filename = f"{timestamp}_{safe_prompt}_{i}.png"
                    filepath = self.output_dir / filename

                    # Save image
                    pil_image.save(filepath, "PNG")
                    generated_files.append(filepath)

                    logger.info(f"Saved generated image to {filepath}")

                    # Store metadata
                    if save_metadata:
                        metadata = {
                            "filename": str(filepath),
                            "prompt": prompt,
                            "negative_prompt": negative_prompt,
                            "model": self.model_name,
                            "timestamp": timestamp,
                            "image_index": i,
                            "has_synthid": True
                        }
                        self.metadata.append(metadata)

                    # Small delay between generations
                    if i < num_images - 1:
                        time.sleep(1)

            else:
                # Use Vertex AI Imagen model
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
                    safe_prompt = safe_prompt[:50]
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
                            "has_synthid": True
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
