# Deadline Tracker

Deadline Tracker is an AI-powered academic assistant built with Streamlit and Google Gemini.

## Features

- Upload syllabus, timetable, or assignment images
- Extract academic deadlines and important instructions using Gemini Vision
- Ask questions about academic deadlines
- Send an email summary of identified deadlines using Gmail SMTP
- Handles unclear or missing deadlines without guessing

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- Gmail SMTP

## Run Locally

```bash
git clone https://github.com/manusri-v07/DeadlineTracker.git
cd DeadlineTracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py