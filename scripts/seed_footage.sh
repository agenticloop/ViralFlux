#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ViralFlux — Footage Library Seed Script
#
# Creates placeholder README files in each footage bucket folder explaining
# what CC0 "satisfying-loop" clips to add and where to source them. Footage is
# the visual backdrop for Brainrot-genre videos (vertical, looping, no audio).
#
# Usage:
#   bash scripts/seed_footage.sh
#
# Safe to run multiple times — it will not overwrite existing README files.
# Mirrors scripts/seed_music.sh.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(cd "${SCRIPT_DIR}/../assets" && pwd)"
FOOTAGE_DIR="${ASSETS_DIR}/footage"

# ANSI colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}ViralFlux — Seeding footage library placeholder READMEs${RESET}"
echo -e "${CYAN}──────────────────────────────────────────────────────${RESET}"

# ─────────────────────────────────────────────────────────────────────────────
# Bucket definitions
# Format: "slug|display_name|description|sources|recommended"
# Buckets match the curated CC0 satisfying-loop set used by the Brainrot genre.
# ─────────────────────────────────────────────────────────────────────────────

declare -a BUCKETS=(
  "satisfying|Satisfying|Catch-all bucket of generic satisfying loops (soap cutting, paint mixing, slime, foam, glass polishing). The default Brainrot backdrop.|Pixabay Video (search: satisfying), Pexels Videos (search: satisfying loop), Mixkit (Satisfying / Abstract categories). All CC0 / Pexels & Mixkit free license.|Vertical 1080x1920 preferred (or center-croppable 16:9). 10–30s seamless loops. No on-screen text, no logos, no audio. Bright, high-contrast, hypnotic motion that reads on a phone."
  "parkour_clean|Parkour (Clean)|First-person / smooth parkour and movement runs used as fast-paced motion under narration. \"Clean\" = no HUD, no watermark, no game UI.|Pixabay Video (search: parkour, free running), Pexels Videos (search: parkour, rooftop run), Mixkit (Sports / Action). CC0 / free license only.|Vertical or center-croppable. 15–30s continuous motion. Steady forward momentum, no jarring cuts. Must be free of game HUD, kill-feeds, or copyrighted gameplay overlays."
  "hydraulic|Hydraulic Press|Hydraulic-press crush clips — objects being flattened. Classic high-retention satisfying/destruction loops.|Pixabay Video (search: hydraulic press, crush), Pexels Videos (search: press crush), Mixkit (Abstract / Industrial). CC0 / free license only.|Vertical or croppable. 8–20s. Single clean crush per clip, centered subject. No commentary audio, no channel branding burned in."
  "kinetic_sand|Kinetic Sand|Kinetic-sand cutting, slicing and crumbling loops. Soft, tactile, ASMR-style satisfying motion.|Pixabay Video (search: kinetic sand), Pexels Videos (search: sand cutting), Mixkit (Abstract / Macro). CC0 / free license only.|Vertical or croppable, macro framing. 10–25s seamless. Even lighting, saturated colors. No hands-with-tattoos/logos in frame if avoidable, no audio."
)

# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

created=0
skipped=0

for entry in "${BUCKETS[@]}"; do
  IFS='|' read -r slug display_name description sources recommended <<< "${entry}"

  bucket_dir="${FOOTAGE_DIR}/${slug}"
  readme_path="${bucket_dir}/README.md"

  # Create directory if it does not exist
  mkdir -p "${bucket_dir}"

  if [[ -f "${readme_path}" ]]; then
    echo -e "  ${YELLOW}SKIP${RESET}  ${slug}/ — README already exists"
    ((skipped++)) || true
    continue
  fi

  # Write placeholder README
  cat > "${readme_path}" << HEREDOC
# ${display_name} — Footage Bucket

${description}

## How to Add Clips

1. Download royalty-free .mp4 clips from one of the CC0 sources listed below.
2. Rename files to something descriptive: \`${slug}_loop_01.mp4\`, \`${slug}_02.mp4\`, etc.
3. Drop the .mp4 files directly into this folder (\`assets/footage/${slug}/\`).
4. Restart the worker container so the footage library service rescans: \`docker compose restart worker\`

## Recommended CC0 Sources

${sources}

## Clip Recommendations

${recommended}

## File Requirements

- **Format:** MP4 (H.264) preferred
- **Aspect:** 9:16 vertical (1080x1920) ideal; 16:9 acceptable if center-croppable
- **Length:** 8–30s, seamlessly loopable
- **Audio:** none required — ViralFlux strips clip audio and mixes its own music + narration
- **License:** CC0 (public domain) or the Pexels / Mixkit free license. No copyrighted gameplay or branded footage.

## Current Clip Count

Run this command from the project root to see how many clips are in this bucket:

\`\`\`bash
find assets/footage/${slug} -name "*.mp4" | wc -l
\`\`\`

A minimum of **5 clips** per bucket is recommended so the system can randomize
selections and avoid repetition across consecutive videos.
HEREDOC

  echo -e "  ${GREEN}CREATE${RESET} ${slug}/README.md"
  ((created++)) || true

done

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}──────────────────────────────────────────────────────${RESET}"
echo -e "${GREEN}Done.${RESET} Created: ${created}  Skipped: ${skipped}"
echo ""
echo -e "Footage library is at: ${FOOTAGE_DIR}"
echo -e "Add .mp4 files to each bucket folder, then run:"
echo -e "  ${CYAN}docker compose restart worker${RESET}"
echo ""
echo -e "Bucket folders:"
for entry in "${BUCKETS[@]}"; do
  IFS='|' read -r slug display_name _ <<< "${entry}"
  clip_count=$(find "${FOOTAGE_DIR}/${slug}" -name "*.mp4" 2>/dev/null | wc -l)
  echo -e "  ${slug}/  (${clip_count} clips)"
done
