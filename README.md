# JLR & Tata Motors — Vehicle Review Intelligence Hub

A dual-brand automotive customer review intelligence dashboard powered by AI sentiment analysis.

## Overview

This platform aggregates and analyses customer reviews, owner feedback, and expert opinions across:

- **JLR (Jaguar Land Rover)** — Jaguar, Range Rover, Defender, Discovery
- **Tata Motors** — Nexon EV, Punch EV, Curvv EV, Harrier EV, Safari, Tiago EV, Altroz, and more

## Features

- **Dual-brand switcher** — toggle between JLR (green/gold theme) and Tata Motors (blue/gold theme)
- **Live sentiment analysis** via Gemini AI — Positive / Neutral / Negative per review
- **Feed Explorer** — filter by brand group, review theme (Performance, EV Range, Comfort, etc.), platform
- **AI RAG Chat** — ask questions about any model, compare sentiment, surface top issues
- **Insights Tab** — trending terms, key issues, top praises, model sentiment breakdowns
- **Automated scraping** — Twitter/X, Reddit (r/landrover, r/jaguar, r/IndiaCars), AutoExpress, CarDekho

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Styling | Vanilla CSS (dark mode, dual brand themes) |
| AI Analysis | Google Gemini 1.5 Flash |
| Scraping | Twikit (Twitter), httpx (Reddit public JSON), Playwright (AutoExpress/CarDekho) |
| Database | SQLite (`diaspora.db`) |
| Deployment | Vercel (frontend) |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/lovingsarat/jlr-review.git
cd jlr-review
cd frontend && npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
- `GEMINI_API_KEY` — for backend sentiment analysis
- `VITE_GEMINI_API_KEY` — for frontend AI chat
- `TWITTER_AUTH_TOKEN` + `TWITTER_CT0` — for Twitter scraping (or use Bearer Token)

### 3. Run the scraper

```bash
cd backend
python -m pip install -r requirements.txt
playwright install chromium
python scraper.py
```

### 4. Export data to frontend

```bash
python export_data.py
```

### 5. Run frontend

```bash
cd frontend
npm run dev
```

## Data Schema

Each review item has:

| Field | Description |
|---|---|
| `brand` | `"jlr"` or `"tata"` |
| `city` | Brand group (e.g., `"Defender"`, `"EV"`) |
| `event` | Vehicle model (e.g., `"Defender 110"`, `"Nexon EV"`) |
| `sentiment` | `"Positive"` / `"Neutral"` / `"Negative"` |
| `category_tag` | Review theme (Performance, EV Range, Comfort, etc.) |
| `priority_score` | 1–5 AI-generated urgency score |
| `action_insight` | Actionable recommendation for the brand team |

## Scraping Sources

| Source | Brand | Method |
|---|---|---|
| Twitter/X | JLR + Tata | Twikit browser scraper / Bearer Token API |
| Reddit (r/landrover, r/jaguar, r/RangeRover, r/Defender) | JLR | Public JSON API |
| Reddit (r/IndiaCars, r/TataMotors) | Tata | Public JSON API |
| AutoExpress | JLR | Playwright |
| CarDekho | Tata | Playwright |

## License

MIT
