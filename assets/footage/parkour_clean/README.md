# Parkour Clean — Loop Footage Library

Clean first-person / smooth-tracking parkour and movement loops for Brainrot
Shorts (the "running across rooftops while a story plays" subgenre). Continuous
forward motion, no logos, no commentary.

## How to Add Loops

1. Download CC0 / royalty-free vertical (9:16) or crop-to-vertical video clips
   from one of the sources below.
2. Rename files descriptively: `rooftop_run_01.mp4`, `freerun_alley_02.mp4`.
3. Drop the .mp4 files directly into this folder (`assets/footage/parkour_clean/`).
4. Restart the worker container so the footage library rescans:
   `docker compose restart worker`

## Recommended Sources

Pixabay Video (search: parkour / freerunning / running pov), Pexels Video
(search: parkour, urban running), Mixkit (Free Stock Video). All clips must be
CC0 or the source's free-for-commercial-use license. Verify the license per clip.

## Clip Recommendations

15–60 second continuous-motion loops. Vertical 1080x1920 preferred. Steady,
smooth camera — avoid extreme shake. No HUD overlays, game UI, watermarks, or
recognisable branded games (keep it license-clean, hence "clean").

## File Requirements

- **Format:** MP4 (H.264) preferred; MOV / WEBM / MKV also accepted
- **Aspect:** 9:16 vertical (1080x1920); will be center-cropped if wider
- **Length:** 15 s minimum (the pipeline asks `pick_loop(bucket, min_seconds)`)
- **Audio:** stripped/ignored — ViralFlux supplies its own music + narration
- **License:** CC0 (public domain) or explicit free-for-commercial-use

## Current Clip Count

```bash
find assets/footage/parkour_clean -name "*.mp4" -o -name "*.mov" -o -name "*.webm" | wc -l
```

A minimum of **5 loops** is recommended so the system can randomise selections
and avoid repetition across consecutive videos.
