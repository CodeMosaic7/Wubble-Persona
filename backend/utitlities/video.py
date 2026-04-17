# import subprocess
# import os
# import json
# from pathlib import Path
# from configurations.llm import generate_text


# def get_audio_duration(audio_path: str) -> float:
#     result = subprocess.run(
#         [
#             "ffprobe", "-v", "error",
#             "-show_entries", "format=duration",
#             "-of", "default=noprint_wrappers=1:nokey=1",
#             audio_path,
#         ],
#         capture_output=True, text=True, check=True,
#     )
#     return float(result.stdout.strip())


# def ask_llm_for_edit_plan(media_paths: list[str], audio_duration: float, platform: str) -> list[dict]:
#     """
#     Use Groq LLM to decide how to arrange images/videos into a compelling edit plan.
#     Returns a list of clips: [{path, type, duration, effect}, ...]
#     """
#     media_summary = []
#     for p in media_paths:
#         ext = Path(p).suffix.lower()
#         kind = "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image"
#         media_summary.append({"file": os.path.basename(p), "type": kind})

#     system_prompt = (
#         f"You are a professional short-form video editor specializing in {platform} content. "
#         "You create engaging, dynamic edit plans that maximize viewer retention. "
#         "You respond ONLY with valid raw JSON arrays — no markdown, no backticks, no explanation."
#     )

#     user_prompt = f"""
# The audio track is {audio_duration:.1f} seconds long.
# The user has provided these media files:
# {json.dumps(media_summary, indent=2)}

# Create a JSON edit plan — an ordered list of clips that together fill the full {audio_duration:.1f}s.

# Rules:
# - Total duration of all clips must equal exactly {audio_duration:.1f}s
# - Spread media evenly but vary pacing for visual interest
# - For images: assign duration between 2s and 5s
# - For videos: assign duration between 3s and 8s (or full clip length if shorter)
# - Choose one of these effects per clip: "fade", "zoom_in", "zoom_out", "none"
# - Prefer "zoom_in" or "zoom_out" for images to keep them dynamic
# - Order clips for maximum visual impact

# Respond ONLY with a valid JSON array, no markdown, no explanation:
# [
#   {{"file": "image_0.jpg", "type": "image", "duration": 3.5, "effect": "zoom_in"}},
#   ...
# ]
# """

#     raw = generate_text(
#         user_prompt=user_prompt,
#         system_prompt=system_prompt,
#         temperature=0.4,        # lower = more consistent JSON output
#         max_tokens=1024,
#     )

#     # Strip accidental markdown fences if model adds them
#     clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
#     plan = json.loads(clean)

#     # Map filenames back to full paths
#     name_to_path = {os.path.basename(p): p for p in media_paths}
#     for clip in plan:
#         clip["path"] = name_to_path.get(clip["file"], "")

#     # Safety: fix total duration drift (LLM sometimes gets it slightly wrong)
#     total = sum(c["duration"] for c in plan)
#     if abs(total - audio_duration) > 0.1:
#         scale = audio_duration / total
#         for clip in plan:
#             clip["duration"] = round(clip["duration"] * scale, 3)

#     return plan


# def build_ffmpeg_filter(
#     plan: list[dict],
#     width: str,
#     height: str,
#     fps: int,
#     fade_duration: float
# ) -> tuple[list, str]:
#     """Build FFmpeg inputs + filter_complex from the edit plan."""
#     inputs = []
#     filter_parts = []

#     for i, clip in enumerate(plan):
#         if clip["type"] == "image":
#             inputs += ["-loop", "1", "-t", str(clip["duration"]), "-i", clip["path"]]
#         else:
#             inputs += ["-t", str(clip["duration"]), "-i", clip["path"]]

#         effect = clip.get("effect", "none")
#         base = (
#             f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
#             f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"
#         )

#         if effect == "zoom_in":
#             base += (
#                 f",zoompan=z='min(zoom+0.001,1.3)'"
#                 f":d={int(float(clip['duration']) * fps)}"
#                 f":s={width}x{height}"
#             )
#         elif effect == "zoom_out":
#             base += (
#                 f",zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.001))'"
#                 f":d={int(float(clip['duration']) * fps)}"
#                 f":s={width}x{height}"
#             )

#         filter_parts.append(f"{base}[v{i}];")

#     # Chain xfade transitions between all clips
#     prev = "v0"
#     offset_acc = 0.0
#     for i in range(1, len(plan)):
#         offset_acc += plan[i - 1]["duration"] - fade_duration
#         out = f"vx{i}"
#         filter_parts.append(
#             f"[{prev}][v{i}]xfade=transition=fade"
#             f":duration={fade_duration}"
#             f":offset={offset_acc:.3f}[{out}];"
#         )
#         prev = out

#     filter_complex = "".join(filter_parts) + f"[{prev}]format=yuv420p[vout]"
#     return inputs, filter_complex


# def _even_split_plan(media_paths: list[str], audio_duration: float) -> list[dict]:
#     """Fallback: split audio duration evenly across all media."""
#     duration_each = round(audio_duration / len(media_paths), 3)
#     plan = []
#     for p in media_paths:
#         ext = Path(p).suffix.lower()
#         kind = "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image"
#         plan.append({
#             "file": os.path.basename(p),
#             "path": p,
#             "type": kind,
#             "duration": duration_each,
#             "effect": "zoom_in" if kind == "image" else "none",
#         })
#     return plan


# def create_video(
#     media_paths: list[str],
#     audio_path: str,
#     output_path: str = "output.mp4",
#     resolution: str = "1080x1920",
#     fps: int = 30,
#     fade_duration: float = 0.5,
#     platform: str = "reels",
#     use_llm: bool = True,
# ):
#     width, height = resolution.split("x")
#     audio_duration = get_audio_duration(audio_path)
#     print(f"🎵 Audio duration: {audio_duration:.2f}s")

#     if use_llm and len(media_paths) > 0:
#         print("Asking Groq to plan the edit...")
#         try:
#             plan = ask_llm_for_edit_plan(media_paths, audio_duration, platform)
#             print(f"Edit plan ({len(plan)} clips):\n{json.dumps(plan, indent=2)}")
#         except Exception as e:
#             print(f"LLM planning failed: {e} — falling back to even split")
#             plan = _even_split_plan(media_paths, audio_duration)
#     else:
#         plan = _even_split_plan(media_paths, audio_duration)

#     # Guard: skip clips with missing paths
#     plan = [c for c in plan if c.get("path") and os.path.exists(c["path"])]
#     if not plan:
#         raise ValueError("No valid media files found in edit plan")

#     inputs, filter_complex = build_ffmpeg_filter(plan, width, height, fps, fade_duration)

#     audio_index = len(plan)
#     inputs += ["-i", audio_path]

#     cmd = (
#         ["ffmpeg", "-y"]
#         + inputs
#         + [
#             "-filter_complex", filter_complex,
#             "-map", "[vout]",
#             "-map", f"{audio_index}:a",
#             "-c:v", "libx264",
#             "-preset", "fast",
#             "-crf", "23",
#             "-c:a", "aac",
#             "-b:a", "192k",
#             "-shortest",
#             output_path,
#         ]
#     )

#     print("🎬 Rendering video...")
#     subprocess.run(cmd, check=True)
#     print(f"Video saved: {output_path}")
#     return output_path

"""
video_creator.py
================
AI-powered cinematic video editor.
Combines images/videos with an audio track using FFmpeg,
optionally using an LLM to plan the edit timing and effects.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Types & constants
# ---------------------------------------------------------------------------

VIDEO_EXTENSIONS: frozenset[str] = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})
IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"})

MIN_IMAGE_DURATION = 2.0    # seconds
MAX_IMAGE_DURATION = 5.0    # seconds
MIN_VIDEO_DURATION = 3.0    # seconds
MAX_VIDEO_DURATION = 8.0    # seconds


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"


class Effect(str, Enum):
    FADE     = "fade"
    ZOOM_IN  = "zoom_in"
    ZOOM_OUT = "zoom_out"
    NONE     = "none"


@dataclass
class MediaClip:
    """Represents a single clip in the edit plan."""
    file:     str
    path:     str
    type:     MediaType
    duration: float
    effect:   Effect = Effect.NONE

    @property
    def exists(self) -> bool:
        return bool(self.path) and Path(self.path).is_file()

    def to_dict(self) -> dict:
        return {
            "file":     self.file,
            "path":     self.path,
            "type":     self.type.value,
            "duration": self.duration,
            "effect":   self.effect.value,
        }


@dataclass
class RenderConfig:
    """All rendering parameters in one place."""
    resolution:    str   = "1080x1920"
    fps:           int   = 30
    fade_duration: float = 0.5
    platform:      str   = "reels"
    video_codec:   str   = "libx264"
    audio_codec:   str   = "aac"
    audio_bitrate: str   = "192k"
    crf:           int   = 23
    preset:        str   = "fast"
    use_llm:       bool  = True

    @property
    def width(self) -> str:
        return self.resolution.split("x")[0]

    @property
    def height(self) -> str:
        return self.resolution.split("x")[1]


# ---------------------------------------------------------------------------
# Media helpers
# ---------------------------------------------------------------------------

def classify_media(path: str) -> MediaType:
    """Return MediaType based on file extension."""
    ext = Path(path).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    if ext in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    raise ValueError(f"Unsupported file type: {ext!r} ({path})")


def get_audio_duration(audio_path: str) -> float:
    """Return duration of an audio (or video) file in seconds via ffprobe."""
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    duration = float(result.stdout.strip())
    log.info("Audio duration: %.2fs  (%s)", duration, path.name)
    return duration


def validate_media_paths(paths: list[str]) -> list[str]:
    """Filter out missing files and warn; raise if nothing remains."""
    valid = [p for p in paths if Path(p).is_file()]
    missing = set(paths) - set(valid)
    for p in missing:
        log.warning("Media file not found, skipping: %s", p)
    if not valid:
        raise ValueError("No valid media files found.")
    return valid


# ---------------------------------------------------------------------------
# Edit plan: LLM-based
# ---------------------------------------------------------------------------

def _build_llm_prompt(
    media_summary: list[dict],
    audio_duration: float,
    platform: str,
) -> tuple[str, str]:
    system_prompt = (
        f"You are a professional short-form video editor specialising in {platform} content. "
        "You create engaging, dynamic edit plans that maximise viewer retention. "
        "Respond ONLY with a valid raw JSON array — no markdown, no backticks, no explanation."
    )

    user_prompt = f"""
Audio track length: {audio_duration:.1f}s
Media files available:
{json.dumps(media_summary, indent=2)}

Produce an ordered JSON edit plan whose clip durations sum to exactly {audio_duration:.1f}s.

Rules:
- Images: duration {MIN_IMAGE_DURATION}s – {MAX_IMAGE_DURATION}s
- Videos: duration {MIN_VIDEO_DURATION}s – {MAX_VIDEO_DURATION}s (or full clip if shorter)
- Each clip has one effect: "fade", "zoom_in", "zoom_out", or "none"
- Prefer "zoom_in" / "zoom_out" for images to keep them dynamic
- Order for maximum visual impact

Return ONLY a JSON array:
[
  {{"file": "example.jpg", "type": "image", "duration": 3.5, "effect": "zoom_in"}},
  ...
]
"""
    return system_prompt, user_prompt


def _normalise_plan_duration(clips: list[MediaClip], target: float) -> list[MediaClip]:
    """Scale clip durations so they sum exactly to *target* seconds."""
    total = sum(c.duration for c in clips)
    drift = abs(total - target)
    if drift > 0.05:
        log.debug("Normalising plan duration: %.3fs → %.3fs (drift %.3fs)", total, target, drift)
        scale = target / total
        for clip in clips:
            clip.duration = round(clip.duration * scale, 3)
    return clips


def _parse_llm_response(
    raw: str,
    name_to_path: dict[str, str],
    audio_duration: float,
) -> list[MediaClip]:
    """Parse raw LLM text into a validated list of MediaClip objects."""
    clean = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    data: list[dict] = json.loads(clean)

    clips: list[MediaClip] = []
    for item in data:
        filename = item.get("file", "")
        full_path = name_to_path.get(filename, "")
        try:
            media_type = MediaType(item.get("type", "image"))
        except ValueError:
            media_type = classify_media(full_path) if full_path else MediaType.IMAGE
        try:
            effect = Effect(item.get("effect", "none"))
        except ValueError:
            effect = Effect.NONE

        clips.append(MediaClip(
            file=filename,
            path=full_path,
            type=media_type,
            duration=float(item.get("duration", 3.0)),
            effect=effect,
        ))

    return _normalise_plan_duration(clips, audio_duration)


def ask_llm_for_edit_plan(
    media_paths: list[str],
    audio_duration: float,
    platform: str,
) -> list[MediaClip]:
    """
    Ask the LLM to produce a timed edit plan for the given media files.
    Returns a list of MediaClip objects ordered for maximum visual impact.
    """
    # Lazy import so the rest of the module works without this dependency
    from configurations.llm import generate_text  # type: ignore

    media_summary = [
        {"file": Path(p).name, "type": classify_media(p).value}
        for p in media_paths
    ]
    name_to_path = {Path(p).name: p for p in media_paths}

    system_prompt, user_prompt = _build_llm_prompt(media_summary, audio_duration, platform)

    log.info("Requesting LLM edit plan for %d clips (platform: %s)…", len(media_paths), platform)
    raw = generate_text(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.4,
        max_tokens=1024,
    )

    clips = _parse_llm_response(raw, name_to_path, audio_duration)
    log.info("LLM plan received: %d clips", len(clips))
    return clips


# ---------------------------------------------------------------------------
# Edit plan: fallback (even split)
# ---------------------------------------------------------------------------

def even_split_plan(media_paths: list[str], audio_duration: float) -> list[MediaClip]:
    """Distribute audio duration evenly across all media files."""
    duration_each = round(audio_duration / len(media_paths), 3)
    clips = []
    for p in media_paths:
        media_type = classify_media(p)
        clips.append(MediaClip(
            file=Path(p).name,
            path=p,
            type=media_type,
            duration=duration_each,
            effect=Effect.ZOOM_IN if media_type == MediaType.IMAGE else Effect.NONE,
        ))
    log.info("Fallback plan: %d clips × %.3fs each", len(clips), duration_each)
    return clips


# ---------------------------------------------------------------------------
# FFmpeg command builder
# ---------------------------------------------------------------------------

def _video_filter_for_clip(
    index: int,
    clip: MediaClip,
    width: str,
    height: str,
    fps: int,
) -> str:
    """Return the FFmpeg filter string for one input clip."""
    n_frames = int(clip.duration * fps)
    base = (
        f"[{index}:v]"
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,"
        f"setsar=1,"
        f"fps={fps}"
    )

    if clip.effect == Effect.ZOOM_IN:
        base += (
            f",zoompan=z='min(zoom+0.001,1.3)'"
            f":d={n_frames}"
            f":s={width}x{height}"
        )
    elif clip.effect == Effect.ZOOM_OUT:
        base += (
            f",zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.001))'"
            f":d={n_frames}"
            f":s={width}x{height}"
        )

    return base + f"[v{index}]"


def build_ffmpeg_command(
    plan: list[MediaClip],
    audio_path: str,
    output_path: str,
    cfg: RenderConfig,
) -> list[str]:
    """
    Construct the complete FFmpeg command list for the edit plan.
    Handles inputs, filter_complex (with xfade transitions), and encoding options.
    """
    inputs: list[str] = []
    filter_parts: list[str] = []

    # --- Input flags + per-clip video filters ---
    for i, clip in enumerate(plan):
        if clip.type == MediaType.IMAGE:
            inputs += ["-loop", "1", "-t", str(clip.duration), "-i", clip.path]
        else:
            inputs += ["-t", str(clip.duration), "-i", clip.path]

        filter_parts.append(
            _video_filter_for_clip(i, clip, cfg.width, cfg.height, cfg.fps) + ";"
        )

    # --- Chain xfade transitions between clips ---
    prev_label = "v0"
    offset_acc = 0.0

    for i in range(1, len(plan)):
        offset_acc += plan[i - 1].duration - cfg.fade_duration
        out_label = f"vx{i}"
        filter_parts.append(
            f"[{prev_label}][v{i}]"
            f"xfade=transition=fade"
            f":duration={cfg.fade_duration}"
            f":offset={offset_acc:.3f}"
            f"[{out_label}];"
        )
        prev_label = out_label

    filter_complex = (
        "".join(filter_parts)
        + f"[{prev_label}]format=yuv420p[vout]"
    )

    audio_index = len(plan)
    inputs += ["-i", audio_path]

    return (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{audio_index}:a",
            "-c:v", cfg.video_codec,
            "-preset", cfg.preset,
            "-crf", str(cfg.crf),
            "-c:a", cfg.audio_codec,
            "-b:a", cfg.audio_bitrate,
            "-shortest",
            output_path,
        ]
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def create_video(
    media_paths: list[str],
    audio_path: str,
    output_path: str = "output.mp4",
    resolution: str = "1080x1920",
    fps: int = 30,
    fade_duration: float = 0.5,
    platform: str = "reels",
    use_llm: bool = True,
    render_config: Optional[RenderConfig] = None,
) -> str:
    """
    Render a cinematic short-form video from media files and an audio track.

    Parameters
    ----------
    media_paths   : Ordered list of image / video file paths.
    audio_path    : Path to the audio file (mp3, wav, aac, …).
    output_path   : Destination for the rendered MP4.
    resolution    : WIDTHxHEIGHT string, e.g. "1080x1920" for vertical video.
    fps           : Frames per second (24 for cinematic, 30 for social).
    fade_duration : Cross-fade length in seconds between clips.
    platform      : Guides LLM pacing style ("reels", "tiktok", "youtube", …).
    use_llm       : If True, ask LLM for the edit plan; else use even split.
    render_config : Override all render params with a RenderConfig instance.

    Returns
    -------
    str : Absolute path to the rendered video file.
    """
    cfg = render_config or RenderConfig(
        resolution=resolution,
        fps=fps,
        fade_duration=fade_duration,
        platform=platform,
        use_llm=use_llm,
    )

    # --- Validate inputs ---
    media_paths = validate_media_paths(media_paths)
    audio_duration = get_audio_duration(audio_path)

    # --- Build edit plan ---
    plan: list[MediaClip] = []

    if cfg.use_llm:
        try:
            plan = ask_llm_for_edit_plan(media_paths, audio_duration, cfg.platform)
        except Exception as exc:
            log.warning("LLM planning failed (%s) — falling back to even split.", exc)
            plan = even_split_plan(media_paths, audio_duration)
    else:
        plan = even_split_plan(media_paths, audio_duration)

    # Remove clips whose files couldn't be resolved
    valid_plan = [c for c in plan if c.exists]
    skipped = len(plan) - len(valid_plan)
    if skipped:
        log.warning("%d clip(s) removed from plan (file not found).", skipped)
    if not valid_plan:
        raise ValueError("Edit plan contains no valid media files.")

    log.info(
        "Final plan: %d clips | total %.2fs | resolution %s | %dfps",
        len(valid_plan),
        sum(c.duration for c in valid_plan),
        cfg.resolution,
        cfg.fps,
    )
    for i, clip in enumerate(valid_plan, 1):
        log.debug("  [%02d] %-30s %s  %.2fs  %s", i, clip.file, clip.type.value, clip.duration, clip.effect.value)

    # --- Build & run FFmpeg command ---
    cmd = build_ffmpeg_command(valid_plan, audio_path, output_path, cfg)
    log.info("Rendering with FFmpeg…")
    log.debug("FFmpeg command:\n  %s", " ".join(cmd))

    subprocess.run(cmd, check=True)

    abs_output = str(Path(output_path).resolve())
    log.info("Video saved → %s", abs_output)
    return abs_output