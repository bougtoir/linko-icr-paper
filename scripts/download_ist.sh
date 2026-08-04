#!/usr/bin/env bash
# Download the public International Stroke Trial (IST) individual patient data.
# Open access: Sandercock PAG, Niewada M, Czlonkowska A. The International
# Stroke Trial database. Trials 2011;12:101. https://datashare.ed.ac.uk/handle/10283/124
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/data/ist"
mkdir -p "$DIR"
if [ -s "$DIR/IST_corrected.csv" ]; then
  echo "IST data already present: $DIR/IST_corrected.csv"
  exit 0
fi
curl -fsSL -o "$DIR/IST_corrected.csv" \
  "https://datashare.ed.ac.uk/bitstream/handle/10283/124/IST_corrected.csv"
echo "Saved $DIR/IST_corrected.csv"
