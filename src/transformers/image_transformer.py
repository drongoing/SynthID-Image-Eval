"""Image transformation module for testing SynthID robustness."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from loguru import logger
from tqdm import tqdm


class ImageTransformer:
    """Apply various transformations to images for robustness testing."""

    def __init__(self, output_dir: str = "data/transformed"):
        """
        Initialize the image transformer.

        Args:
            output_dir: Directory to save transformed images
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata: List[Dict[str, Any]] = []

    def apply_jpeg_compression(
        self,
        image: Image.Image,
        quality: int = 85
    ) -> Image.Image:
        """
        Apply JPEG compression to an image.

        Args:
            image: Input PIL Image
            quality: JPEG quality (1-100, lower = more compression)

        Returns:
            Compressed image
        """
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, format='JPEG', quality=quality)
        buffer.seek(0)
        return Image.open(buffer)

    def apply_resize(
        self,
        image: Image.Image,
        scale_factor: float = 1.0
    ) -> Image.Image:
        """
        Resize an image by a scale factor.

        Args:
            image: Input PIL Image
            scale_factor: Scale factor (e.g., 0.5 = half size, 2.0 = double size)

        Returns:
            Resized image
        """
        new_size = (
            int(image.width * scale_factor),
            int(image.height * scale_factor)
        )
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def apply_rotation(
        self,
        image: Image.Image,
        angle: float = 0
    ) -> Image.Image:
        """
        Rotate an image by a given angle.

        Args:
            image: Input PIL Image
            angle: Rotation angle in degrees

        Returns:
            Rotated image
        """
        return image.rotate(angle, expand=True, fillcolor='white')

    def apply_gaussian_noise(
        self,
        image: Image.Image,
        intensity: float = 0.05
    ) -> Image.Image:
        """
        Add Gaussian noise to an image.

        Args:
            image: Input PIL Image
            intensity: Noise intensity (0.0 to 1.0)

        Returns:
            Noisy image
        """
        img_array = np.array(image).astype(np.float32) / 255.0
        noise = np.random.normal(0, intensity, img_array.shape)
        noisy = np.clip(img_array + noise, 0, 1)
        return Image.fromarray((noisy * 255).astype(np.uint8))

    def apply_salt_pepper_noise(
        self,
        image: Image.Image,
        intensity: float = 0.01
    ) -> Image.Image:
        """
        Add salt-and-pepper noise to an image.

        Args:
            image: Input PIL Image
            intensity: Noise intensity (percentage of pixels affected)

        Returns:
            Noisy image
        """
        img_array = np.array(image).copy()
        num_pixels = int(intensity * img_array.size)

        # Add salt (white pixels)
        coords = [np.random.randint(0, i, num_pixels // 2) for i in img_array.shape[:2]]
        img_array[coords[0], coords[1]] = 255

        # Add pepper (black pixels)
        coords = [np.random.randint(0, i, num_pixels // 2) for i in img_array.shape[:2]]
        img_array[coords[0], coords[1]] = 0

        return Image.fromarray(img_array)

    def apply_blur(
        self,
        image: Image.Image,
        kernel_size: int = 5
    ) -> Image.Image:
        """
        Apply Gaussian blur to an image.

        Args:
            image: Input PIL Image
            kernel_size: Size of blur kernel

        Returns:
            Blurred image
        """
        return image.filter(ImageFilter.GaussianBlur(radius=kernel_size))

    def apply_sharpen(
        self,
        image: Image.Image,
        factor: float = 1.5
    ) -> Image.Image:
        """
        Sharpen an image.

        Args:
            image: Input PIL Image
            factor: Sharpness factor (>1.0 = sharper)

        Returns:
            Sharpened image
        """
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)

    def apply_crop(
        self,
        image: Image.Image,
        crop_percentage: float = 0.1
    ) -> Image.Image:
        """
        Crop edges from an image.

        Args:
            image: Input PIL Image
            crop_percentage: Percentage to crop from each edge (0.0 to 0.5)

        Returns:
            Cropped image
        """
        width, height = image.size
        crop_x = int(width * crop_percentage)
        crop_y = int(height * crop_percentage)

        return image.crop((
            crop_x,
            crop_y,
            width - crop_x,
            height - crop_y
        ))

    def apply_brightness(
        self,
        image: Image.Image,
        factor: float = 1.0
    ) -> Image.Image:
        """
        Adjust image brightness.

        Args:
            image: Input PIL Image
            factor: Brightness factor (0.0 = black, 1.0 = original, >1.0 = brighter)

        Returns:
            Brightness-adjusted image
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def apply_contrast(
        self,
        image: Image.Image,
        factor: float = 1.0
    ) -> Image.Image:
        """
        Adjust image contrast.

        Args:
            image: Input PIL Image
            factor: Contrast factor (0.0 = gray, 1.0 = original, >1.0 = more contrast)

        Returns:
            Contrast-adjusted image
        """
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)

    def apply_saturation(
        self,
        image: Image.Image,
        factor: float = 1.0
    ) -> Image.Image:
        """
        Adjust image saturation.

        Args:
            image: Input PIL Image
            factor: Saturation factor (0.0 = grayscale, 1.0 = original, >1.0 = more saturated)

        Returns:
            Saturation-adjusted image
        """
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    def apply_format_conversion(
        self,
        image: Image.Image,
        format: str = "PNG"
    ) -> Image.Image:
        """
        Convert image format.

        Args:
            image: Input PIL Image
            format: Target format (PNG, JPEG, WEBP, BMP, etc.)

        Returns:
            Converted image
        """
        from io import BytesIO
        buffer = BytesIO()

        # Convert RGBA to RGB for formats that don't support transparency
        if format.upper() in ['JPEG', 'BMP'] and image.mode == 'RGBA':
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[3])
            image = rgb_image

        image.save(buffer, format=format)
        buffer.seek(0)
        return Image.open(buffer)

    def transform_image(
        self,
        image_path: Path,
        transformations: List[Dict[str, Any]],
        output_subdir: Optional[str] = None
    ) -> List[Tuple[Path, Dict[str, Any]]]:
        """
        Apply multiple transformations to an image.

        Args:
            image_path: Path to input image
            transformations: List of transformation configurations
            output_subdir: Optional subdirectory for outputs

        Returns:
            List of (output_path, metadata) tuples
        """
        results = []
        image = Image.open(image_path)

        # Create output directory
        if output_subdir:
            out_dir = self.output_dir / output_subdir
        else:
            out_dir = self.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        base_name = image_path.stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for idx, transform_config in enumerate(transformations):
            try:
                transformed = image.copy()
                transform_type = transform_config.get('type')

                # Apply transformation
                if transform_type == 'compression':
                    transformed = self.apply_jpeg_compression(
                        transformed,
                        quality=transform_config.get('quality', 85)
                    )
                elif transform_type == 'resize':
                    transformed = self.apply_resize(
                        transformed,
                        scale_factor=transform_config.get('scale_factor', 1.0)
                    )
                elif transform_type == 'rotation':
                    transformed = self.apply_rotation(
                        transformed,
                        angle=transform_config.get('angle', 0)
                    )
                elif transform_type == 'gaussian_noise':
                    transformed = self.apply_gaussian_noise(
                        transformed,
                        intensity=transform_config.get('intensity', 0.05)
                    )
                elif transform_type == 'salt_pepper_noise':
                    transformed = self.apply_salt_pepper_noise(
                        transformed,
                        intensity=transform_config.get('intensity', 0.01)
                    )
                elif transform_type == 'blur':
                    transformed = self.apply_blur(
                        transformed,
                        kernel_size=transform_config.get('kernel_size', 5)
                    )
                elif transform_type == 'sharpen':
                    transformed = self.apply_sharpen(
                        transformed,
                        factor=transform_config.get('factor', 1.5)
                    )
                elif transform_type == 'crop':
                    transformed = self.apply_crop(
                        transformed,
                        crop_percentage=transform_config.get('crop_percentage', 0.1)
                    )
                elif transform_type == 'brightness':
                    transformed = self.apply_brightness(
                        transformed,
                        factor=transform_config.get('factor', 1.0)
                    )
                elif transform_type == 'contrast':
                    transformed = self.apply_contrast(
                        transformed,
                        factor=transform_config.get('factor', 1.0)
                    )
                elif transform_type == 'saturation':
                    transformed = self.apply_saturation(
                        transformed,
                        factor=transform_config.get('factor', 1.0)
                    )
                elif transform_type == 'format_conversion':
                    transformed = self.apply_format_conversion(
                        transformed,
                        format=transform_config.get('format', 'PNG')
                    )
                else:
                    logger.warning(f"Unknown transformation type: {transform_type}")
                    continue

                # Save transformed image
                transform_desc = "_".join([f"{k}_{v}" for k, v in transform_config.items()])
                output_filename = f"{base_name}_{transform_desc}_{timestamp}.png"
                output_path = out_dir / output_filename
                transformed.save(output_path)

                # Store metadata
                metadata = {
                    "original_image": str(image_path),
                    "transformed_image": str(output_path),
                    "transformation": transform_config,
                    "timestamp": timestamp
                }
                self.metadata.append(metadata)
                results.append((output_path, metadata))

                logger.info(f"Applied {transform_type} to {image_path.name} -> {output_filename}")

            except Exception as e:
                logger.error(f"Error applying transformation {transform_config}: {e}")

        return results

    def transform_directory(
        self,
        input_dir: Path,
        transformations: List[Dict[str, Any]],
        file_pattern: str = "*.png"
    ) -> Dict[str, List[Tuple[Path, Dict[str, Any]]]]:
        """
        Transform all images in a directory.

        Args:
            input_dir: Input directory containing images
            transformations: List of transformation configurations
            file_pattern: Glob pattern for matching files

        Returns:
            Dictionary mapping input files to lists of (output_path, metadata) tuples
        """
        input_dir = Path(input_dir)
        image_files = list(input_dir.glob(file_pattern))

        if not image_files:
            logger.warning(f"No images found in {input_dir} matching {file_pattern}")
            return {}

        results = {}
        logger.info(f"Processing {len(image_files)} images with {len(transformations)} transformations")

        for image_file in tqdm(image_files, desc="Transforming images"):
            results[str(image_file)] = self.transform_image(
                image_file,
                transformations
            )

        return results

    def save_metadata(self, output_file: Optional[str] = None):
        """
        Save transformation metadata to JSON file.

        Args:
            output_file: Path to output JSON file (optional)
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"transformation_metadata_{timestamp}.json"

        with open(output_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

        logger.info(f"Saved transformation metadata to {output_file}")


def main():
    """CLI interface for image transformation."""
    import argparse

    parser = argparse.ArgumentParser(description="Transform images for SynthID testing")
    parser.add_argument('--input', required=True, help='Input image or directory')
    parser.add_argument('--output', default='data/transformed', help='Output directory')
    parser.add_argument('--pattern', default='*.png', help='File pattern for directory input')

    args = parser.parse_args()

    # Example transformations
    transformations = [
        {'type': 'compression', 'quality': 85},
        {'type': 'compression', 'quality': 50},
        {'type': 'resize', 'scale_factor': 0.5},
        {'type': 'rotation', 'angle': 5},
        {'type': 'gaussian_noise', 'intensity': 0.05},
        {'type': 'blur', 'kernel_size': 5},
    ]

    transformer = ImageTransformer(output_dir=args.output)

    input_path = Path(args.input)
    if input_path.is_file():
        results = transformer.transform_image(input_path, transformations)
        print(f"\nGenerated {len(results)} transformed images")
    elif input_path.is_dir():
        results = transformer.transform_directory(
            input_path,
            transformations,
            file_pattern=args.pattern
        )
        total = sum(len(v) for v in results.values())
        print(f"\nGenerated {total} transformed images from {len(results)} source images")
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        return

    transformer.save_metadata()


if __name__ == "__main__":
    main()
