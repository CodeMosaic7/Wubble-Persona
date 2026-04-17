import os
from PIL import Image
from moviepy import ImageClip, VideoFileClip, ColorClip, CompositeVideoClip
import numpy as np


def _load_media(self, path: str, w: int, h: int, duration: float):
    """Return a MoviePy clip (image or video) sized to (w, h)."""
    ext = os.path.splitext(path)[1].lower()

    if ext in (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"):
            clip = (
                ImageClip(path)
                .set_duration(duration)
                .resize(self._fit_size(path, w, h))
            )
            # Centre on black background if aspect doesn't match
            bg = ColorClip(size=(w, h), color=(0, 0, 0), duration=duration)
            clip = clip.set_position("center")
            return CompositeVideoClip([bg, clip], size=(w, h))
 
    else:
            # Video file — loop or trim to fit duration
            vc = VideoFileClip(path)
            if vc.duration < duration:
                loops = int(np.ceil(duration / vc.duration))
                vc = concatenate_videoclips([vc] * loops).subclip(0, duration)
            else:
                vc = vc.subclip(0, duration)
            vc = vc.resize(self._fit_size(path, w, h, is_video=True))
            bg = ColorClip(size=(w, h), color=(0, 0, 0), duration=duration)
            vc = vc.set_position("center")
            return CompositeVideoClip([bg, vc], size=(w, h))
 
@staticmethod
def _fit_size(path: str, target_w: int, target_h: int, is_video: bool = False) -> tuple[int, int]:
        """Scale proportionally so the clip fills the target frame (cover)."""
        try:
            if is_video:
                vc = VideoFileClip(path)
                src_w, src_h = vc.size
                vc.close()
            else:
                img = Image.open(path)
                src_w, src_h = img.size
        except Exception:
            return (target_w, target_h)
 
        scale = max(target_w / src_w, target_h / src_h)
        return (int(src_w * scale), int(src_h * scale))