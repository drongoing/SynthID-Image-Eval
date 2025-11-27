# test_image_generation.ps1
# PowerShell script to test image generation for SynthID-Image-Eval

Write-Host "=== SynthID Image Generation Test ===" -ForegroundColor Green
Write-Host ""

# Step 1: Check if virtual environment is activated
Write-Host "Step 1: Checking virtual environment..." -ForegroundColor Yellow
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Virtual environment is activated: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Red
    Write-Host "Run: .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "Press Enter to continue anyway, or Ctrl+C to exit..."
    Read-Host
}

# Step 2: Check .env file exists
Write-Host "`nStep 2: Checking .env file..." -ForegroundColor Yellow
if (Test-Path .env) {
    Write-Host "✅ .env file found" -ForegroundColor Green

    # Load .env file
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Host "✅ Environment variables loaded from .env" -ForegroundColor Green
} else {
    Write-Host "❌ .env file not found!" -ForegroundColor Red
    Write-Host "Create .env file first with:" -ForegroundColor Cyan
    Write-Host "  GOOGLE_CLOUD_PROJECT=your-project-id" -ForegroundColor Cyan
    Write-Host "  GEMINI_API_KEY=your-api-key" -ForegroundColor Cyan
    exit 1
}

# Step 3: Check required environment variables
Write-Host "`nStep 3: Checking required credentials..." -ForegroundColor Yellow
$projectId = $env:GOOGLE_CLOUD_PROJECT
$apiKey = $env:GEMINI_API_KEY

if (-not $projectId) {
    Write-Host "❌ GOOGLE_CLOUD_PROJECT not set!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Project ID: $projectId" -ForegroundColor Green

if (-not $apiKey) {
    Write-Host "❌ GEMINI_API_KEY not set!" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Gemini API Key: $(if($apiKey.Length -gt 10) { $apiKey.Substring(0,10) + '...' } else { 'Set' })" -ForegroundColor Green

# Step 4: Check data directory exists
Write-Host "`nStep 4: Ensuring data directory exists..." -ForegroundColor Yellow
if (-not (Test-Path data\generated)) {
    New-Item -ItemType Directory -Path data\generated -Force | Out-Null
    Write-Host "✅ Created data\generated directory" -ForegroundColor Green
} else {
    Write-Host "✅ data\generated directory exists" -ForegroundColor Green
}

# Step 5: Run image generation
Write-Host "`nStep 5: Generating test image..." -ForegroundColor Yellow
Write-Host "Command: python src/generators/image_generator.py --project-id $projectId --model gemini-3-pro-image-preview --prompt 'A test image of a sunset' --count 1 --output-dir data/generated" -ForegroundColor Cyan

python src/generators/image_generator.py `
  --project-id $projectId `
  --model gemini-3-pro-image-preview `
  --prompt "A test image of a sunset" `
  --count 1 `
  --output-dir data/generated

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Image generation completed successfully!" -ForegroundColor Green

    # Step 6: Check generated files
    Write-Host "`nStep 6: Checking generated files..." -ForegroundColor Yellow
    $files = Get-ChildItem data\generated\*.png | Sort-Object LastWriteTime -Descending | Select-Object -First 5

    if ($files) {
        Write-Host "✅ Found generated image(s):" -ForegroundColor Green
        $files | ForEach-Object {
            Write-Host "  - $($_.Name) ($('{0:N0}' -f ($_.Length/1KB)) KB, $($_.LastWriteTime))" -ForegroundColor Cyan
        }
    } else {
        Write-Host "⚠️  No PNG files found in data\generated" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n❌ Image generation failed with exit code: $LASTEXITCODE" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
