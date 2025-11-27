# SynthID-Image-Eval

A security research tool for evaluating the detection performance of Google's SynthID AI-generated image detection feature.

## Purpose

This repository supports security research to identify potential vulnerabilities in Google's SynthID image detection system. The objective is to conduct responsible security testing and share any identified vulnerabilities with Google for improvement of their detection capabilities.

## Features

- **Automated Image Generation**: Generate images using Google's image generation models (Imagen, etc.)
- **Image Transformation Pipeline**: Apply various transformations to AI-generated images at different intensity levels
- **Detection Testing**: Test whether Google's Gemini can detect SynthID watermarks in transformed images
- **Baseline Comparison**: Create and compare against baselines using original non-transformed images
- **Results Visualization**: Present findings in human-readable reports and visualizations

## Project Structure

```
SynthID-Image-Eval/
├── src/
│   ├── generators/         # Image generation modules
│   ├── transformers/       # Image transformation modules
│   ├── detectors/          # SynthID detection testing modules
│   └── utils/              # Utility functions
├── data/
│   ├── generated/          # Original AI-generated images
│   ├── transformed/        # Transformed images
│   └── baseline/           # Baseline test images
├── results/                # Test results and reports
├── config/                 # Configuration files
├── tests/                  # Unit tests
└── notebooks/              # Jupyter notebooks for analysis
```

## Setup

### Prerequisites

- Python 3.8+
- Google Cloud Platform account with API access
- API keys for:
  - Google Imagen (or other Google image generation services)
  - Google Gemini API

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd SynthID-Image-Eval
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API credentials:
```bash
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys
```

## Usage

### Quick Start

Run a complete evaluation pipeline:

```bash
python src/main.py --config config/config.yaml
```

### Individual Components

#### Generate Images

```bash
python src/generators/image_generator.py --prompt "A sunset over mountains" --count 10
```

#### Transform Images

```bash
python src/transformers/image_transformer.py --input data/generated/ --output data/transformed/
```

#### Test Detection

```bash
python src/detectors/synthid_detector.py --input data/transformed/ --output results/
```

### Advanced Usage

See `notebooks/example_usage.ipynb` for detailed examples and custom workflows.

## Transformation Types

The toolkit supports various image transformations:

- **Compression**: JPEG compression at varying quality levels
- **Resizing**: Scale images up/down
- **Rotation**: Rotate by various angles
- **Noise**: Add Gaussian, salt-and-pepper, or speckle noise
- **Filters**: Blur, sharpen, edge detection
- **Color Adjustments**: Brightness, contrast, saturation modifications
- **Cropping**: Remove portions of the image
- **Format Conversion**: Convert between image formats
- **Steganography**: Embed additional data

## Results

Results are stored in the `results/` directory and include:

- Detection success/failure rates
- Transformation resilience analysis
- Comparative visualizations
- Detailed logs and metadata

## Ethical Guidelines

This tool is intended for:
- ✅ Authorized security research
- ✅ Defensive security testing
- ✅ Educational purposes
- ✅ Responsible disclosure to Google

This tool should NOT be used for:
- ❌ Malicious watermark removal
- ❌ Mass generation of undetectable AI content
- ❌ Circumventing detection for deceptive purposes

## Responsible Disclosure

Any vulnerabilities discovered should be reported to Google through their Vulnerability Reward Program (VRP):
- https://bughunters.google.com/

## License

[Specify License]

## Contributing

Contributions are welcome! Please ensure all contributions align with ethical security research practices.

## Disclaimer

This tool is for security research and educational purposes only. Users are responsible for ensuring their use complies with applicable laws and Google's Terms of Service.
