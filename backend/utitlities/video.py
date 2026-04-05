import subprocess
import os
import json
from pathlib import Path
from configurations.llm import generate_text


def get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio_path,
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def ask_llm_for_edit_plan(media_paths: list[str], audio_duration: float, platform: str) -> list[dict]:
    """
    Use Groq LLM to decide how to arrange images/videos into a compelling edit plan.
    Returns a list of clips: [{path, type, duration, effect}, ...]
    """
    media_summary = []
    for p in media_paths:
        ext = Path(p).suffix.lower()
        kind = "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image"
        media_summary.append({"file": os.path.basename(p), "type": kind})

    system_prompt = (
        f"You are a professional short-form video editor specializing in {platform} content. "
        "You create engaging, dynamic edit plans that maximize viewer retention. "
        "You respond ONLY with valid raw JSON arrays — no markdown, no backticks, no explanation."
    )

    user_prompt = f"""
The audio track is {audio_duration:.1f} seconds long.
The user has provided these media files:
{json.dumps(media_summary, indent=2)}

Create a JSON edit plan — an ordered list of clips that together fill the full {audio_duration:.1f}s.

Rules:
- Total duration of all clips must equal exactly {audio_duration:.1f}s
- Spread media evenly but vary pacing for visual interest
- For images: assign duration between 2s and 5s
- For videos: assign duration between 3s and 8s (or full clip length if shorter)
- Choose one of these effects per clip: "fade", "zoom_in", "zoom_out", "none"
- Prefer "zoom_in" or "zoom_out" for images to keep them dynamic
- Order clips for maximum visual impact

Respond ONLY with a valid JSON array, no markdown, no explanation:
[
  {{"file": "image_0.jpg", "type": "image", "duration": 3.5, "effect": "zoom_in"}},
  ...
]
"""

    raw = generate_text(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.4,        # lower = more consistent JSON output
        max_tokens=1024,
    )

    # Strip accidental markdown fences if model adds them
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    plan = json.loads(clean)

    # Map filenames back to full paths
    name_to_path = {os.path.basename(p): p for p in media_paths}
    for clip in plan:
        clip["path"] = name_to_path.get(clip["file"], "")

    # Safety: fix total duration drift (LLM sometimes gets it slightly wrong)
    total = sum(c["duration"] for c in plan)
    if abs(total - audio_duration) > 0.1:
        scale = audio_duration / total
        for clip in plan:
            clip["duration"] = round(clip["duration"] * scale, 3)

    return plan


def build_ffmpeg_filter(
    plan: list[dict],
    width: str,
    height: str,
    fps: int,
    fade_duration: float
) -> tuple[list, str]:
    """Build FFmpeg inputs + filter_complex from the edit plan."""
    inputs = []
    filter_parts = []

    for i, clip in enumerate(plan):
        if clip["type"] == "image":
            inputs += ["-loop", "1", "-t", str(clip["duration"]), "-i", clip["path"]]
        else:
            inputs += ["-t", str(clip["duration"]), "-i", clip["path"]]

        effect = clip.get("effect", "none")
        base = (
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"
        )

        if effect == "zoom_in":
            base += (
                f",zoompan=z='min(zoom+0.001,1.3)'"
                f":d={int(float(clip['duration']) * fps)}"
                f":s={width}x{height}"
            )
        elif effect == "zoom_out":
            base += (
                f",zoompan=z='if(lte(zoom,1.0),1.3,max(1.0,zoom-0.001))'"
                f":d={int(float(clip['duration']) * fps)}"
                f":s={width}x{height}"
            )

        filter_parts.append(f"{base}[v{i}];")

    # Chain xfade transitions between all clips
    prev = "v0"
    offset_acc = 0.0
    for i in range(1, len(plan)):
        offset_acc += plan[i - 1]["duration"] - fade_duration
        out = f"vx{i}"
        filter_parts.append(
            f"[{prev}][v{i}]xfade=transition=fade"
            f":duration={fade_duration}"
            f":offset={offset_acc:.3f}[{out}];"
        )
        prev = out

    filter_complex = "".join(filter_parts) + f"[{prev}]format=yuv420p[vout]"
    return inputs, filter_complex


def _even_split_plan(media_paths: list[str], audio_duration: float) -> list[dict]:
    """Fallback: split audio duration evenly across all media."""
    duration_each = round(audio_duration / len(media_paths), 3)
    plan = []
    for p in media_paths:
        ext = Path(p).suffix.lower()
        kind = "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image"
        plan.append({
            "file": os.path.basename(p),
            "path": p,
            "type": kind,
            "duration": duration_each,
            "effect": "zoom_in" if kind == "image" else "none",
        })
    return plan


def create_video(
    media_paths: list[str],
    audio_path: str,
    output_path: str = "output.mp4",
    resolution: str = "1080x1920",
    fps: int = 30,
    fade_duration: float = 0.5,
    platform: str = "reels",
    use_llm: bool = True,
):
    width, height = resolution.split("x")
    audio_duration = get_audio_duration(audio_path)
    print(f"🎵 Audio duration: {audio_duration:.2f}s")

    if use_llm and len(media_paths) > 0:
        print("Asking Groq to plan the edit...")
        try:
            plan = ask_llm_for_edit_plan(media_paths, audio_duration, platform)
            print(f"Edit plan ({len(plan)} clips):\n{json.dumps(plan, indent=2)}")
        except Exception as e:
            print(f"LLM planning failed: {e} — falling back to even split")
            plan = _even_split_plan(media_paths, audio_duration)
    else:
        plan = _even_split_plan(media_paths, audio_duration)

    # Guard: skip clips with missing paths
    plan = [c for c in plan if c.get("path") and os.path.exists(c["path"])]
    if not plan:
        raise ValueError("No valid media files found in edit plan")

    inputs, filter_complex = build_ffmpeg_filter(plan, width, height, fps, fade_duration)

    audio_index = len(plan)
    inputs += ["-i", audio_path]

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{audio_index}:a",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path,
        ]
    )

    print("🎬 Rendering video...")
    subprocess.run(cmd, check=True)
    print(f"Video saved: {output_path}")
    return output_path