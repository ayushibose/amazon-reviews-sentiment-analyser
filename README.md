# Amazon Review Sentiment Dashboard

A full-stack project that automates the collection, analysis, and visualization of **Amazon product review sentiment**.  
Built to demonstrate **data analysis, customer-first product thinking** and **engineering** skills — from web scraping and API design to dashboard analytics.

## Overview
This system:
- Extracts reviews from Amazon product pages via a **custom Chrome extension**
- Classifies sentiment (Positive / Neutral / Negative) using a **FastAPI backend**
- Aggregates and visualizes insights in an **interactive Streamlit dashboard**

## Live Demo
You can try out the project in two parts:

### 1. Sentiment Analysis API (Backend)
The FastAPI service is deployed on **Render**.

- **API Base URL:** [https://amazon-reviews-sentiment-analyser-backend.onrender.com/](https://amazon-reviews-sentiment-analyser-backend.onrender.com/)
- **Health Check:** [https://amazon-reviews-sentiment-analyser-backend.onrender.com/health](https://amazon-reviews-sentiment-analyser-backend.onrender.com/health)


### 2. Interactive Dashboard
The Streamlit dashboard visualizes live sentiment data collected from Amazon reviews.

- **Live Dashboard:** [https://amazon-reviews-sentiment-analyser.onrender.com/](https://amazon-reviews-sentiment-analyser.onrender.com/)

If you visit the dashboard before ingesting reviews, it will show:
> _“No products ingested yet. Open some Amazon product pages with the extension running.”_

Once reviews are processed by the browser extension, they’ll appear here.


### 3. Chrome Extension (Data Ingestion)
The Chrome Extension captures live Amazon reviews and sends them to the backend API.


#### 👉 Installation Steps
**Download or clone** this repository:
   git clone https://github.com/ayushibose/amazon-reviews-sentiment-analyser.git

Open Chrome → go to chrome://extensions/

Enable Developer Mode

Click Load unpacked

Select the extension/ folder

Visit any Amazon product page — the extension will:

Highlight reviews by sentiment

Send results to the API

Update the dashboard automatically

---
## Run Locally

### Setup
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
