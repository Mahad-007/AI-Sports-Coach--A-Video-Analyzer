import os
import tempfile
import cv2
from PIL import Image
import base64
import io

import streamlit as st
from dotenv import load_dotenv
import groq

# Load .env
load_dotenv()

# Initialize Groq client
client = groq.Groq(
    api_key=os.getenv("GROQ_API_KEY"),
)

st.set_page_config(page_title="Sports Coaching Analyzer", layout="wide")
st.title("🎥 Sports Coaching Video Analyzer (using Groq + OpenCV)")

video_file = st.file_uploader("Upload a video (.mp4)", type=["mp4"])
interval_sec = st.number_input("Frame interval (seconds)", min_value=1, max_value=10, value=3)

if video_file:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tfile.write(video_file.read())
    tfile.flush()

    cap = cv2.VideoCapture(tfile.name)
    if not cap.isOpened():
        st.error("Unable to open video.")
    else:
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        interval = max(1, int(fps * interval_sec))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / fps
        st.write(f"Video duration: {total:.1f}s — FPS: {fps:.2f}")

        summaries = []
        container = st.container()
        frame_idx = 0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % interval == 0:
                    ts = frame_idx / fps
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil = Image.fromarray(rgb)
                    container.image(pil, caption=f"Frame at {ts:.1f}s", use_container_width=True)

                    # Try image analysis first, fall back to text-based analysis
                    analysis_success = False
                    
                    # Method 1: Try with image data (if supported)
                    try:
                        # Convert image to base64
                        img_buffer = io.BytesIO()
                        pil.save(img_buffer, format="JPEG", quality=85)
                        img_str = base64.b64encode(img_buffer.getvalue()).decode()
                        
                        messages = [
                            {"role": "system", "content": "You are a sports coaching assistant. Analyze the image and describe what is happening in this frame from a sports video."},
                            {"role": "user", "content": f"Describe what is happening in this frame from a sports video. Image data: data:image/jpeg;base64,{img_str}"}
                        ]

                        resp = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            temperature=0.2,
                        )

                        caption = resp.choices[0].message.content.strip()
                        summaries.append((ts, caption))
                        container.markdown(f"**AI analysis:** {caption}")
                        analysis_success = True
                        
                    except Exception as e:
                        # If image analysis fails, try text-based analysis
                        st.warning(f"Image analysis failed, trying text-based analysis: {str(e)}")
                        
                        # Get basic frame information for text analysis
                        height, width = frame.shape[:2]
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        brightness = int(gray.mean())
                        
                        # Calculate some basic image statistics
                        contrast = int(gray.std())
                        
                        frame_description = f"Frame at {ts:.1f} seconds: {width}x{height} pixels, brightness {brightness}/255, contrast {contrast}"

                        messages = [
                            {"role": "system", "content": "You are a sports coaching assistant. Based on the frame description, analyze what might be happening in this sports video frame and provide insights."},
                            {"role": "user", "content": f"Analyze this frame from a sports video: {frame_description}. What might be happening in this frame? Provide sports coaching insights."}
                        ]

                        try:
                            resp = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=messages,
                                temperature=0.2,
                            )

                            caption = resp.choices[0].message.content.strip()
                            summaries.append((ts, caption))
                            container.markdown(f"**AI analysis (text-based):** {caption}")
                            analysis_success = True
                            
                        except Exception as e2:
                            st.error(f"Both image and text analysis failed: {str(e2)}")
                            summaries.append((ts, "Analysis failed"))

                    if not analysis_success:
                        summaries.append((ts, "Analysis failed"))

                frame_idx += 1

        finally:
            # Always release the video capture and clean up
            cap.release()
            # Close the temporary file
            tfile.close()
            # Try to delete the temporary file, but don't fail if it's still in use
            try:
                os.unlink(tfile.name)
            except (OSError, PermissionError):
                # File might still be in use, that's okay
                pass

        if summaries:
            st.header("📋 Summary")
            for t, c in summaries:
                st.write(f"- At {t:.1f}s: {c}")

            combined = "\n".join(c for _, c in summaries if c not in ["Error processing frame", "Analysis failed"])
            if combined:
                advice_messages = [
                    {"role": "system", "content": "You are a sports coaching assistant. Provide helpful coaching advice based on the video analysis."},
                    {"role": "user", "content": (
                        "Summarize the following observations into coaching advice:\n\n" + combined
                    )},
                ]
                
                try:
                    resp2 = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=advice_messages,
                        temperature=0.2,
                    )
                    advice = resp2.choices[0].message.content.strip()

                    st.header("📣 Coaching Suggestions")
                    st.write(advice)
                except Exception as e:
                    st.error(f"Error generating coaching advice: {str(e)}")
        else:
            st.info("No frames processed — try adjusting interval or checking the video file.")
