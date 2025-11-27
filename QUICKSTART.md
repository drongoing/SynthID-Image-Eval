# Quick Start Guide

This guide will help you get started with SynthID-Image-Eval quickly.

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- Google Gemini API access

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SynthID-Image-Eval
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Configure the application**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # Edit config/config.yaml with your settings
   ```

   Key settings to configure:
   - `google_cloud.project_id`: Your Google Cloud project ID
   - `api_keys.gemini_api_key`: Your Gemini API key
   - `generation.default_prompts`: Prompts for image generation
   - `transformations`: Enable/disable specific transformations

## Usage

### Option 1: Run the Full Pipeline

```bash
python src/main.py --config config/config.yaml
```

This will:
1. Generate images using Google's models
2. Test baseline SynthID detection
3. Apply transformations to images
4. Test detection on transformed images
5. Generate analysis reports

### Option 2: Run Individual Components

**Generate Images:**
```bash
python src/generators/image_generator.py \
  --project-id your-project-id \
  --prompt "A sunset over mountains" \
  --count 5 \
  --output-dir data/generated
```

**Transform Images:**
```bash
python src/transformers/image_transformer.py \
  --input data/generated \
  --output data/transformed
```

**Test Detection:**
```bash
python src/detectors/synthid_detector.py \
  --api-key your-gemini-api-key \
  --input data/transformed \
  --output results
```

**Analyze Results:**
```bash
python src/utils/results_analyzer.py \
  --baseline results/baseline/detection_results_*.json \
  --transformed results/transformed/detection_results_*.json \
  --output-dir results
```

### Option 3: Use Jupyter Notebook

```bash
jupyter notebook notebooks/example_usage.ipynb
```

The notebook provides an interactive walkthrough of all features.

## Example Workflow

Here's a minimal example to test the system:

```python
from pathlib import Path
from generators.image_generator import ImageGenerator
from transformers.image_transformer import ImageTransformer
from detectors.synthid_detector import SynthIDDetector

# 1. Generate an image
generator = ImageGenerator(
    project_id="your-project",
    location="us-central1"
)
images = generator.generate_images(
    prompt="A cat on a windowsill",
    num_images=1
)

# 2. Transform it
transformer = ImageTransformer()
transformations = [
    {'type': 'compression', 'quality': 50},
    {'type': 'rotation', 'angle': 5}
]
results = transformer.transform_image(images[0], transformations)

# 3. Test detection
detector = SynthIDDetector(api_key="your-api-key")
baseline = detector.detect_single_image(images[0])
transformed = detector.detect_batch([r[0] for r in results])

# 4. Compare
print(f"Baseline detected: {baseline.get('is_ai_generated')}")
print(f"Transformed detected: {sum(1 for r in transformed if r.get('is_ai_generated'))}/{len(transformed)}")
```

## Viewing Results

Results are saved in the `results/` directory:

- **JSON files**: Detailed detection results
- **PNG files**: Visualization plots
- **HTML files**: Comprehensive reports

Open the HTML report in your browser:
```bash
open results/report_*.html  # macOS
xdg-open results/report_*.html  # Linux
start results/report_*.html  # Windows
```

## Running Tests

```bash
pytest tests/ -v
```

## Troubleshooting

**API Authentication Errors:**
- Ensure your Google Cloud credentials are properly set
- Check that the service account has necessary permissions
- Verify GEMINI_API_KEY is correct

**Rate Limiting:**
- Adjust `batch_size` in config to process fewer images at once
- Increase delays between API calls

**Out of Memory:**
- Process fewer images at a time
- Reduce image resolution in generation config
- Use smaller transformation batches

## Next Steps

- Review the full [README.md](README.md) for detailed documentation
- Explore the [example notebook](notebooks/example_usage.ipynb)
- Read about [responsible disclosure](README.md#responsible-disclosure)

## Support

For issues and questions:
- Check existing documentation
- Review code comments
- Create an issue in the repository

## Important Reminder

This tool is for **authorized security research only**. Any vulnerabilities discovered should be responsibly disclosed to Google through their Vulnerability Reward Program: https://bughunters.google.com/
