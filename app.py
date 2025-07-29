
import streamlit as st
import tempfile
import cv2
import os
from PIL import Image
import numpy as np
from pipecat.grok import GrokLLMService

# initialize Groq client
grok = GrokLLMService(api_key=os.getenv("GROQ_API_KEY"))

st.title("🎥 Sports Coaching Video Analyzer (using Groq + OpenCV)")

video_file = st.file_uploader("Upload a video (.mp4)", type=["mp4"])
interval_sec = st.number_input("Frame interval (sec)", min_value=1, max_value=10, value=3)

if video_file:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(video_file.read())
    tfile.flush()
    cap = cv2.VideoCapture(tfile.name)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    interval_frames = int(fps * interval_sec)
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = n_frames / fps

    st.write(f"Video duration: {duration:.1f}s, FPS: {fps:.2f}")

    summaries = []
    i = 0
    frame_count = 0
    container = st.container()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % interval_frames == 0:
            # convert to PIL for display & Groq
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            container.image(pil, caption=f"Frame at {frame_count/fps:.1f}s", use_column_width=True)
            # prepare image as bytes
            buffered = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            pil.save(buffered.name, format="JPEG")
            with open(buffered.name, "rb") as f:
                img_bytes = f.read()

            # call groq
            prompt = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "image": {"bytes": img_bytes},
                "text": "Describe what is happening in this frame."
            }
            resp = grok.generate(prompt)
            desc = resp.text.strip()
            summaries.append((frame_count/fps, desc))
            container.write(f"**AI description:** {desc}")

        frame_count += 1

    cap.release()
    os.unlink(tfile.name)

    st.header("Summary of feedback")
    full_summary = "\n".join(f"At {t:.1f}s: {d}" for t, d in summaries)
    st.write(full_summary)

    # optional nice natural-language summary
    if summaries:
        combined = "\n".join(d for _, d in summaries)
        prompt2 = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "text": f"Summarize the following observations into coaching advice:\n\n{combined}"
        }
        coach = grok.generate(prompt2).text.strip()
        st.subheader("📣 Coaching Suggestions")
        st.write(coach)
