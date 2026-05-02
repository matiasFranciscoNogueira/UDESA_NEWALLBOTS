#!/bin/bash
# export_seed_data.sh
# Exporta los archivos de datos del volumen Docker a la carpeta seeds/.
# Correr desde cualquier lugar: bash scripts/export_seed_data.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEED_DIR="$PROJECT_ROOT/seeds"

echo "=== EPU — Exportación de datos para seed ==="
echo ""

# Detectar volumen con los datos
VOLUME=""
for vol in all-bots_epu_data udesa_epu_data; do
    if docker volume ls --format '{{.Name}}' | grep -qx "$vol"; then
        if docker run --rm -v "$vol":/data alpine test -f "/data/epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv" 2>/dev/null; then
            VOLUME="$vol"
            echo "Volumen encontrado: $vol"
            break
        fi
    fi
done

if [ -z "$VOLUME" ]; then
    echo "ERROR: No se encontró ningún volumen con el CSV principal del EPU."
    echo "Volúmenes disponibles:"
    docker volume ls
    exit 1
fi

mkdir -p "$SEED_DIR"
mkdir -p "$SEED_DIR/subcategories"

# CSV principal
FILE="epu_argentina_key_words_gdelt_maped_jp_maped_all_media_with_sentiment.csv"
echo "Exportando CSV principal (~455MB)..."
docker run --rm \
    -v "$VOLUME":/data \
    -v "$SEED_DIR":/out \
    alpine cp "/data/$FILE" "/out/$FILE"
echo "  ✓ $FILE"

# Benchmark Excel
FILE="EPU_All_benchmark_ghirelli.xlsx"
echo "Exportando benchmark Excel..."
docker run --rm \
    -v "$VOLUME":/data \
    -v "$SEED_DIR":/out \
    alpine cp "/data/$FILE" "/out/$FILE"
echo "  ✓ $FILE"

# Subcategorías
echo "Exportando subcategorías..."
SUBCATS=("trade" "fiscal" "monetary_policy" "currency_crisis")
for subcat in "${SUBCATS[@]}"; do
    FILE="epu_argentina_key_words_gdelt_maped_jp_${subcat}_maped_all_media_with_sentiment.csv"
    if docker run --rm -v "$VOLUME":/data alpine test -f "/data/subcategories/$FILE" 2>/dev/null; then
        docker run --rm \
            -v "$VOLUME":/data \
            -v "$SEED_DIR/subcategories":/out \
            alpine cp "/data/subcategories/$FILE" "/out/$FILE"
        echo "  ✓ $FILE"
    else
        echo "  ⚠ No encontrado: $subcat (se omite)"
    fi
done

echo ""
echo "=== Exportación completada ==="
echo ""
ls -lh "$SEED_DIR/"
if [ "$(ls -A "$SEED_DIR/subcategories")" ]; then
    echo "subcategories/"
    ls -lh "$SEED_DIR/subcategories/"
fi
echo ""
echo "Próximo paso: subí la carpeta seeds/ a Google Drive y"
echo "en Windows corré: scripts\import_seed_data.ps1"
