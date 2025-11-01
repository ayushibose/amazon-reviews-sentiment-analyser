# Amazon Review Sentiment Dashboard

A full-stack project that automates the collection, analysis, and visualization of **Amazon product review sentiment**.  
Built to demonstrate **data analysis, customer-first product thinking** and **engineering** skills — from web scraping and API design to dashboard analytics.

---

## Overview
This system:
- Extracts reviews from Amazon product pages via a **custom Chrome extension**
- Classifies sentiment (Positive / Neutral / Negative) using a **FastAPI backend**
- Aggregates and visualizes insights in an **interactive Streamlit dashboard**

---

## My Role & Engineering Work
- **Designed and implemented** the FastAPI backend for data ingestion, storage, and analytics endpoints  
- **Integrated** a pretrained NLP model (`distilbert-base-uncased-finetuned-sst-2-english`) for sentiment classification  
- **Developed** a Chrome extension (JavaScript, Manifest V3) to capture and highlight review sentiment on Amazon pages  
- **Built** a Streamlit dashboard for interactive data visualization and trend analysis  
- **Handled data flow** between the extension, API, and dashboard with CORS, REST calls, and JSON payloads  

---

## Tech Stack
**Backend:** FastAPI · Transformers · PyTorch  
**Frontend / Extension:** JavaScript · Chart.js  
**Dashboard:** Streamlit · Pandas  
**Environment:** Python · Conda  

---

## Run Locally

### Setup
```bash
git clone https://github.com/yourusername/sentiment.git
cd sentiment
conda create -n sentiment python=3.10
conda activate sentiment
pip install -r requirements.txt

Start backend
cd backend
python app.py
uvicorn app:app --reload

Launch dashboard
streamlit run dashboard.py

Load the Chrome Extension
Go to chrome://extensions/
Enable Developer Mode
Click Load unpacked → select the extension/ folder
Visit an Amazon product page — review sentiments will appear as colored badges and be sent to the backend
