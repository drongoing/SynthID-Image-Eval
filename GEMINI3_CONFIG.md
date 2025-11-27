# Gemini 3 Configuration Guide

This guide shows how to configure SynthID-Image-Eval to use the latest Gemini 3 models for both image generation and detection.

## Model Information

**Gemini 3 Pro Image Preview** (`gemini-3-pro-image-preview`)
- Purpose: AI image generation with SynthID watermarking
- Replaces: Imagen models for this research
- API: Google Gemini API

**Gemini 3 Pro Preview** (`gemini-3-pro-preview`)
- Purpose: AI-generated image detection
- API: Google Gemini API

## Configuration Files

### 1. .env File (Windows Paths)

```bash
# .env - Your actual credentials

# Google Cloud Project ID
GOOGLE_CLOUD_PROJECT=your-actual-project-id

# Path to service account credentials (use forward slashes on Windows!)
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/YourName/Documents/gcp-credentials.json

# Gemini API Key (REQUIRED for Gemini 3 models)
GEMINI_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Optional: Override model names (can also set in config.yaml)
IMAGE_GENERATION_MODEL=gemini-3-pro-image-preview
DETECTION_MODEL=gemini-3-pro-preview
```

### 2. config/config.yaml File

```yaml
# config/config.yaml - Your main configuration

google_cloud:
  project_id: "your-actual-project-id"
  location: "us-central1"
  credentials_path: "C:/Users/YourName/Documents/gcp-credentials.json"

api_keys:
  gemini_api_key: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"

# IMAGE GENERATION - Gemini 3 Pro Image Preview
generation:
  model: "gemini-3-pro-image-preview"  # ✅ Latest Gemini 3

  default_prompts:
    - "A photorealistic sunset over mountains"
    - "A cat sitting on a windowsill"
    - "Abstract geometric patterns"
  images_per_prompt: 5
  output_format: "PNG"
  resolution:
    width: 1024
    height: 1024

# DETECTION - Gemini 3 Pro Preview
detection:
  model: "gemini-3-pro-preview"  # ✅ Latest Gemini 3
  batch_size: 10
  retry_attempts: 3
  timeout: 30

  detection_prompt: |
    Analyze this image and determine if it appears to be AI-generated.
    Look for signs of SynthID watermarking or other AI generation artifacts.
    Provide your assessment and confidence level in JSON format:
    {
      "is_ai_generated": true/false,
      "confidence": 0.0-1.0,
      "has_synthid_markers": true/false/unknown,
      "reasoning": "explanation",
      "visual_artifacts": ["list of artifacts"]
    }

# TRANSFORMATIONS (configure which tests to run)
transformations:
  compression:
    enabled: true
    quality_levels: [95, 85, 75, 65, 50, 35, 20]

  resize:
    enabled: true
    scale_factors: [0.5, 0.75, 1.25, 1.5, 2.0]

  rotation:
    enabled: true
    angles: [5, 15, 45, 90, 180]

  noise:
    enabled: true
    types: ["gaussian", "salt_pepper"]
    intensity_levels: [0.01, 0.05, 0.1, 0.2]

  blur:
    enabled: true
    kernel_sizes: [3, 5, 7, 11]

  crop:
    enabled: true
    crop_percentages: [0.05, 0.1, 0.2, 0.3]

  color_adjust:
    enabled: true
    brightness_factors: [0.7, 0.85, 1.15, 1.3]
    contrast_factors: [0.7, 0.85, 1.15, 1.3]
    saturation_factors: [0.5, 0.75, 1.25, 1.5]

# TESTING PARAMETERS
testing:
  baseline_runs: 3
  test_runs_per_transformation: 5
  save_intermediate_results: true
  generate_visualizations: true

# OUTPUT SETTINGS
output:
  results_dir: "results"
  data_dir: "data"
  log_level: "INFO"
  save_transformed_images: true
  generate_report: true
  report_format: "html"

# EXPERIMENT TRACKING
experiment:
  name: "synthid_gemini3_evaluation"
  description: "Testing SynthID robustness using Gemini 3 models"
  track_metadata: true
```

## Setup Steps

### Step 1: Get Your Gemini API Key

1. Visit https://ai.google.dev/
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key

### Step 2: Create Configuration Files

```powershell
# In PowerShell, navigate to your project
cd C:\path\to\SynthID-Image-Eval

# Copy templates
Copy-Item .env.example .env
Copy-Item config\config.example.yaml config\config.yaml

# Edit with your values
notepad .env
notepad config\config.yaml
```

### Step 3: Edit .env (IMPORTANT!)

Open `.env` and replace with your actual values:

```bash
GOOGLE_CLOUD_PROJECT=my-research-project-123456
GOOGLE_APPLICATION_CREDENTIALS=C:/Users/YourName/gcp-key.json
GEMINI_API_KEY=AIzaSyB_your_actual_key_here_xxxxxxxxxxx
IMAGE_GENERATION_MODEL=gemini-3-pro-image-preview
DETECTION_MODEL=gemini-3-pro-preview
```

### Step 4: Edit config.yaml

Open `config/config.yaml` and update:

```yaml
google_cloud:
  project_id: "my-research-project-123456"  # Your actual project ID
  credentials_path: "C:/Users/YourName/gcp-key.json"  # Your actual path

api_keys:
  gemini_api_key: "AIzaSyB_your_actual_key_here_xxxxxxxxxxx"  # Your actual key

generation:
  model: "gemini-3-pro-image-preview"  # Gemini 3 for generation

detection:
  model: "gemini-3-pro-preview"  # Gemini 3 for detection
```

## Testing Your Configuration

### Test 1: Verify Config Loads

```powershell
python -c "
import sys
sys.path.insert(0, 'src')
from utils.config_loader import get_config
config = get_config('config/config.yaml')
print('✅ Generation model:', config.get('generation.model'))
print('✅ Detection model:', config.get('detection.model'))
print('✅ API key loaded:', 'Yes' if config.get('api_keys.gemini_api_key') else 'No')
"
```

Expected output:
```
✅ Generation model: gemini-3-pro-image-preview
✅ Detection model: gemini-3-pro-preview
✅ API key loaded: Yes
```

### Test 2: Test Gemini API Connection

```python
# test_gemini_connection.py
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Test API key
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key found: {bool(api_key)}")

# Configure Gemini
genai.configure(api_key=api_key)

# Test generation model
try:
    gen_model = genai.GenerativeModel("gemini-3-pro-image-preview")
    print("✅ Generation model loaded successfully")
except Exception as e:
    print(f"❌ Generation model error: {e}")

# Test detection model
try:
    det_model = genai.GenerativeModel("gemini-3-pro-preview")
    print("✅ Detection model loaded successfully")
except Exception as e:
    print(f"❌ Detection model error: {e}")
```

Run it:
```powershell
python test_gemini_connection.py
```

### Test 3: Generate One Test Image

```powershell
python src/generators/image_generator.py `
  --project-id your-project-id `
  --model gemini-3-pro-image-preview `
  --prompt "A test sunset" `
  --count 1 `
  --output-dir data/generated
```

Check the output:
```powershell
ls data\generated
```

## How the Code Works

The updated `ImageGenerator` now:

1. **Auto-detects model type** based on the model name
   - If "gemini" is in the name → uses Gemini API
   - Otherwise → uses Vertex AI Imagen API

2. **Uses the appropriate API**:
   ```python
   if "gemini" in model_name.lower():
       # Use google.generativeai API
       model = genai.GenerativeModel(model_name)
   else:
       # Use Vertex AI API
       model = ImageGenerationModel.from_pretrained(model_name)
   ```

3. **Handles both generation paths**:
   - Gemini: `model.generate_content(prompt)`
   - Imagen: `model.generate_images(prompt=...)`

## Running Your First Experiment

### Small Test (Recommended First)

Edit `config/config.yaml`:
```yaml
generation:
  model: "gemini-3-pro-image-preview"
  default_prompts:
    - "A sunset"
  images_per_prompt: 1  # Just 1 image for testing

transformations:
  compression:
    enabled: true
    quality_levels: [50]  # Just one transformation

  resize:
    enabled: false
  rotation:
    enabled: false
  # Disable others...
```

Run:
```powershell
python src\main.py --config config\config.yaml
```

This will:
1. Generate 1 image using Gemini 3 Pro Image
2. Transform it with compression
3. Test detection with Gemini 3 Pro
4. Create a report

Check results:
```powershell
ls results
start results\report_*.html
```

## Troubleshooting

### "API key required" error
- Check that `GEMINI_API_KEY` is set in `.env`
- Verify the key is valid at https://ai.google.dev/

### "Model not found" error
- Ensure you have access to Gemini 3 preview models
- Try using stable models: `gemini-1.5-pro` and `gemini-1.5-flash`
- Check Google AI Studio for available models

### Image generation fails
- Verify your Gemini API quota
- Check that the model supports image generation
- Try with a simpler prompt first

### Rate limiting
- Reduce `batch_size` in config
- Increase delays between requests
- Check your API quotas in GCP Console

## Cost Estimates (Gemini 3)

*Note: Pricing may vary. Check current rates at https://ai.google.dev/pricing*

Estimated costs for a full research experiment:
- 50 original images: ~$2-5
- 2,000 transformed images (detection): ~$5-10
- **Total: $7-15** for a comprehensive study

## Summary Checklist

- [ ] Got Gemini API key from https://ai.google.dev/
- [ ] Created `.env` file with real credentials (NOT committed to git!)
- [ ] Created `config/config.yaml` with model settings
- [ ] Set `generation.model: gemini-3-pro-image-preview`
- [ ] Set `detection.model: gemini-3-pro-preview`
- [ ] Tested configuration loads correctly
- [ ] Tested Gemini API connection
- [ ] Generated first test image
- [ ] Ready to run full pipeline!

You're now configured to use the latest Gemini 3 models for your SynthID security research! 🚀
