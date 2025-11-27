"""Unit tests for image transformers."""

import pytest
from pathlib import Path
from PIL import Image
import numpy as np
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from transformers.image_transformer import ImageTransformer


@pytest.fixture
def sample_image(tmp_path):
    """Create a sample test image."""
    img = Image.new('RGB', (100, 100), color='red')
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return img_path


@pytest.fixture
def transformer(tmp_path):
    """Create an ImageTransformer instance."""
    return ImageTransformer(output_dir=str(tmp_path / "transformed"))


def test_jpeg_compression(transformer):
    """Test JPEG compression transformation."""
    img = Image.new('RGB', (100, 100), color='blue')
    compressed = transformer.apply_jpeg_compression(img, quality=50)

    assert compressed is not None
    assert compressed.size == img.size


def test_resize(transformer):
    """Test image resizing."""
    img = Image.new('RGB', (100, 100), color='green')
    resized = transformer.apply_resize(img, scale_factor=0.5)

    assert resized is not None
    assert resized.size == (50, 50)


def test_rotation(transformer):
    """Test image rotation."""
    img = Image.new('RGB', (100, 100), color='yellow')
    rotated = transformer.apply_rotation(img, angle=45)

    assert rotated is not None
    # Rotated image will be larger due to expand=True
    assert rotated.size[0] >= img.size[0]


def test_gaussian_noise(transformer):
    """Test Gaussian noise addition."""
    img = Image.new('RGB', (100, 100), color='purple')
    noisy = transformer.apply_gaussian_noise(img, intensity=0.1)

    assert noisy is not None
    assert noisy.size == img.size

    # Verify that noise was actually added (images should be different)
    img_array = np.array(img)
    noisy_array = np.array(noisy)
    assert not np.array_equal(img_array, noisy_array)


def test_blur(transformer):
    """Test blur transformation."""
    img = Image.new('RGB', (100, 100), color='orange')
    blurred = transformer.apply_blur(img, kernel_size=5)

    assert blurred is not None
    assert blurred.size == img.size


def test_crop(transformer):
    """Test image cropping."""
    img = Image.new('RGB', (100, 100), color='cyan')
    cropped = transformer.apply_crop(img, crop_percentage=0.1)

    assert cropped is not None
    # Image should be smaller after cropping
    assert cropped.size[0] < img.size[0]
    assert cropped.size[1] < img.size[1]


def test_brightness_adjustment(transformer):
    """Test brightness adjustment."""
    img = Image.new('RGB', (100, 100), color='gray')
    brighter = transformer.apply_brightness(img, factor=1.5)

    assert brighter is not None
    assert brighter.size == img.size


def test_contrast_adjustment(transformer):
    """Test contrast adjustment."""
    img = Image.new('RGB', (100, 100), color='pink')
    contrasted = transformer.apply_contrast(img, factor=1.5)

    assert contrasted is not None
    assert contrasted.size == img.size


def test_transform_image(transformer, sample_image):
    """Test complete image transformation workflow."""
    transformations = [
        {'type': 'compression', 'quality': 85},
        {'type': 'resize', 'scale_factor': 0.75},
        {'type': 'rotation', 'angle': 15},
    ]

    results = transformer.transform_image(sample_image, transformations)

    assert len(results) == len(transformations)
    for output_path, metadata in results:
        assert output_path.exists()
        assert 'transformation' in metadata
        assert 'timestamp' in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
