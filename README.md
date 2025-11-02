# Amazon Review Sentiment Dashboard

A full-stack project that automates the collection, analysis, and visualization of **Amazon product review sentiment**.  
Built to demonstrate **data analysis, customer-first product thinking** and **engineering** skills — from web scraping and API design to dashboard analytics.

## Overview
This system:
- Extracts reviews from Amazon product pages via a **custom Chrome extension**
- Classifies sentiment (Positive / Neutral / Negative) using a **FastAPI backend**
- Aggregates and visualizes insights in an **interactive Streamlit dashboard**

<img width="1382" height="809" alt="image" src="https://github.com/user-attachments/assets/600d27f2-042e-49e8-8e34-b3309fdce623" />
<img width="1504" height="820" alt="image" src="https://github.com/user-attachments/assets/56df0d1f-b341-4731-93c6-22f73bc72d2b" />
<img width="1476" height="837" alt="image" src="https://github.com/user-attachments/assets/821ff7af-ac81-418f-9578-1d1bf0f7eadd" />

## Click on the amazon sentiment extension on chrome for quick analysis while shopping
<img width="900" height="700" alt="image" src="https://github.com/user-attachments/assets/bbce539f-8d12-49f2-9080-35adbc6bd786" />


## Live Demo
You can try out the project in two parts:

### 1. Sentiment Analysis API (Backend)
The FastAPI service is deployed on **Render**.

- **API Base URL:** [https://amazon-reviews-sentiment-analyser-backend.onrender.com/](https://amazon-reviews-sentiment-analyser-backend.onrender.com/)
- **Health Check:** [https://amazon-reviews-sentiment-analyser-backend.onrender.com/health](https://amazon-reviews-sentiment-analyser-backend.onrender.com/health)


### 2. Interactive Dashboard
The Streamlit dashboard visualizes live sentiment data collected from Amazon reviews.

- **SET API URL on the left sidebar to :  https://amazon-reviews-sentiment-analyser-backend.onrender.com/**

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
