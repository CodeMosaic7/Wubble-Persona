from .Data_structures import Timeline
from .helpers import _load_media
from moviepy import (
    concatenate_videoclips,
    TextClip,
    CompositeVideoClip,
    AudioFileClip,
)
from configurations.log import logger
import os

class VideoRenderer:
    """
    Renders a Timeline into an mp4 using MoviePy.
    Handles both image and video media.  Adds captions when present.
    """
 
    CAPTION_FONT = "DejaVu-Sans-Bold"
    CAPTION_FONTSIZE = 48
    CAPTION_COLOR = "white"
    CAPTION_STROKE_COLOR = "black"
    CAPTION_STROKE_WIDTH = 2
    CAPTION_POSITION = ("center", 0.82)  # relative from top
 
    def render(self, timeline: Timeline, output_path: str) -> None:
        w, h = timeline.resolution
        clips = []
 
        for seg in timeline.segments:
            clip_duration = seg.end_time - seg.start_time
            if clip_duration <= 0:
                continue
 
            # Load media
            media_clip = self._load_media(seg.media_path, w, h, clip_duration)

            # Apply transition
            if seg.transition == "fade":
                media_clip = media_clip.fadein(0.15).fadeout(0.15)
 
            # Add caption overlay
            if seg.caption:
                try:
                    txt = TextClip(
                        seg.caption,
                        fontsize=self.CAPTION_FONTSIZE,
                        font=self.CAPTION_FONT,
                        color=self.CAPTION_COLOR,
                        stroke_color=self.CAPTION_STROKE_COLOR,
                        stroke_width=self.CAPTION_STROKE_WIDTH,
                        method="caption",
                        size=(int(w * 0.85), None),
                        align="center",
                    ).set_duration(clip_duration)
 
                    txt = txt.set_position(self.CAPTION_POSITION, relative=True)
                    media_clip = CompositeVideoClip([media_clip, txt])
                except Exception as e:
                    logger.warning("Caption render failed ('%s'): %s", seg.caption, e)
 
            clips.append(media_clip)
 
        if not clips:
            raise RuntimeError("No clips were generated from the timeline")
 
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
 
        # Attach audio
        audio = AudioFileClip(timeline.audio_path).subclip(0, timeline.duration)
        final_video = final_video.set_audio(audio)
 
        # Export
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        logger.info("Rendering to %s …", output_path)
        final_video.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="fast",
            threads=4,
            logger=None,           # suppress moviepy progress bars in prod
        )
 
        # Cleanup
        final_video.close()
        audio.close()
        for c in clips:
            c.close()
 
        logger.info("Render complete: %s", output_path)
 