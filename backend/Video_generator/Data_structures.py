from dataclasses import dataclass, field
import numpy as np
from typing import Optional
RESOLUTION_MAP = {
    "reels":"1080x1920",
    "story":"1080x1920",
    "tiktok":"1080x1920",
    "youtube":"1920x1080",
    "landscape":"1920x1080",
    "square":"1080x1080",
}
 
 
def parse_resolution(res: str) -> tuple[int, int]:
    """Parse '1080x1920' → (1080, 1920)."""
    w, h = res.split("x")
    return int(w), int(h)
 
 
@dataclass
class BeatInfo:
    tempo: float
    beat_times: np.ndarray          # seconds
    duration: float                 # total audio seconds
 
 
@dataclass
class ClipSegment:
    media_path: str
    start_time: float               # position in final video (s)
    end_time: float
    caption: Optional[str] = None
    transition: str = "cut"         # "cut" | "fade"
 
 
@dataclass
class Timeline:
    segments: list[ClipSegment] = field(default_factory=list)
    audio_path: str = ""
    duration: float = 0.0
    resolution: tuple[int, int] = (1080, 1920)
 
 
