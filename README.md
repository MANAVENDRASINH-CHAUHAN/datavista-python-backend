# DataVista 🚀

DataVista is a full-stack data visualization and analysis platform.

## Features
- User Authentication (JWT)
- CSV Dataset Upload
- Dataset Records View
- Data Cleaning
- Data Insights
- Statistics & Analytics

## Tech Stack
### Frontend
- React + Vite

### Backend
- FastAPI (Python)
- MongoDB
- Pandas

## Setup

### Backend
```bash
cd backend-python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 5000
