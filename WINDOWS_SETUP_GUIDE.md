# Windows Setup & Testing Guide

Quick guide for running SynthID-Image-Eval on Windows with PowerShell.

## Prerequisites Checklist

- [ ] Python 3.8+ installed (`python --version`)
- [ ] Git installed
- [ ] Google Cloud Project ID
- [ ] Gemini API Key from https://ai.google.dev/

## Quick Setup (5 minutes)

### 1. Navigate to Your Repository

```powershell
cd C:\Users\vibhu\Learn\SynthID-Image-Eval
```

### 2. Create Virtual Environment

```powershell
# Create venv
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run this once:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

You should see `(venv)` at the start of your prompt.

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Create .env File

```powershell
# Copy template
Copy-Item .env.example .env

# Edit with notepad
notepad .env
```

Add your credentials:
```
GOOGLE_CLOUD_PROJECT=your-actual-project-id
GEMINI_API_KEY=your-actual-gemini-api-key
IMAGE_GENERATION_MODEL=gemini-3-pro-image-preview
DETECTION_MODEL=gemini-3-pro-preview
```

**IMPORTANT:** Use your real values, not the placeholders!

### 5. Create config.yaml

```powershell
# Copy template
Copy-Item config\config.example.yaml config\config.yaml

# Edit with notepad
notepad config\config.yaml
```

Update these sections:
```yaml
google_cloud:
  project_id: "your-actual-project-id"

api_keys:
  gemini_api_key: "your-actual-api-key"

generation:
  model: "gemini-3-pro-image-preview"

detection:
  model: "gemini-3-pro-preview"
```

## Run Test Image Generation

### Option 1: Automated Test Script (Recommended)

```powershell
.\test_image_generation.ps1
```

This script will:
- ✅ Check your virtual environment
- ✅ Load .env variables
- ✅ Verify credentials
- ✅ Generate a test image
- ✅ Show you the results

### Option 2: Manual Test

```powershell
# Load .env file manually
Get-Content .env | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
}

# Run generation
python src/generators/image_generator.py `
  --project-id $env:GOOGLE_CLOUD_PROJECT `
  --model gemini-3-pro-image-preview `
  --prompt "A test image of a sunset" `
  --count 1 `
  --output-dir data/generated

# Check output
Get-ChildItem data\generated
```

## Troubleshooting

### "Virtual environment not activated"
```powershell
.\venv\Scripts\Activate.ps1
```

### "Execution policy error"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "GEMINI_API_KEY not set"
- Check your .env file exists
- Make sure you added your real API key (not the placeholder)
- Reload environment variables or restart PowerShell

### "Failed to load Gemini model"
- Verify your API key is correct
- Check you have access to Gemini 3 models at https://ai.google.dev/
- Try using `gemini-1.5-pro` instead if Gemini 3 isn't available

### "Module not found"
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### "No images generated but no error"
- Check `data\generated` folder
- Check the metadata JSON file for errors
- Look at the console output for warnings

## Expected Results

After successful generation:

```
✅ Virtual environment is activated
✅ .env file found
✅ Project ID: your-project-id
✅ Gemini API Key: AIzaSy...
✅ Created data\generated directory
Generating 1 images for prompt: 'A test image of a sunset'
Saved generated image to data\generated\20251127_120000_A_test_image_of_a_sunset_0.png
✅ Image generation completed successfully!
✅ Found generated image(s):
  - 20251127_120000_A_test_image_of_a_sunset_0.png (245 KB, 11/27/2025 12:00:00 PM)
```

## Next Steps

Once image generation works:

1. **Test Transformation**
   ```powershell
   python src/transformers/image_transformer.py `
     --input data/generated `
     --output data/transformed
   ```

2. **Test Detection**
   ```powershell
   python src/detectors/synthid_detector.py `
     --api-key $env:GEMINI_API_KEY `
     --input data/generated `
     --output results/test
   ```

3. **Run Full Pipeline**
   ```powershell
   python src/main.py --config config/config.yaml
   ```

## Quick Reference Commands

```powershell
# Activate venv
.\venv\Scripts\Activate.ps1

# Check files
Get-ChildItem data\generated
Get-ChildItem data\transformed
Get-ChildItem results

# View logs
Get-Content results\pipeline.log -Tail 20

# Open results
start results\report_*.html

# List Python packages
pip list

# Check environment variables
$env:GEMINI_API_KEY
$env:GOOGLE_CLOUD_PROJECT
```

## Getting Help

If you're still stuck:

1. Check the full [EXECUTION_PLAN.md](EXECUTION_PLAN.md)
2. See [GEMINI3_CONFIG.md](GEMINI3_CONFIG.md) for Gemini 3 specific setup
3. Review [QUICKSTART.md](QUICKSTART.md)
4. Check Python version: `python --version` (need 3.8+)
5. Check if packages installed: `pip list | Select-String google`

## Common Commands for Debugging

```powershell
# Check Python environment
python --version
Get-Command python | Select-Object Source

# Verify imports
python -c "import google.generativeai; print('OK')"

# Test config loading
python test_config.py

# Check file structure
tree /F src
```
