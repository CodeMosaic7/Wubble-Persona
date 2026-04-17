from .Data_structures import BeatInfo, ClipSegment, Timeline
from typing import Optional
from configurations.log import logger

class TimelineBuilder:
    """ Converts beat timestamps + LLM plan (or a default plan) into a Timeline """ 
    def build(self,
        media_paths: list[str],
        beat_info: BeatInfo,
        resolution: tuple[int, int],
        audio_path: str,
        llm_plan: Optional[list[dict]] = None
    ) -> Timeline:
        beats = beat_info.beat_times
        duration = beat_info.duration
        n_media = len(media_paths) 
        # Build cut points: each beat is a cut point; last cut goes to audio end
        cut_times = list(beats) + [duration]
 
        segments: list[ClipSegment] = []
 
        for i, start in enumerate(cut_times[:-1]):
            end = cut_times[i + 1]
 
            if llm_plan and i < len(llm_plan):
                entry = llm_plan[i]
                media_idx = int(entry.get("media_index", i % n_media)) % n_media
                caption = entry.get("caption", "")
                transition = entry.get("transition", "cut")
            else:
                media_idx = i % n_media
                caption = ""
                transition = "cut"
 
            segments.append(
                ClipSegment(
                    media_path=media_paths[media_idx],
                    start_time=start,
                    end_time=end,
                    caption=caption or None,
                    transition=transition,
                )
            )
 
        logger.info("Timeline built: %d segments, %.1fs total", len(segments), duration)
        return Timeline(
            segments=segments,
            audio_path=audio_path,
            duration=duration,
            resolution=resolution,
        )
 
 
