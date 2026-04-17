from configurations.log import logger
from .Data_structures import BeatInfo
import librosa
import numpy as np

class AudioAnalyzer:
    """ Wraps librosa to extract beat timestamps and audio metadata."""
    def analyze(self, audio_path: str) -> BeatInfo:
        logger.info("Analyzing audio: %s", audio_path)
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = librosa.get_duration(y=y, sr=sr)
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)
        if len(beat_times) == 0:
            beat_times = np.array([0.0])
 
        logger.info(
            "Audio: %.1fs, tempo=%.1f BPM, %d beats", duration, float(tempo), len(beat_times)
        )
        return BeatInfo(
            tempo=float(tempo),
            beat_times=beat_times,
            duration=duration,
        )