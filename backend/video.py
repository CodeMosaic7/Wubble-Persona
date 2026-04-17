from moviepy.editor import *

# Load video and audio
video = VideoFileClip("raw_footage.mp4")
audio = AudioFileClip("soundtrack.mp3")

# Trim video
clip = video.subclip(0, 30)

# Color grading — cinematic look
clip = clip.fx(vfx.colorx, 1.2)           # boost saturation
clip = clip.fx(vfx.lum_contrast, lum=-20) # darken slightly

# Add fade in/out
clip = clip.fadein(1.5).fadeout(1.5)

# Set audio with fade
audio = audio.subclip(0, 30).audio_fadein(1.5).audio_fadeout(2)
clip = clip.set_audio(audio)

# Add title text
title = (TextClip("MY FILM", fontsize=70, color='white', font='Arial-Bold')
         .set_position('center')
         .set_duration(3)
         .fadein(1).fadeout(1))

# Composite
final = CompositeVideoClip([clip, title])
final.write_videofile("cinematic_output.mp4", fps=24, codec='libx264')