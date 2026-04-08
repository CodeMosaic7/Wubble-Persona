def parse_wubble_response(song_data: dict) -> tuple[str, list]:
    """
    Parse the Wubble API response shape:
    {
      "streaming": { "final_audio_url": "https://..." },
      "results": {
        "custom_data": {
          "audios": [{ "lyrics_sections": [...] }]
        }
      }
    }
    Returns (audio_url, lyrics_sections)
    """
    audio_url = (
        song_data.get("streaming", {}).get("final_audio_url")
        or song_data.get("results", {})
                  .get("custom_data", {})
                  .get("audios", [{}])[0]
                  .get("audio_url")
    )

    lyrics_sections = (
        song_data.get("results", {})
                 .get("custom_data", {})
                 .get("audios", [{}])[0]
                 .get("lyrics_sections", [])
    )

    return audio_url, lyrics_sections

def build_lyrics_subtitles(lyrics_sections: list, srt_path: str):
    """
    Convert Wubble lyrics_sections (with ms timestamps) → .srt subtitle file.
    Only includes sections that have lines (skips bare intro/outro markers).
    """
    entries = []
    for section in lyrics_sections:
        for line in section.get("lines", []):
            entries.append({
                "start_ms": line["start"],
                "end_ms": line["end"],
                "text": line["text"],
            })

    def ms_to_srt_time(ms: int) -> str:
        h = ms // 3_600_000
        m = (ms % 3_600_000) // 60_000
        s = (ms % 60_000) // 1_000
        milli = ms % 1_000
        return f"{h:02}:{m:02}:{s:02},{milli:03}"

    with open(srt_path, "w", encoding="utf-8") as f:
        for idx, entry in enumerate(entries, 1):
            f.write(f"{idx}\n")
            f.write(f"{ms_to_srt_time(entry['start_ms'])} --> {ms_to_srt_time(entry['end_ms'])}\n")
            f.write(f"{entry['text']}\n\n")

    return srt_path if entries else None


def burn_subtitles(input_video: str, srt_path: str, output_video: str, resolution: str):
    """
    Burn styled subtitles into the video using FFmpeg subtitles filter.
    Font size and position are tuned for vertical (Reels/TikTok) formats.
    """
    width = resolution.split("x")[0]
    font_size = 22 if int(width) >= 1080 else 16

    subtitle_style = (
        f"FontName=Arial,FontSize={font_size},Bold=1,"
        "PrimaryColour=&H00FFFFFF,"   
        "OutlineColour=&H00000000,"  
        "Outline=2,Shadow=1,"
        "Alignment=2,"                
        "MarginV=120"                 
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-vf", f"subtitles={srt_path}:force_style='{subtitle_style}'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        output_video,
    ]
    subprocess.run(cmd, check=True)