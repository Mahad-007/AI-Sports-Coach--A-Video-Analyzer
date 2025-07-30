import os
import io
import cv2
import base64
import tempfile
from PIL import Image

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Use a vision-capable model
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

st.set_page_config(page_title="Exercise Coaching Analyzer", layout="wide")
st.title("🎥 Exercise Video Coaching (Groq + OpenCV)")

video_file = st.file_uploader("Upload a video (.mp4)", type=["mp4"])
interval_sec = st.number_input("Frame interval (seconds)", min_value=1, max_value=10, value=3)

if video_file:
    tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp_video.write(video_file.read())
    tmp_video.flush()

    cap = cv2.VideoCapture(tmp_video.name)
    if not cap.isOpened():
        st.error("Unable to open video file.")
    else:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        interval = max(1, int(fps * interval_sec))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
        st.write(f"Duration: {total:.1f}s — FPS: {fps:.2f}")

        summaries = []
        frame_idx = 0
        container = st.container()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % interval == 0:
                ts = frame_idx / fps

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb)
                container.image(pil, caption=f"Frame at {ts:.1f}s", use_container_width=True)

                # Encode frame to base64
                buf = io.BytesIO()
                pil.save(buf, format="JPEG", quality=85)
                encoded = base64.b64encode(buf.getvalue()).decode("utf-8")

                # Build chat message with image content
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": (
                                "You are a certified fitness trainer. Analyze the athlete's form in this image. "
                                "Focus on posture, technique, and safety. Provide specific feedback."
                            )},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/jpeg;base64,{encoded}"
                            }}
                        ]
                    }
                ]

                resp = client.chat.completions.create(
                    model=VISION_MODEL,
                    messages=messages,
                    temperature=0.2,
                )

                caption = resp.choices[0].message.content.strip()
                summaries.append((ts, caption))
                container.markdown(f"**AI analysis:** {caption}")

            frame_idx += 1

        cap.release()
    try:
        os.unlink(tmp_video.name)
    except:
        pass

    if summaries:
        st.header("📋 Frame-level Feedback")
        for t, desc in summaries:
            st.write(f"- At {t:.1f}s: {desc}")

        combined = "\n".join(desc for _, desc in summaries)
        advice_messages = [
            {"role": "system", "content": (
                "You are a certified fitness trainer with experience across all types of exercises."
            )},
            {"role": "user", "content": (
                "Based on the frame-by-frame observations below, provide overall coaching suggestions "
                "for general exercise technique and form:\n\n" + combined
            )}
        ]
        resp2 = client.chat.completions.create(
            model=VISION_MODEL,
            messages=advice_messages,
            temperature=0.2,
        )
        advice = resp2.choices[0].message.content.strip()
        st.header("📣 Coaching Suggestions")
        st.write(advice)
    else:
        st.info("No frames were processed—try adjusting the interval or use a clearer exercise video.")
