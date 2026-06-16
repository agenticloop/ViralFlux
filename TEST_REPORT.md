# ViralFlux — Real End-to-End Test & Fix Report

Branch: `feat/viralflux-v2-rearchitecture`
Date: 2026-06-16
Environment: full Docker stack, dev bind-mount override, REAL API keys
(Gemini, ElevenLabs, Imagen, Nano Banana Pro).

All work done against live external providers — no stubs, no faked passes.

---

## Summary

| Phase | Result |
|-------|--------|
| Keyless + gated test suite | **64 passed, 0 failed** (was 63 passed / 1 failed) |
| Real E2E generation matrix | **6 / 6 passed** — all produce valid 1080x1920 MP4s with video + audio |
| Nano Banana Pro smoke test | **PASS** — 1 image, 788 KB, via `generateContent` inline data |

The 3 previously-skipped external gated tests now RUN and PASS (Gemini script,
ElevenLabs synthesize, Imagen image). The single baseline failure
(`test_image_service_generates_scene_images`) is fixed.

---

## Pytest counts

**Before (real keys, baseline):** `1 failed, 63 passed`
 - FAILED `tests/test_external_gated.py::test_image_service_generates_scene_images`
   — Imagen 400 "Setting addWatermark is not supported."

**After:** `64 passed` (keyless + gated, excluding the slow e2e module)
 - All 3 gated external tests pass (not skipped).
 - 61 keyless tests still green.
 - E2E module (`tests/test_e2e_generation.py`, 6 tests) all pass when run
   (kept in a separate run to respect ElevenLabs credit limits).

---

## E2E matrix results

Run via `_generate_video_async(job_id)` (the real Celery task's async impl),
asserting: terminal-success status, MP4 on disk, video stream 1080x1920, an
audio stream present, duration sane for the tier, script within char budget,
EL word-timestamps present.

| # | Genre | Dur | Model | Script src | Image engine | Result | MP4 dur | Notes |
|---|-------|-----|-------|-----------|--------------|--------|---------|-------|
| 1 | horror | 20s | Lite | ai | Imagen 4 Fast | PASS | 16.6s | word_timestamps populated |
| 2 | horror | 60s | Max | manual | Imagen 4 Fast | PASS | ~29s (matches manual script length) | manual length follows user text |
| 3 | brainrot | 30s | Lite | seed | loop footage | PASS | 25.5s | satisfying loop, ducked music |
| 4 | brainrot | 60s | Balanced | ai | loop footage | PASS | ~55s | |
| 5 | custom | 30s | Balanced | ai | Imagen 4 Fast | PASS | 29.6s | |
| 6 | horror | 30s | Lite | ai | Imagen 4 Fast | PASS | ~28s | confirmed retry recovers transient Imagen failure |

Sample MP4s copied for human review (bind-mounted to host `media/samples/`):
 - `media/samples/horror_20s.mp4`  (1080x1920, 16.6s)
 - `media/samples/brainrot_30s.mp4` (1080x1920, 25.5s)
 - `media/samples/custom_30s.mp4`  (1080x1920, 29.6s)

---

## Real bugs found & fixed

### 1. Imagen `:predict` rejects `addWatermark` AND `seed` (HTTP 400) — FATAL
`backend/app/services/assets/image_service.py` (~line 106, `ImagenProvider.generate`).
The payload sent `"seed"` and `"addWatermark": False`. Imagen 4 Fast on the AI
Studio Generative Language API returns **400 "Setting addWatermark is not
supported."** and, with seed alone, **400 "Setting seed is not supported."**
(verified against the live endpoint). This made ALL generated-image videos
(horror/custom) impossible and failed the gated image test.
**Fix:** removed both params from the payload. The `seed` argument is retained in
the method signature for the provider contract; visual coherence across scenes is
steered via the prompt/style prefix.

### 2. `mix_audio` filtergraph reused an output label twice — FATAL
`backend/app/services/video/ffmpeg_utils.py` (`mix_audio`).
The narration label `[voice]` was consumed by BOTH `sidechaincompress` (as the
duck key) AND the final `amix`. An ffmpeg filtergraph output pad can be consumed
only once → `Stream specifier 'voice' ... matches no streams` / `Error binding
filtergraph inputs/outputs`. This failed EVERY video that had background music
(i.e. all of them).
**Fix:** `asplit=2[vkey][vmix]` so the voice feeds the sidechain key and the mix
independently.

### 3. Thinking-model token starvation truncated Gemini JSON — FATAL on Max
`backend/app/services/llm/gemini.py` (`generate_script`, `generate_seo`,
`generate_seed_ideas`).
The Max tier maps to `gemini-3.5-flash`, a **thinking** model where
`max_output_tokens` covers internal reasoning AND visible output. The old budget
(`~2x char_limit/4 + 512`) was entirely consumed by thinking, returning
`finish_reason=MAX_TOKENS` after ~250 chars → `json.JSONDecodeError: Unterminated
string`. horror/60s/Max failed every retry.
**Fix:** budget for real output need (narration is carried twice in the JSON +
per-scene image prompts) and add a fixed thinking reserve with a high floor
(`min(8192, max(4096, output + 2048))`). SEO and seed-idea budgets bumped to 4096
for the same reason. Also added `_loads_lenient()` — a salvage parse that closes a
JSON body truncated mid-structure, so an occasional cap still yields a usable
script instead of failing the whole video.

### 4. Brainrot loop-footage looked in the wrong bucket — FATAL for brainrot
`backend/app/core/genres.py`, `backend/app/services/formats/base.py`,
`backend/app/services/video/pipeline.py`.
The pipeline called `footage_library.pick_loop(fmt.music_bucket)`, but
`music_bucket` for brainrot is `"upbeat_hype"` (a MUSIC bucket). Footage lives in
`satisfying / parkour_clean / hydraulic / kinetic_sand`, so brainrot found no
footage → `No loop footage available`.
**Fix:** added a `footage_bucket` field to each genre (brainrot → `"satisfying"`,
generated-image genres → `None`), threaded it through `FormatOutput`, and the
pipeline now uses `fmt.footage_bucket` (falling back to `music_bucket`). Also made
the footage pick accept a single short loop (footage is looped to length, so it no
longer demands a clip already ≥ full narration).

### 5. Dead import crashed the video service package — FATAL
`backend/app/services/video/__init__.py`.
`from .pipeline import VideoPipeline, PipelineContext` — `PipelineContext` no
longer exists after the v2 rearchitecture → `ImportError` whenever
`app.services.video` was imported as a package.
**Fix:** removed `PipelineContext` from the import and `__all__`.

### 6. Image provider had no retry on transient HTTP failures — ROBUSTNESS
`backend/app/services/assets/image_service.py`.
The 6th e2e video failed with an empty-message `Imagen request failed:` (a
transient timeout/reset — image gen is the most network-heavy step, one call per
scene). Unlike the LLM/TTS layers, the image providers had no retry.
**Fix:** added `_post_with_retry()` (exponential backoff on connection errors and
429/5xx, immediate raise on non-retryable 4xx) and routed both `ImagenProvider`
and `NanoBananaProvider` through it. Re-running the failed combo then passed.

---

## Nano Banana Pro (STEP 4)

Instantiated `NanoBananaProvider` directly (no env change) and generated one image
with `model=gemini-3-pro-image-preview`:
 - **PASS** — 788,262-byte PNG via the `generateContent` inline-image path.
`IMAGE_PROVIDER` remains the default `imagen`.

---

## ElevenLabs credit / permission observations

- `GET /v1/voices` → **401** (key lacks `voices_read`).
- `GET /v1/user/subscription` → **401** (key lacks `user_read`).
- `POST /v1/text-to-speech/{voice}/with-timestamps` → **200**, returns base64
  audio + character alignment, which the service collapses to word timestamps.
  **Verified working across all 6 e2e videos.**
- The pipeline never calls `list_voices`/subscription during generation (voice IDs
  are hardcoded per genre in `app/core/genres.py`), so the missing voice-catalog
  permission does **not** affect generation — it degrades gracefully as required.
- Credit usage kept modest: 6 e2e videos + 3 gated tests + a handful of isolated
  Gemini/Nano probes. Total narration synthesized was well under a few thousand
  characters; no quota errors observed from ElevenLabs.

---

## Still broken / caveats

- None blocking. All 6 matrix combos and the full keyless+gated suite pass.
- The `google-generativeai` SDK is deprecated (emits a FutureWarning). Not fixed
  here — out of scope and currently functional. Migrating to `google-genai` would
  also let us set an explicit `thinking_config` budget instead of reserving tokens.
- Imagen generation is the slow path (~1–2 min/video for multi-scene horror/custom
  due to one image call per scene); functional, not a correctness issue.
