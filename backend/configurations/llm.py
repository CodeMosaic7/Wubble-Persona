import os
from groq import Groq
import json
import textwrap
from Video_generator.Data_structures import BeatInfo
# from dataclasses import Beatinfo
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class LLMDirector:

    def __init__(self, model: str = "llama3-70b-8192"):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.model = model

    def plan(
        self,
        media_paths: list[str],
        beat_info: BeatInfo,
        platform: str,
    ) -> list[dict]:

        media_names = [os.path.basename(p) for p in media_paths]
        n_media = len(media_paths)
        n_beats = len(beat_info.beat_times)

        prompt = textwrap.dedent(f"""
        You are an AI video editor creating a viral short-form video for {platform}.

        Audio Info:
        Duration: {beat_info.duration:.1f}s
        Tempo: {beat_info.tempo:.1f} BPM
        Beats: {n_beats}

        Media Files (0-indexed):
        {json.dumps(media_names)}

        TASK:
        Return ONLY valid JSON array (no markdown).

        Each item:
        {{
          "media_index": int,
          "caption": "short punchy caption",
          "transition": "cut" or "fade"
        }}

        RULES:
        - Generate exactly {min(n_beats, 30)} entries
        - Avoid repeating same media consecutively
        - First and last transition = "fade"
        - Captions should be viral, energetic, under 6 words
        """).strip()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a video editing AI that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        raw = response.choices[0].message.content.strip()
        # cleaning the text
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            plan = json.loads(raw)
        except Exception:
            print(" Raw LLM Output:\n", raw)
            raise Exception("Invalid JSON from Groq")

        return plan