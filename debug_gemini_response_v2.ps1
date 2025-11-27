# debug_gemini_response_v2.ps1
# Better debug script to see the exact inline_data structure

Write-Host "=== Gemini 3 Inline Data Inspector ===" -ForegroundColor Green

# Load .env
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$debugScript = @"
import os
import google.generativeai as genai
from PIL import Image
import io

api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

model = genai.GenerativeModel("gemini-3-pro-image-preview")
prompt = "Generate an image: A simple red circle"

print("Generating...")
response = model.generate_content(prompt)

print("\n=== Response Analysis ===")
print(f"Response type: {type(response)}")
print(f"Has candidates: {hasattr(response, 'candidates')}")

if hasattr(response, 'candidates') and response.candidates:
    candidate = response.candidates[0]
    print(f"\nCandidate type: {type(candidate)}")

    if hasattr(candidate, 'content'):
        content = candidate.content
        print(f"Content type: {type(content)}")
        print(f"Content has parts: {hasattr(content, 'parts')}")

        if hasattr(content, 'parts'):
            print(f"Number of parts: {len(content.parts)}")

            for i, part in enumerate(content.parts):
                print(f"\n--- Part {i} ---")
                print(f"Part type: {type(part)}")
                print(f"Has inline_data: {hasattr(part, 'inline_data')}")
                print(f"Has text: {hasattr(part, 'text')}")

                if hasattr(part, 'inline_data'):
                    inline = part.inline_data
                    print(f"  inline_data type: {type(inline)}")
                    print(f"  Has data: {hasattr(inline, 'data')}")
                    print(f"  Has mime_type: {hasattr(inline, 'mime_type')}")

                    if hasattr(inline, 'mime_type'):
                        print(f"  mime_type: {inline.mime_type}")

                    if hasattr(inline, 'data'):
                        data = inline.data
                        print(f"  data type: {type(data)}")
                        print(f"  data length: {len(data)} bytes")

                        # Try to open as image directly
                        try:
                            # Data might already be bytes, not base64
                            print("\n  Attempting to open as raw bytes...")
                            img = Image.open(io.BytesIO(data))
                            print(f"  ✅ SUCCESS! Image size: {img.size}, mode: {img.mode}")

                            # Save test image
                            test_path = "test_gemini_output.png"
                            img.save(test_path)
                            print(f"  ✅ Saved test image to: {test_path}")

                        except Exception as e1:
                            print(f"  ❌ Failed as raw bytes: {e1}")

                            # Try base64 decode
                            try:
                                print("\n  Attempting base64 decode...")
                                import base64
                                decoded = base64.b64decode(data)
                                img = Image.open(io.BytesIO(decoded))
                                print(f"  ✅ SUCCESS with base64! Image size: {img.size}")

                                test_path = "test_gemini_output.png"
                                img.save(test_path)
                                print(f"  ✅ Saved test image to: {test_path}")

                            except Exception as e2:
                                print(f"  ❌ Failed with base64: {e2}")

                                # Show first few bytes
                                print(f"\n  First 20 bytes: {data[:20]}")

"@

$debugScript | Out-File -FilePath debug_gemini_v2.py -Encoding UTF8
python debug_gemini_v2.py

Write-Host "`n=== Check for test image ===" -ForegroundColor Yellow
if (Test-Path test_gemini_output.png) {
    $file = Get-Item test_gemini_output.png
    Write-Host "✅ Test image created: $($file.Length) bytes" -ForegroundColor Green
    Write-Host "Opening image..." -ForegroundColor Cyan
    start test_gemini_output.png
} else {
    Write-Host "❌ No test image created" -ForegroundColor Red
}
