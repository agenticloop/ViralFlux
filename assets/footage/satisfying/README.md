# Satisfying — Loop Footage Library

Oddly-satisfying CC0 background loops for Brainrot Shorts: slime, soap cutting,
paint mixing, glossy spheres, ASMR cleaning. Calm, mesmerising, no hard cuts.

## How to Add Loops

1. Download CC0 / royalty-free vertical (9:16) or crop-to-vertical video clips
   from one of the sources below.
2. Rename files descriptively: `slime_press_01.mp4`, `paint_mix_02.mp4`, etc.
3. Drop the .mp4 files directly into this folder (`assets/footage/satisfying/`).
4. Restart the worker container so the footage library rescans:
   `docker compose restart worker`

## Recommended Sources

Pixabay Video (search: satisfying / slime / asmr), Pexels Video
(search: satisfying loops), Mixkit (Free Stock Video). All clips must be CC0 or
the source's free-for-commercial-use license. Verify the license per clip.

## Clip Recommendations

15–60 second seamless loops. Vertical 1080x1920 preferred (taller crops fine).
No on-screen watermarks, captions, or logos. Smooth, hypnotic motion — avoid
flashing or jarring cuts so it sits quietly behind narration + captions.

## File Requirements

- **Format:** MP4 (H.264) preferred; MOV / WEBM / MKV also accepted
- **Aspect:** 9:16 vertical (1080x1920); will be center-cropped if wider
- **Length:** 15 s minimum (the pipeline asks `pick_loop(bucket, min_seconds)`)
- **Audio:** stripped/ignored — ViralFlux supplies its own music + narration
- **License:** CC0 (public domain) or explicit free-for-commercial-use

## Current Clip Count

```bash
find assets/footage/satisfying -name "*.mp4" -o -name "*.mov" -o -name "*.webm" | wc -l
```

A minimum of **5 loops** is recommended so the system can randomise selections
and avoid repetition across consecutive videos.
