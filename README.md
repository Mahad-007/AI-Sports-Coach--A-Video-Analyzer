# 🎥 Sports Coaching Video Analyzer

An AI-powered sports coaching assistant that analyzes video frames and provides coaching feedback using Groq's Llama 3.3 70B model.

## 🚀 How to Run

### 1. Create a virtual environment in your project folder:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Set up your Groq API key:

Create a `.env` file in your project root and add:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from [https://console.groq.com/](https://console.groq.com/)

### 4. Launch the app:

```bash
streamlit run app.py
```

## 🎯 How it works

1. Upload any .mp4 sports video clip
2. The app extracts frames at specified intervals
3. Each frame is analyzed by Groq's AI model
4. Get AI-generated descriptions of what's happening
5. Receive coaching suggestions based on the analysis

## 🔧 Features

- **Video Frame Extraction**: Automatically extracts frames at configurable intervals
- **AI Analysis**: Uses Groq's Llama 3.3 70B model for intelligent frame analysis
- **Coaching Feedback**: Provides actionable coaching advice based on video content
- **Real-time Processing**: Shows results as frames are processed
- **Error Handling**: Robust error handling for API calls and video processing

## 📋 Requirements

- Python 3.7+
- Groq API key
- MP4 video files