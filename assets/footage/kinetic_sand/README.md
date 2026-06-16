# Kinetic Sand — Loop Footage Library

Kinetic-sand cutting / slicing CC0 loops for Brainrot Shorts: crisp blade cuts
through coloured sand, crumble, and reshape. Classic ASMR-satisfying texture.

## How to Add Loops

1. Download CC0 / royalty-free vertical (9:16) or crop-to-vertical video clips
   from one of the sources below.
2. Rename files descriptively: `sand_cut_01.mp4`, `kinetic_slice_02.mp4`.
3. Drop the .mp4 files directly into this folder (`assets/footage/kinetic_sand/`).
4. Restart the worker container so the footage library rescans:
   `docker compose restart worker`

## Recommended Sources

Pixabay Video (search: kinetic sand / sand cutting), Pexels Video
(search: kinetic sand, asmr sand), Mixkit (Free Stock Video). All clips must be
CC0 or the source's free-for-commercial-use license. Verify the license per clip.

## Clip Recommendations

15–60 second loops. Vertical 1080x1920 preferred. Close-up, steady framing of
the cuts works best. No on-screen watermarks, channel logos, or text overlays.
Smooth, repetitive motion keeps it calm behind narration + captions.

## File Requirements

- **Format:** MP4 (H.264) preferred; MOV / WEBM / MKV also accepted
- **Aspect:** 9:16 vertical (1080x1920); will be center-cropped if wider
- **Length:** 15 s minimum (the pipeline asks `pick_loop(bucket, min_seconds)`)
- **Audio:** stripped/ignored — ViralFlux supplies its own music + narration
- **License:** CC0 (public domain) or explicit free-for-commercial-use

## Current Clip Count

```bash
find assets/footage/kinetic_sand -name "*.mp4" -o -name "*.mov" -o -name "*.webm" | wc -l
```

A minimum of **5 loops** is recommended so the system can randomise selections
and avoid repetition across consecutive videos.
