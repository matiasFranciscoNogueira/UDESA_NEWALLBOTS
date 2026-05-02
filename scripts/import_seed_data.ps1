# import_seed_data.ps1
# Importa los archivos de seeds/ al volumen Docker y levanta el stack.
# Correr desde la raiz del proyecto: .\scripts\import_seed_data.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$SeedDir = Join-Path $ProjectRoot "seeds"
$Volume = "all-bots_epu_data"

Write-Host ""
Write-Host "=== EPU - Importacion de datos al volumen ===" -ForegroundColor Cyan
Write-Host ""

# Verificar que existe la carpeta seeds/
if (-not (Test-Path $SeedDir)) {
    Write-Host "ERROR: No existe la carpeta 'seeds\'." -ForegroundColor Red
    Write-Host "Descarga los archivos de Google Drive y ponelos en: $SeedDir"
    exit 1
}

# Bajar el stack (preserva el volumen)
Write-Host "Bajando el stack..." -ForegroundColor Yellow
Set-Location $ProjectRoot
docker compose down
Write-Host "  OK" -ForegroundColor Green

# Crear directorio subcategories en el volumen
Write-Host "Preparando volumen..."
docker run --rm -v "${Volume}:/data" alpine mkdir -p /data/subcategories
Write-Host "  OK" -ForegroundColor Green

# Funcion helper para copiar un archivo al volumen
function Copy-ToVolume {
    param(
        [string]$LocalFile,
        [string]$DestPath
    )
    $filename = Split-Path $LocalFile -Leaf
    $folder = Split-Path $LocalFile -Parent
    Write-Host "  Copiando $filename..."
    docker run --rm `
        -v "${Volume}:/dst" `
        -v "${folder}:/src" `
        alpine cp "/src/$filename" "$DestPath"
}

# CSV principal
$MainCsv = Join-Path $SeedDir "epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv"
Write-Host "Importando CSV principal (~455MB)..."
if (Test-Path $MainCsv) {
    Copy-ToVolume $MainCsv "/dst/"
    Write-Host "  OK" -ForegroundColor Green
} else {
    Write-Host "  AVISO: No se encontro el CSV principal en seeds\." -ForegroundColor Yellow
}

# Benchmark Excel
$BenchmarkXlsx = Join-Path $SeedDir "EPU_All_benchmark_ghirelli.xlsx"
Write-Host "Importando benchmark Excel..."
if (Test-Path $BenchmarkXlsx) {
    Copy-ToVolume $BenchmarkXlsx "/dst/"
    Write-Host "  OK" -ForegroundColor Green
} else {
    Write-Host "  AVISO: No se encontro EPU_All_benchmark_ghirelli.xlsx en seeds\." -ForegroundColor Yellow
}

# Subcategorias
$SubcatDir = Join-Path $SeedDir "subcategories"
Write-Host "Importando subcategorias..."
if (Test-Path $SubcatDir) {
    $csvFiles = Get-ChildItem $SubcatDir -Filter "*.csv"
    if ($csvFiles.Count -eq 0) {
        Write-Host "  AVISO: La carpeta subcategories\ esta vacia." -ForegroundColor Yellow
    }
    foreach ($file in $csvFiles) {
        Write-Host "  Copiando $($file.Name)..."
        docker run --rm `
            -v "${Volume}:/dst" `
            -v "${SubcatDir}:/src" `
            alpine cp "/src/$($file.Name)" "/dst/subcategories/"
    }
    Write-Host "  OK ($($csvFiles.Count) archivos)" -ForegroundColor Green
} else {
    Write-Host "  AVISO: No existe seeds\subcategories\." -ForegroundColor Yellow
}

# Verificar contenido del volumen
Write-Host ""
Write-Host "=== Contenido del volumen ===" -ForegroundColor Cyan
docker run --rm -v "${Volume}:/data" alpine sh -c "ls -lh /data/ && echo '-- subcategories --' && ls -lh /data/subcategories/"

# Levantar el stack
Write-Host ""
Write-Host "Levantando el stack..." -ForegroundColor Yellow
docker compose up --build -d
Write-Host ""
Write-Host "=== Listo! ===" -ForegroundColor Green
Write-Host "Para ver los logs: docker compose logs epu-arg -f"
