# SynthID-Image-Eval: Step-by-Step Execution Plan

This guide provides a detailed, practical plan for running your SynthID security research project from start to finish.

## Phase 1: Prerequisites & Account Setup

### 1.1 Create Google Cloud Platform Account

1. **Sign up for GCP** (if you don't have an account)
   - Go to https://cloud.google.com/
   - Create a new project or use an existing one
   - Note your **Project ID** (you'll need this)

2. **Enable Required APIs**
   ```
   - Navigate to APIs & Services > Library
   - Search for and enable:
     • Vertex AI API
     • Cloud AI Platform API
   ```

3. **Set up Authentication** (Choose ONE method)

   **Option A: Service Account (Recommended for automation)**
   ```bash
   # In GCP Console:
   # 1. Go to IAM & Admin > Service Accounts
   # 2. Create Service Account
   # 3. Grant roles:
   #    - Vertex AI User
   #    - Storage Object Viewer (if using Cloud Storage)
   # 4. Create and download JSON key
   # 5. Save it as credentials.json in your project root
   ```

   **Option B: User Authentication**
   ```bash
   # Install gcloud CLI: https://cloud.google.com/sdk/docs/install
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

### 1.2 Get Gemini API Key

1. **Obtain Gemini API access** (for image generation only)
   - Go to https://ai.google.dev/
   - Sign in and create an API key
   - This is used for generating images with Gemini 3 Image

2. **Note your API key** - you'll add this to `.env` later

**Important Note on SynthID Detection:**
- SynthID watermark detection uses **Vertex AI WatermarkVerificationModel**, NOT Gemini API
- This is a dedicated watermark detection API (imageverification@001)
- It detects invisible SynthID watermarks embedded at the pixel level
- The service account credentials from step 1.1 are used for detection
- You don't need a separate "detection model" configuration

### 1.3 Check API Quotas

- Go to **APIs & Services > Quotas** in GCP Console
- Check quotas for:
  - Vertex AI image generation (requests per minute)
  - Gemini API (requests per minute)
- Request quota increases if needed for large-scale testing

**Cost Estimate:**
- Image generation (Gemini 3 Image): ~$0.04-0.08 per image
- Watermark detection (Vertex AI): Included with Vertex AI usage
- For 100 images with 10 transformations: ~$5-10 total
- Note: Actual costs depend on your GCP pricing tier and region

---

## Phase 2: Environment Setup

### 2.1 Clone and Navigate to Repository

```bash
cd ~/projects  # or wherever you keep projects
git clone <your-repo-url> SynthID-Image-Eval
cd SynthID-Image-Eval
```

### 2.2 Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Verify activation (should show venv path)
which python
```

### 2.3 Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
python -c "import google.generativeai; import PIL; print('✅ Dependencies installed')"
```

---

## Phase 3: Configuration

### 3.1 Set Up Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit with your actual credentials
nano .env  # or vim, code, etc.
```

Add your real values:
```bash
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/credentials.json
GEMINI_API_KEY=your-actual-gemini-api-key
```

### 3.2 Configure Application Settings

```bash
# Copy the config template
cp config/config.example.yaml config/config.yaml

# Edit with your preferences
nano config/config.yaml
```

**Key settings to customize:**

```yaml
google_cloud:
  project_id: "your-actual-project-id"
  location: "us-central1"  # or your preferred region
  credentials_path: "/path/to/credentials.json"  # or omit if using gcloud auth

api_keys:
  gemini_api_key: "your-actual-api-key"

generation:
  default_prompts:  # Customize these for your research
    - "A photorealistic landscape"
    - "A portrait of a person"
    - "Abstract geometric art"
  images_per_prompt: 3  # Start small for testing

transformations:
  # Enable/disable transformations you want to test
  compression:
    enabled: true
    quality_levels: [85, 70, 50]  # Start with fewer levels

  resize:
    enabled: true
    scale_factors: [0.5, 1.5]

  # Configure others as needed...
```

### 3.3 Verify Configuration

```bash
python -c "import sys; sys.path.insert(0, 'src'); from utils.config_loader import get_config; c = get_config('config/config.yaml'); print('Project:', c.get('google_cloud.project_id')); print('Gen Model:', c.get('generation.model')); print('Location:', c.get('google_cloud.location'))"
```

---

## Phase 4: Test Individual Components

**Start small!** Test each component separately before running the full pipeline.

### 4.1 Test Image Generation

```bash
# Generate a single test image
python src/generators/image_generator.py \
  --project-id YOUR_PROJECT_ID \
  --prompt "A test image of a sunset" \
  --count 1 \
  --output-dir data/generated \
  --credentials config/credentials.json  # if using service account

# Check the output
ls -lh data/generated/
```

**Expected result:** You should see a PNG file generated

**Troubleshooting:**
- If authentication fails, check credentials path
- If API not enabled, enable Vertex AI API in GCP Console
- If quota exceeded, wait or request increase

### 4.2 Test Image Transformation

```bash
# Transform the generated image
python src/transformers/image_transformer.py \
  --input data/generated \
  --output data/transformed

# Check the output
ls -lh data/transformed/
```

**Expected result:** Multiple transformed versions of your image

### 4.3 Test SynthID Detection

```bash
# Test watermark detection on original image using Vertex AI
python src/detectors/synthid_detector.py \
  --project-id YOUR_PROJECT_ID \
  --input data/generated \
  --output results/test \
  --pattern "*.png" \
  --credentials config/credentials.json  # if using service account

# Check results
cat results/test/watermark_detection_*.json
```

**Expected result:** JSON file with watermark detection results showing `watermark_detected: true` for AI-generated images

**Note:** This uses Vertex AI's WatermarkVerificationModel (imageverification@001), which detects the invisible SynthID watermark embedded in images. It does NOT use Gemini for visual analysis.

### 4.4 Test on Transformed Images

```bash
# Test watermark detection on transformed images
python src/detectors/synthid_detector.py \
  --project-id YOUR_PROJECT_ID \
  --input data/transformed \
  --output results/test_transformed \
  --credentials config/credentials.json  # if using service account
```

**Expected result:** Watermark detection results for transformed images (detection rate may vary based on transformation severity - this is what you're testing!)

---

## Phase 5: Run Small-Scale Experiment

### 5.1 Edit Config for Small Test

```yaml
# In config/config.yaml
generation:
  default_prompts:
    - "A sunset over mountains"
    - "A cat on a windowsill"
  images_per_prompt: 2  # Just 2 images per prompt = 4 total

transformations:
  compression:
    enabled: true
    quality_levels: [85, 50]  # Just 2 levels

  resize:
    enabled: true
    scale_factors: [0.75]  # Just 1 scale

  rotation:
    enabled: true
    angles: [5]  # Just 1 angle

  # Disable others for this test
  noise:
    enabled: false
  blur:
    enabled: false
```

### 5.2 Run the Full Pipeline

```bash
# Run the complete pipeline
python src/main.py --config config/config.yaml

# This will:
# 1. Generate 4 images (2 prompts × 2 images)
# 2. Test baseline detection on originals
# 3. Apply 4 transformations to each (4 × 4 = 16 transformed images)
# 4. Test detection on transformed images
# 5. Generate analysis and reports
```

**Time estimate:** 10-20 minutes for this small test

### 5.3 Review Results

```bash
# Check generated images
ls -lh data/generated/

# Check transformed images
ls -lh data/transformed/

# Check results
ls -lh results/

# Open HTML report
open results/report_*.html  # macOS
# or
xdg-open results/report_*.html  # Linux
# or
start results/report_*.html  # Windows
```

**What to look for:**
- Watermark detection rate on baseline images (should be near 100% for Google AI-generated images)
- Watermark detection rate on transformed images (this is your research finding!)
- Which transformations are most effective at breaking the watermark
- Trade-off between image quality and watermark evasion

---

## Phase 6: Scale Up for Full Research

Once the small test works, scale up:

### 6.1 Design Your Experiment

Create a research plan:

```yaml
# Example full-scale config
generation:
  default_prompts:
    - "A photorealistic portrait"
    - "A landscape with mountains"
    - "An abstract geometric artwork"
    - "A street scene in a city"
    - "An animal in nature"
  images_per_prompt: 10  # 5 prompts × 10 = 50 images

transformations:
  compression:
    quality_levels: [95, 85, 75, 65, 50, 35, 20]  # 7 levels

  resize:
    scale_factors: [0.5, 0.75, 1.25, 1.5, 2.0]  # 5 levels

  rotation:
    angles: [5, 15, 45, 90]  # 4 angles

  noise:
    intensity_levels: [0.01, 0.05, 0.1, 0.2]  # 4 levels

  blur:
    kernel_sizes: [3, 5, 7, 11]  # 4 sizes

  crop:
    crop_percentages: [0.05, 0.1, 0.2, 0.3]  # 4 percentages

  color_adjust:
    brightness_factors: [0.7, 0.85, 1.15, 1.3]  # 4 factors
    contrast_factors: [0.7, 0.85, 1.15, 1.3]
    saturation_factors: [0.5, 0.75, 1.25, 1.5]
```

**This would generate:**
- 50 original images
- ~40 transformations × 50 images = 2,000 transformed images
- Total API calls: ~2,050 (baseline + transformed)
- **Estimated cost: $80-100**
- **Estimated time: 4-8 hours** (with rate limiting)

### 6.2 Run in Batches

For large experiments, run in batches to avoid quota issues:

```bash
# Run generation only first
python src/generators/image_generator.py \
  --project-id YOUR_PROJECT_ID \
  --prompt "Batch 1 prompt" \
  --count 10

# Then transformations
python src/transformers/image_transformer.py \
  --input data/generated \
  --output data/transformed

# Then watermark detection in smaller batches
# Edit config.yaml detection.batch_size: 5
python src/detectors/synthid_detector.py \
  --project-id YOUR_PROJECT_ID \
  --input data/transformed \
  --batch-size 5 \
  --credentials config/credentials.json
```

### 6.3 Monitor Progress

```bash
# Check logs
tail -f results/pipeline.log

# Monitor costs in GCP Console
# Billing > Reports
```

---

## Phase 7: Analysis & Reporting

### 7.1 Generate Comprehensive Analysis

```bash
# If you ran components separately, analyze results:
python src/utils/results_analyzer.py \
  --baseline results/baseline/detection_results_*.json \
  --transformed results/transformed/detection_results_*.json \
  --metadata data/transformed/transformation_metadata_*.json \
  --output-dir results/final_analysis
```

### 7.2 Use Jupyter for Custom Analysis

```bash
# Start Jupyter
jupyter notebook notebooks/example_usage.ipynb

# Use the notebook to:
# - Visualize specific transformations
# - Compare different transformation types
# - Generate custom plots
# - Deep-dive into specific findings
```

### 7.3 Key Metrics to Report

For responsible disclosure, document:

1. **Baseline Performance**
   - Watermark detection rate on unmodified AI-generated images from Google's models
   - Confidence scores (if available)

2. **Vulnerability Findings**
   - Which transformations break the SynthID watermark most effectively
   - At what intensity levels watermark detection fails
   - Combination effects of multiple transformations

3. **Reproducibility**
   - Exact transformation parameters
   - Models and versions used
   - Sample images (if non-sensitive)

4. **Impact Assessment**
   - How easy/practical is the evasion technique
   - What level of image quality degradation occurs

---

## Phase 8: Responsible Disclosure

### 8.1 Prepare Your Report

Include:
- Executive summary of findings
- Methodology (transformations tested)
- Results (detection rate changes)
- Proof of concept (sample images if appropriate)
- Suggested mitigations (if you have ideas)

### 8.2 Submit to Google VRP

1. Go to https://bughunters.google.com/
2. Create a new report
3. Select appropriate category (AI/ML security)
4. Provide detailed findings
5. Include your analysis results

### 8.3 Follow Coordinated Disclosure

- Give Google time to respond (typically 90 days)
- Don't publish findings publicly until they acknowledge
- Follow their disclosure timeline

---

## Best Practices & Tips

### Cost Management

```yaml
# For development, use minimal settings:
testing:
  baseline_runs: 1  # Instead of 3
  test_runs_per_transformation: 1  # Instead of 5

detection:
  batch_size: 5  # Smaller batches
```

### Rate Limiting

If you hit rate limits:
- Increase delays in config: `detection.timeout: 60`
- Reduce batch sizes
- Run overnight when quotas reset
- Request quota increases

### Data Management

```bash
# Organize experiments by date
mkdir -p experiments/2024-01-15
cp config/config.yaml experiments/2024-01-15/
cp -r results/* experiments/2024-01-15/results/

# Keep notes
echo "Tested compression levels 95-20" > experiments/2024-01-15/notes.txt
```

### Error Recovery

If the pipeline fails:
```bash
# Results are saved incrementally, so:
# 1. Check what completed: ls -lh data/ results/
# 2. Resume from failed phase (edit main.py if needed)
# 3. Or re-run just that component
```

### Version Control

```bash
# Commit experiment configs (without secrets!)
git add config/config.example.yaml
git add experiments/2024-01-15/notes.txt
git commit -m "Document experiment configuration for Jan 15 test"
```

---

## Quick Reference Commands

```bash
# Full pipeline
python src/main.py --config config/config.yaml

# Individual components
python src/generators/image_generator.py --project-id PROJECT --prompt "test" --count 1
python src/transformers/image_transformer.py --input data/generated --output data/transformed
python src/detectors/synthid_detector.py --project-id PROJECT --input data/transformed --credentials config/credentials.json
python src/utils/results_analyzer.py --baseline B.json --transformed T.json

# Jupyter analysis
jupyter notebook notebooks/example_usage.ipynb

# Check logs
tail -f results/pipeline.log

# Run tests
pytest tests/ -v
```

---

## Troubleshooting

### Authentication Errors
```bash
# Verify credentials
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

### API Not Enabled
```
Go to GCP Console > APIs & Services > Enable APIs
Enable: Vertex AI API, Cloud AI Platform API
```

### Rate Limits
```
Reduce batch_size in config.yaml
Add delays between requests
Request quota increase in GCP Console
```

### Out of Memory
```
Process fewer images at once
Reduce image resolution in config
Close other applications
```

### Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## Timeline for a Complete Research Project

- **Week 1:** Setup, testing, small-scale experiments
- **Week 2:** Run full-scale experiments, collect data
- **Week 3:** Analysis, visualization, findings documentation
- **Week 4:** Prepare and submit responsible disclosure report

---

## Success Checklist

- [ ] GCP account created and configured
- [ ] APIs enabled and credentials obtained
- [ ] Virtual environment created and dependencies installed
- [ ] Configuration files set up with real credentials (not committed!)
- [ ] Individual components tested successfully
- [ ] Small-scale pipeline run completed
- [ ] Results analyzed and visualized
- [ ] Full-scale experiment planned
- [ ] Data organized and documented
- [ ] Findings compiled for disclosure
- [ ] Report submitted to Google VRP

---

Good luck with your research! Remember: the goal is to help improve SynthID's robustness through responsible security research.
