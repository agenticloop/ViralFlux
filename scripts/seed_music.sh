#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# ViralFlux — Music Library Seed Script
#
# Creates placeholder README files in each music category folder explaining
# what tracks to add and where to source them.
#
# Usage:
#   bash scripts/seed_music.sh
#
# This script is safe to run multiple times — it will not overwrite existing
# README files if they are already present.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$(cd "${SCRIPT_DIR}/../assets" && pwd)"
MUSIC_DIR="${ASSETS_DIR}/music"

# ANSI colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${CYAN}ViralFlux — Seeding music library placeholder READMEs${RESET}"
echo -e "${CYAN}─────────────────────────────────────────────────────${RESET}"

# ─────────────────────────────────────────────────────────────────────────────
# Category definitions
# Format: "slug|display_name|description|sources|recommended"
# ─────────────────────────────────────────────────────────────────────────────

declare -a CATEGORIES=(
  "horror_ambient|Horror Ambient|Dark, atmospheric, slow-building tracks for Horror Story Shorts.|YouTube Audio Library (filter: Dark → Ambient), Pixabay Music (search: horror ambient), Freesound.org (CC0 license).|2–5 minute loops. Slow tempo (60–80 BPM). No sudden loud peaks that would overpower narration. Examples: deep drones, reverb-heavy piano, distant wind."
  "upbeat_hype|Upbeat Hype|Energetic, punchy tracks for Ranking and Listicle format videos.|YouTube Audio Library (filter: Upbeat → Electronic/Hip-Hop), Pixabay Music (search: upbeat hype), Bensound (free tier).|45–90 seconds or loops. Fast tempo (120–145 BPM). Heavy bass, trap beats, or electronic drops. Should feel exciting but not overwhelming."
  "cinematic_epic|Cinematic Epic|Grand, sweeping orchestral tracks for Motivational and Stoic format videos.|YouTube Audio Library (filter: Cinematic → Epic), Pixabay Music (search: cinematic epic), Freesound.org (CC0 license).|60–180 seconds or loops. Mid tempo with build (80–110 BPM). Full orchestral arrangement. Rising strings, percussion hits. Should feel inspiring and powerful."
  "lo_fi_chill|Lo-Fi Chill|Mellow, laid-back beats for informational or conversational formats.|YouTube Audio Library (filter: Hip Hop/Rap → Lo-Fi), Lofi Girl (YouTube channel, free for creators), Pixabay Music (search: lofi chill).|1–3 minute loops. Slow tempo (70–90 BPM). Jazzy chords, vinyl crackle, soft beats. Good for educational or talking-head style content."
  "horror_tense|Horror Tense|High-tension, suspenseful tracks for climactic moments in horror content.|YouTube Audio Library (filter: Dark → Tense), Freesound.org (search: suspense sting), Pixabay Music (search: horror tense).|30–90 seconds. Builds in intensity. Dissonant strings, staccato, sudden silences. Use for short format segments or as transition stingers."
)

# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────

created=0
skipped=0

for entry in "${CATEGORIES[@]}"; do
  IFS='|' read -r slug display_name description sources recommended <<< "${entry}"

  category_dir="${MUSIC_DIR}/${slug}"
  readme_path="${category_dir}/README.md"

  # Create directory if it does not exist
  mkdir -p "${category_dir}"

  if [[ -f "${readme_path}" ]]; then
    echo -e "  ${YELLOW}SKIP${RESET}  ${slug}/ — README already exists"
    ((skipped++)) || true
    continue
  fi

  # Write placeholder README
  cat > "${readme_path}" << HEREDOC
# ${display_name} — Music Library

${description}

## How to Add Tracks

1. Download royalty-free .mp3 files from one of the sources listed below.
2. Rename files to something descriptive: \`dark_drone_loop_01.mp3\`, \`tense_strings_02.mp3\`, etc.
3. Drop the .mp3 files directly into this folder (\`assets/music/${slug}/\`).
4. Restart the worker container so the music library service rescans: \`docker compose restart worker\`

## Recommended Sources

${sources}

## Track Recommendations

${recommended}

## File Requirements

- **Format:** MP3 (preferred) or WAV
- **Sample rate:** 44,100 Hz
- **Bitrate:** 128 kbps minimum, 320 kbps preferred
- **Length:** See category description above
- **License:** CC0 (public domain) or YouTube Audio Library (free for YouTube use)
- **No stems required** — ViralFlux mixes the track at 15% volume under narration

## Current Track Count

Run this command from the project root to see how many tracks are in this category:

\`\`\`bash
find assets/music/${slug} -name "*.mp3" -o -name "*.wav" | wc -l
\`\`\`

A minimum of **5 tracks** per category is recommended so the system can randomize
selections and avoid repetition across consecutive videos.
HEREDOC

  echo -e "  ${GREEN}CREATE${RESET} ${slug}/README.md"
  ((created++)) || true

done

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${CYAN}─────────────────────────────────────────────────────${RESET}"
echo -e "${GREEN}Done.${RESET} Created: ${created}  Skipped: ${skipped}"
echo ""
echo -e "Music library is at: ${MUSIC_DIR}"
echo -e "Add .mp3 files to each category folder, then run:"
echo -e "  ${CYAN}docker compose restart worker${RESET}"
echo ""
echo -e "Category folders:"
for entry in "${CATEGORIES[@]}"; do
  IFS='|' read -r slug display_name _ <<< "${entry}"
  track_count=$(find "${MUSIC_DIR}/${slug}" -name "*.mp3" -o -name "*.wav" 2>/dev/null | wc -l)
  echo -e "  ${slug}/  (${track_count} tracks)"
done
