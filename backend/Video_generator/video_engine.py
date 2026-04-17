from moviepy import *
import random
from typing import Optional
from .Data_structures import parse_resolution
from .helpers import _load_media
from .Timeline_Builder import TimelineBuilder
from .Video_Renderer import VideoRenderer
from .audio_analyzer import AudioAnalyzer
from configurations.llm import LLMDirector
from configurations.log import logger

def apply_effect(clip, effect):
    if effect == "zoom":
        return clip.resize(lambda t: 1 + 0.1 * t)
    elif effect == "fade":
        return clip.crossfadein(0.5)
    return clip


def create_video(
    media_paths: list[str],
    audio_path: str,
    output_path: str,
    resolution: str = "1080x1920",
    platform: str = "reels",
    use_llm: bool = True,
) -> None:
    """
    Pipeline: analyze audio → (optional LLM) → build timeline → render.
    """
    res_tuple = parse_resolution(resolution)
    # 1. Analyze audio
    analyzer = AudioAnalyzer()
    beat_info = analyzer.analyze(audio_path)
    # 2. (Optional) LLM direction
    llm_plan: Optional[list[dict]] = None
    if use_llm:
        try:
            director = LLMDirector()
            llm_plan = director.plan(media_paths, beat_info, platform)
        except Exception as e:
            logger.warning("LLM direction failed (falling back to default): %s", e)
 
    # 3. Build timeline
    builder = TimelineBuilder()
    timeline = builder.build(
        media_paths=media_paths,
        beat_info=beat_info,
        resolution=res_tuple,
        audio_path=audio_path,
        llm_plan=llm_plan,
    )
    # 4. Render
    renderer = VideoRenderer()
    renderer.render(timeline, output_path)
    return output_path
