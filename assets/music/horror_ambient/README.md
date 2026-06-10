# Horror Ambient — Music Library

Add royalty-free horror ambient .mp3 files here. Sources: YouTube Audio Library, Pixabay Music (CC0). Recommended: dark, atmospheric, 2-5 minute loops.

## What to Look For

Tracks in this category are played at **15% volume** underneath the narration voice. They should create atmosphere without competing with the script.

Good characteristics:
- Deep drones and sub-bass rumble
- Reverb-heavy piano or strings
- Distant wind, rain, or environmental textures
- Slow, gradual builds — no sudden loud peaks
- Minor key or atonal — nothing melodic or recognizable
- Length: 2–5 minutes (loops or one-shots both work)
- Tempo: 55–75 BPM (or no discernible beat)

## Recommended Sources

- **YouTube Audio Library** — Filter: Dark > Ambient. All tracks are free for YouTube use.
  https://studio.youtube.com/channel/music
- **Pixabay Music** — Search: "horror ambient", "dark atmosphere", "creepy ambient". All CC0.
  https://pixabay.com/music/
- **Freesound.org** — Search: "horror ambient loop", "dark drone". Filter for CC0 license.
  https://freesound.org/
- **Incompetech (Kevin MacLeod)** — Horror section, CC-BY license (credit required in description).
  https://incompetech.filmmusic.io/

## File Requirements

- **Format:** MP3 (128 kbps minimum, 320 kbps preferred) or WAV
- **Filename convention:** Use descriptive names, e.g., `dark_hallway_drone_01.mp3`
- **No stems or split tracks** — single mixed file only

## How to Add

1. Download files from the sources above
2. Drop the .mp3 files into this folder
3. Restart the worker: `docker compose restart worker`

The music library service will automatically discover all `.mp3` and `.wav` files in this directory and make them available for video generation.

## Minimum Recommended: 5 tracks
