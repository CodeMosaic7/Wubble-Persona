import os
from transformers import pipeline
from PIL import Image

# Global variable (so model loads only once)
pipe = None

def init_hg_face():
    global pipe
    if pipe is None:
        pipe = pipeline(
            "image-to-text",
            model="Salesforce/blip-image-captioning-base"
        )

def caption_image(image_path, prompt=None):
    init_hg_face()

    image = Image.open(image_path).convert("RGB")

    if prompt:
        result = pipe(image, prompt=prompt, device=-1)  # CPU
    else:
        result = pipe(image, device=-1)  # CPU

    return result[0]["generated_text"]