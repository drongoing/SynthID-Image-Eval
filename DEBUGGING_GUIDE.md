# Debugging Guide for Gemini 3 Image Generation

## Current Issue

The Gemini 3 API is responding, but the image extraction is failing. We need to understand the exact response format.

## Step 1: Run Debug Script

```powershell
cd C:\Users\vibhu\Learn\SynthID-Image-Eval
.\debug_gemini_response.ps1
```

This will show us the exact structure of Gemini 3's response.

## Step 2: Share the Output

Copy the entire output and share it. We need to see:
- Response type
- What attributes the response has
- The structure of `parts` or `candidates`
- The format of any image data

## Possible Issues & Solutions

### Issue 1: Gemini 3 Returns Text, Not Images

**Symptom:** Response has `text` but no image data

**Solution:** Gemini 3 Pro Image Preview might not actually generate images directly through `generate_content()`. It might:
- Return a URL to the generated image
- Require a different API endpoint
- Need specific parameters

### Issue 2: Image Data Format Mismatch

**Symptom:** Response has image data but PIL can't read it

**Possible causes:**
- Data is double-encoded (base64 of base64)
- Data needs different decoding
- Mime type mismatch

### Issue 3: Wrong Model Name

**Symptom:** Model loads but behaves unexpectedly

**Check:** Verify `gemini-3-pro-image-preview` is the correct model name for image generation.

**Alternatives to try:**
- `gemini-pro-vision` (older model that handles images)
- `imagen-3` (if Gemini 3 is just for detection)
- `imagegeneration@006` (Vertex AI Imagen 3)

## Manual Testing Commands

### Test 1: Check Available Models

```powershell
python -c "import google.generativeai as genai; import os; genai.configure(api_key=os.getenv('GEMINI_API_KEY')); models = genai.list_models(); print([m.name for m in models if 'image' in m.name.lower() or 'vision' in m.name.lower()])"
```

### Test 2: Try Text Generation (Verify API Works)

```powershell
python -c "import google.generativeai as genai; import os; genai.configure(api_key=os.getenv('GEMINI_API_KEY')); model = genai.GenerativeModel('gemini-1.5-pro'); response = model.generate_content('Say hello'); print(response.text)"
```

### Test 3: Try Vision Model (Send Image to Gemini)

```powershell
# This tests if Gemini can ANALYZE images (not generate them)
python -c "import google.generativeai as genai; import os; from PIL import Image; genai.configure(api_key=os.getenv('GEMINI_API_KEY')); model = genai.GenerativeModel('gemini-1.5-pro'); img = Image.new('RGB', (100, 100), 'red'); response = model.generate_content(['What color is this?', img]); print(response.text)"
```

## Quick Fix: Use Vertex AI Imagen Instead

If Gemini 3 image generation isn't working as expected, we can switch to Vertex AI's Imagen 3:

### Update .env:
```bash
IMAGE_GENERATION_MODEL=imagegeneration@006
```

### Update config.yaml:
```yaml
generation:
  model: "imagegeneration@006"  # Use Vertex AI Imagen 3
```

### Install Vertex AI:
```powershell
pip install google-cloud-aiplatform
```

### Set up credentials:
You'll need a service account JSON file from Google Cloud Console:
1. Go to https://console.cloud.google.com/
2. IAM & Admin > Service Accounts
3. Create service account
4. Download JSON key
5. Add to .env:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=C:/path/to/your/service-account-key.json
   ```

## Next Steps

1. Run `.\debug_gemini_response.ps1`
2. Share the output
3. Based on the response structure, I'll update the code to correctly extract images

OR

If Gemini 3 doesn't support image generation:
1. Switch to Vertex AI Imagen (instructions above)
2. Use Gemini 3 only for detection (which it definitely supports)
