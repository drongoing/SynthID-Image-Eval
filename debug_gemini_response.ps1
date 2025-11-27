# debug_gemini_response.ps1
# Debug script to inspect Gemini 3 API response structure

Write-Host "=== Gemini 3 Response Debugger ===" -ForegroundColor Green
Write-Host ""

# Load .env
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$apiKey = $env:GEMINI_API_KEY

if (-not $apiKey) {
    Write-Host "Error: GEMINI_API_KEY not set" -ForegroundColor Red
    exit 1
}

Write-Host "Testing Gemini 3 API response format..." -ForegroundColor Yellow
Write-Host ""

# Create debug script
$debugScript = @"
import os
import google.generativeai as genai

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

print("=== Testing Gemini 3 Pro Image Preview ===")
print()

try:
    model = genai.GenerativeModel("gemini-3-pro-image-preview")
    print("✅ Model loaded successfully")
    print()

    # Try to generate
    prompt = "Generate an image: A simple red circle"
    print(f"Prompt: {prompt}")
    print()

    response = model.generate_content(prompt)

    print("=== Response Structure ===")
    print(f"Response type: {type(response)}")
    print(f"Has 'text' attr: {hasattr(response, 'text')}")
    print(f"Has 'image' attr: {hasattr(response, 'image')}")
    print(f"Has 'parts' attr: {hasattr(response, 'parts')}")
    print(f"Has 'candidates' attr: {hasattr(response, 'candidates')}")
    print()

    if hasattr(response, 'text'):
        print(f"Response text: {response.text[:200]}")
        print()

    if hasattr(response, 'parts'):
        print(f"Number of parts: {len(list(response.parts))}")
        for i, part in enumerate(response.parts):
            print(f"  Part {i}:")
            print(f"    Type: {type(part)}")
            print(f"    Has 'inline_data': {hasattr(part, 'inline_data')}")
            print(f"    Has 'text': {hasattr(part, 'text')}")
            print(f"    Has 'mime_type': {hasattr(part, 'mime_type')}")
            if hasattr(part, 'inline_data'):
                print(f"    inline_data type: {type(part.inline_data)}")
                print(f"    inline_data.data length: {len(part.inline_data.data) if hasattr(part.inline_data, 'data') else 'N/A'}")
                print(f"    inline_data.mime_type: {part.inline_data.mime_type if hasattr(part.inline_data, 'mime_type') else 'N/A'}")
        print()

    if hasattr(response, 'candidates'):
        print(f"Number of candidates: {len(response.candidates)}")
        for i, candidate in enumerate(response.candidates):
            print(f"  Candidate {i}:")
            print(f"    Type: {type(candidate)}")
            print(f"    Has 'content': {hasattr(candidate, 'content')}")
            if hasattr(candidate, 'content'):
                content = candidate.content
                print(f"    Content type: {type(content)}")
                print(f"    Content has 'parts': {hasattr(content, 'parts')}")
                if hasattr(content, 'parts'):
                    for j, part in enumerate(content.parts):
                        print(f"      Part {j}: {type(part)}")
                        if hasattr(part, 'inline_data'):
                            print(f"        Has inline_data")
        print()

    # Print full response for inspection
    print("=== Full Response (str) ===")
    print(str(response)[:500])

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

"@

$debugScript | Out-File -FilePath debug_gemini.py -Encoding UTF8

Write-Host "Running debug script..." -ForegroundColor Cyan
python debug_gemini.py

Write-Host ""
Write-Host "=== Debug Complete ===" -ForegroundColor Green
