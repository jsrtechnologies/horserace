# AusRace Predictor AI

A comprehensive horse racing prediction system for Australian races that scrapes data, stores it in a database, and uses machine learning to predict race outcomes.

## Project Structure

```
horseracing/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints/
│   │   │       ├── races.py
│   │   │       ├── predictions.py
│   │   │       └── scraping.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── database.py
│   │   │   └── schemas.py
│   │   ├── services/
│   │   │   ├── scraper/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_scraper.py
│   │   │   │   ├── racing_com_scraper.py
│   │   │   │   ├── punters_scraper.py
│   │   │   │   └── weather_api.py
│   │   │   ├── ml/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── feature_engineering.py
│   │   │   │   ├── model_trainer.py
│   │   │   │   └── predictor.py
│   │   │   └── prediction_service.py
│   │   ├── main.py
│   │   └── requirements.txt
│   └── venv/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── RaceCard.jsx
│   │   │   ├── PredictionTable.jsx
│   │   │   ├── WeatherWidget.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Races.jsx
│   │   │   ├── Predictions.jsx
│   │   │   └── Settings.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── data/
│   ├── racing_data.db
│   └── models/
│       └── horse_model.pkl
└── README.md
```

## Features

### 1. Web Scraper
- Scrapes data from multiple Australian horse racing sources
- Collects race information, horse details, jockey/trainer statistics
- Gathers weather and track condition data
- Automatic updates for upcoming races and results

### 2. Database
- SQLite for local development (easily migrated to PostgreSQL)
- Stores venues, meetings, races, horses, participants, and predictions
- Historical data for model training

### 3. Machine Learning
- XGBoost-based prediction model
- Features include:
  - Horse statistics (age, weight, form)
  - Jockey and trainer strike rates
  - Track conditions and weather
  - Distance suitability
  - Barrier draw analysis
- Automatic model retraining on new results

### 4. Web Dashboard
- React-based responsive UI
- Race meeting selector with date picker
- Prediction tables with confidence scores
- Weather and track condition widgets
- Real-time updates

## Setup

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r app/requirements.txt
python -m app.models.database  # Initialize database
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Races
- `GET /api/races` - List all races
- `GET /api/races/{race_id}` - Get race details
- `GET /api/races/meetings` - Get upcoming meetings

### Predictions
- `GET /api/predictions/{race_id}` - Get predictions for a race
- `POST /api/predictions/generate` - Generate predictions for a race

### Scraping
- `POST /api/scraping/scrape-races` - Trigger race scraping
- `POST /api/scraping/scrape-results` - Scrape latest results
- `POST /api/scraping/update-weather` - Update weather data

### Model
- `POST /api/model/train` - Train the prediction model
- `GET /api/model/stats` - Get model performance statistics

## Environment Variables

```
DATABASE_URL=sqlite:///./data/racing_data.db
WEATHER_API_KEY=your_weather_api_key
SCRAPING_INTERVAL_MINUTES=30
MODEL_RETRAIN_DAYS=7
```

## License

MIT License
