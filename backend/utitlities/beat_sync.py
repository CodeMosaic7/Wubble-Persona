import subprocess
import os
import json
import numpy as np
from pathlib import Path
# from configurations.llm import generate_text

# librosa is the core — install with: pip install librosa soundfile
import librosa


# 1. Beat Detection

def detect_beats(audio_path: str) -> dict:
    """
    Analyze audio and return BPM + beat timestamps.
    Also detects energy peaks (drops/hooks) for emphasis.
    """
    y, sr = librosa.load(audio_path, sr=None)

    # Tempo + beat frames
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()

    # RMS energy per beat segment → find high-energy moments
    rms = librosa.feature.rms(y=y)[0]
    rms_times = librosa.frames_to_time(range(len(rms)), sr=sr)
    energy_beats = []
    for bt in beat_times:
        idx = np.argmin(np.abs(rms_times - bt))
        energy_beats.append(float(rms[idx]))

    # Normalize energy 0–1
    max_e = max(energy_beats) if energy_beats else 1
    energy_norm = [round(e / max_e, 3) for e in energy_beats]

    audio_duration = librosa.get_duration(y=y, sr=sr)

    print(f"🥁 BPM: {float(tempo):.1f} | Beats: {len(beat_times)} | Duration: {audio_duration:.2f}s")

    return {
        "bpm": round(float(tempo), 2),
        "beat_times": beat_times,
        "energy_at_beats": energy_norm,
        "audio_duration": round(audio_duration, 3),
    }


# 2. LLM Edit Planner (Beat-Aware)

def ask_llm_beat_plan(
    media_paths: list[str],
    beat_data: dict,
    platform: str,
) -> list[dict]:
    """
    Give the LLM the beat map and let it decide which beats to cut on,
    which media to assign, and which effects to use.
    """
    media_summary = []
    for p in media_paths:
        ext = Path(p).suffix.lower()
        kind = "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image"
        media_summary.append({"file": os.path.basename(p), "type": kind})

    # Only pass every 2nd beat to LLM to avoid overwhelming context
    beats = beat_data["beat_times"]
    energies = beat_data["energy_at_beats"]
    sampled = list(zip(beats[::2], energies[::2]))   # (time, energy) pairs
    sampled_fmt = [{"time": round(t, 3), "energy": e} for t, e in sampled]

    system_prompt = (
        f"You are a professional beat-sync video editor for {platform}. "
        "You cut videos exactly on musical beats to maximize viewer retention. "
        "High-energy beats (energy > 0.7) should get the most impactful visual cuts. "
        "Respond ONLY with a raw JSON array — no markdown, no explanation."
    )

    user_prompt = f"""
Audio duration: {beat_data['audio_duration']}s | BPM: {beat_data['bpm']}

Beat timestamps with energy levels (0=silent, 1=loudest):
{json.dumps(sampled_fmt[:40], indent=2)}

Media files available:
{json.dumps(media_summary, indent=2)}

Create a beat-synced edit plan. Each clip starts at a beat timestamp and ends at the next chosen beat.

Rules:
- Pick cut points from the beat timestamps above (use "time" values)
- First clip MUST start at 0.0
- Last clip MUST end at exactly {beat_data['audio_duration']}s
- On high-energy beats (energy > 0.7): shorter clips (1–2 beats), punchy effects
- On low-energy beats: longer clips (3–5 beats), smoother effects  
- Cycle through media files; repeat if needed to fill the full duration
- Effects: "zoom_in", "zoom_out", "flash", "none" — use "flash" on peak energy beats

Return ONLY this JSON:
[
  {{"file": "photo.jpg", "type": "image", "start": 0.0, "end": 1.85, "effect": "zoom_in"}},
  ...
]
"""

    raw = generate_text(
        user_prompt=user_prompt,
        system_prompt=system_prompt,
        temperature=0.3,
        max_tokens=2048,
    )

    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    plan = json.loads(clean)

    # Map filenames → full paths (cycle if LLM repeated files)
    name_to_path = {os.path.basename(p): p for p in media_paths}
    for clip in plan:
        clip["path"] = name_to_path.get(clip["file"], media_paths[0])
        clip["duration"] = round(clip["end"] - clip["start"], 3)

    # Clamp last clip to exact audio duration
    if plan:
        plan[-1]["end"] = beat_data["audio_duration"]
        plan[-1]["duration"] = round(plan[-1]["end"] - plan[-1]["start"], 3)

    return plan


# 3. FFmpeg Filter Builder (Beat-Aware)

def build_beat_filter(
    plan: list[dict],
    width: str,
    height: str,
    fps: int,
) -> tuple[list, str]:
    inputs = []
    filter_parts = []

    for i, clip in enumerate(plan):
        duration = clip["duration"]
        effect = clip.get("effect", "none")

        if clip["type"] == "image":
            inputs += ["-loop", "1", "-t", str(duration), "-i", clip["path"]]
        else:
            inputs += ["-t", str(duration), "-i", clip["path"]]

        base = (
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={fps}"
        )

        d_frames = max(1, int(duration * fps))

        if effect == "zoom_in":
            base += f",zoompan=z='min(zoom+0.002,1.4)':d={d_frames}:s={width}x{height}"
        elif effect == "zoom_out":
            base += f",zoompan=z='if(lte(zoom,1.0),1.4,max(1.0,zoom-0.002))':d={d_frames}:s={width}x{height}"
        elif effect == "flash":
            # Quick brightness flash on the beat
            base += f",eq=brightness='if(lt(t,0.08),0.6,0)'"

        filter_parts.append(f"{base}[v{i}];")

    # Hard cuts between clips (no xfade — beat sync needs sharp cuts)
    concat_inputs = "".join(f"[v{i}]" for i in range(len(plan)))
    filter_complex = (
        "".join(filter_parts)
        + f"{concat_inputs}concat=n={len(plan)}:v=1:a=0,format=yuv420p[vout]"
    )

    return inputs, filter_complex


# 4. Main Entry Point

def create_beat_synced_video(
    media_paths: list[str],
    audio_path: str,
    output_path: str = "output.mp4",
    resolution: str = "1080x1920",
    fps: int = 30,
    platform: str = "reels",
) -> dict:
    """
    Full pipeline: beat detection → LLM plan → FFmpeg render.
    Returns output path + beat metadata.
    """
    width, height = resolution.split("x")

    # Step 1: Detect beats
    print("🎵 Analyzing audio beats...")
    beat_data = detect_beats(audio_path)

    # Step 2: LLM plans the edit on beats
    print("🤖 Planning beat-synced edit...")
    try:
        plan = ask_llm_beat_plan(media_paths, beat_data, platform)
        print(f"📋 {len(plan)} clips planned across {beat_data['audio_duration']}s")
    except Exception as e:
        print(f"⚠️ LLM failed ({e}), falling back to auto beat split")
        plan = _auto_beat_split(media_paths, beat_data)

    # Filter missing files
    plan = [c for c in plan if c.get("path") and os.path.exists(c["path"])]
    if not plan:
        raise ValueError("No valid media found in plan")

    # Step 3: Build FFmpeg command
    inputs, filter_complex = build_beat_filter(plan, width, height, fps)
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
            "-crf", "20",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path,
        ]
    )

    print("🎬 Rendering beat-synced video...")
    subprocess.run(cmd, check=True)
    print(f"✅ Done: {output_path}")

    return {
        "output_path": output_path,
        "bpm": beat_data["bpm"],
        "total_cuts": len(plan),
        "audio_duration": beat_data["audio_duration"],
    }


def _auto_beat_split(media_paths: list[str], beat_data: dict) -> list[dict]:
    """Fallback: assign one media file per 2 beats, cycling through files."""
    beats = beat_data["beat_times"]
    cut_points = beats[::2]   # every 2nd beat

    if not cut_points or cut_points[0] != 0.0:
        cut_points = [0.0] + cut_points

    plan = []
    n = len(media_paths)
    for i, start in enumerate(cut_points):
        end = cut_points[i + 1] if i + 1 < len(cut_points) else beat_data["audio_duration"]
        p = media_paths[i % n]
        ext = Path(p).suffix.lower()
        plan.append({
            "file": os.path.basename(p),
            "path": p,
            "type": "video" if ext in [".mp4", ".mov", ".avi", ".mkv"] else "image",
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3),
            "effect": "zoom_in",
        })
    return plan