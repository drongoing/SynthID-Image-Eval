# list_available_models.ps1
# List all available Gemini models for your API key

Write-Host "=== Listing Available Gemini Models ===" -ForegroundColor Green

# Load .env
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$listScript = @"
import os
import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("\n=== Available Models ===\n")

try:
    models = list(genai.list_models())

    print(f"Total models: {len(models)}\n")

    # Filter for models that support generateContent (for detection/analysis)
    generation_models = [m for m in models if 'generateContent' in m.supported_generation_methods]

    print("Models that support generateContent (for image analysis/detection):")
    print("-" * 60)
    for model in generation_models:
        print(f"  Name: {model.name}")
        print(f"    Display: {model.display_name if hasattr(model, 'display_name') else 'N/A'}")
        print(f"    Methods: {', '.join(model.supported_generation_methods)}")
        print()

    print("\nRECOMMENDED FOR DETECTION:")
    print("-" * 60)

    # Find the best model for detection
    for model in generation_models:
        if 'vision' in model.name.lower() or 'pro' in model.name.lower():
            # Extract just the model name without 'models/' prefix
            model_id = model.name.replace('models/', '')
            print(f"  ✅ {model_id}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

"@

$listScript | Out-File -FilePath list_models.py -Encoding UTF8
python list_models.py

Write-Host "`n=== Model Listing Complete ===" -ForegroundColor Green
