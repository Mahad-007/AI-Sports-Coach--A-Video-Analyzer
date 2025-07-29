🧪 How to Run
Create a virtual environment in your project folder:

bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
Set your Groq API key:

bash
Copy
Edit
export GROQ_API_KEY="<your‑key>"
Launch the app:

bash
Copy
Edit
streamlit run app.py
Upload any .mp4 clip (e.g. a sports play), and the app will extract frames every few seconds, show them alongside AI-generated descriptions, and finally offer coaching feedback.