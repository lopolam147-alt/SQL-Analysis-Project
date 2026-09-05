# Spotify SQL Analysis Project

An interactive data analysis dashboard for high-popularity Spotify tracks. The app stores cleaned track data in PostgreSQL, exposes a secured SQL execution API with Redis caching, and renders insights through an ECharts-powered web dashboard.

The dataset contains **1,437 high-popularity tracks** (primarily Western music from 2024), used to study release trends, genre patterns, audio features, and artist behavior — with recommendations aimed at new artists entering the market in 2025.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Database | PostgreSQL 15 (via Docker) |
| ORM | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/) |
| Caching | Redis 7 |
| Data Processing | Pandas |
| Frontend | Jinja2 templates + [Apache ECharts 5](https://echarts.apache.org/) |

---

## Project Structure

```
SQL_Analysis_Project/
├── main.py                  # FastAPI app, SQL API, page routing
├── models.py                # SQLAlchemy ORM model (SpotifyTrack)
├── database.py              # Database engine and session factory
├── csv_loader.py            # Import cleaned CSV into PostgreSQL
├── reset_database.py        # Drop and recreate all tables
├── requirements.txt         # Python dependencies
├── docker-compose.yml       # PostgreSQL + Redis services
├── spotify_cleaned.csv      # Cleaned dataset (output of data pipeline)
├── alembic/                 # Database migration scripts
│   └── versions/            # Schema evolution history
├── data/
│   ├── high_popularity_spotify_data.csv   # Raw source dataset
│   └── clean_spotify_data.py              # Data cleaning script
└── templates/
    └── Analysis.html        # Dashboard UI and chart SQL queries
```

---

## Features

### Interactive Dashboard
- **Release trends** — annual and monthly (2024) track counts
- **Artist analysis** — top collaborators, solo artists, top-10 artists (2023–2024)
- **Genre breakdown** — top genres across all data vs. recent years
- **Audio features** — tempo distribution, energy vs. popularity, liveness vs. popularity
- **Artist genre preferences** — grouped bar chart for top artists

### Secured SQL API (`POST /api/query/execute`)
- Only `SELECT` and `WITH` (CTE) queries are allowed
- Queries must reference the `spotify_tracks` table
- Blocks dangerous keywords: `DROP`, `TRUNCATE`, `UPDATE`, `DELETE`, `ALTER`, `INSERT`
- Results cached in Redis for 5 minutes (keyed by SQL hash)

### Data Pipeline
1. Raw CSV is cleaned with `data/clean_spotify_data.py` (deduplication, date normalization, outlier handling, genre assignment)
2. Output saved as `spotify_cleaned.csv`
3. `csv_loader.py` loads the cleaned file into PostgreSQL

---

## Database Schema

**Table: `spotify_tracks`**

| Column | Type | Description |
|---|---|---|
| `id` | Integer (PK) | Auto-increment primary key |
| `track_id` | String(50) | Unique Spotify track ID |
| `track_name` | String(255) | Track title |
| `track_artist` | String(255) | Artist(s), comma-separated |
| `track_album_name` | String(255) | Album name |
| `track_album_release_date` | Date | Normalized release date |
| `release_year` | Integer | Extracted release year |
| `release_month` | Integer | Extracted release month |
| `playlist_genre` | String(50) | Primary playlist genre |
| `playlist_subgenre` | String(50) | Playlist subgenre |
| `energy`, `tempo`, `danceability`, `loudness`, `liveness`, `valence`, `speechiness`, `acousticness`, `instrumentalness` | Numeric | Spotify audio features |
| `track_popularity` | Integer | Spotify popularity score |
| `duration_ms` | Integer | Track duration in milliseconds |
| `mode`, `key`, `time_signature` | Integer | Musical metadata |

---

## Getting Started

### Prerequisites
- Python 3.9+
- Docker and Docker Compose

### 1. Start infrastructure

```bash
docker-compose up -d
```

This starts:
- **PostgreSQL** on port `5434` (user: `lpl`, password: `lpl01470`, database: `spotify_db`)
- **Redis** on port `6379`

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize the database

Run these in order:

```bash
# Recreate table schema (type "yes" when prompted)
python reset_database.py

# Import cleaned CSV data
python csv_loader.py
```

Alternatively, use Alembic migrations:

```bash
python -m alembic upgrade head 
python csv_loader.py
```

### 4. (Optional) Regenerate cleaned data from raw CSV

If you need to re-run the data cleaning pipeline:

```bash
python data/clean_spotify_data.py
```

> **Note:** Update the input path in `clean_spotify_data.py` if your raw CSV is not at the hardcoded location. The raw file in this repo is at `data/high_popularity_spotify_data.csv`.

### 5. Start the application

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Open the dashboard at [http://localhost:8080](http://localhost:8080).

---

## API Usage

### Execute a SQL query

```http
POST /api/query/execute
Content-Type: application/json

{
  "sql": "SELECT playlist_genre, COUNT(*) FROM spotify_tracks GROUP BY playlist_genre ORDER BY COUNT(*) DESC LIMIT 5"
}
```

**Response:**

```json
{
  "columns": ["playlist_genre", "count"],
  "rows": [["pop", 275], ["rock", 198], ...]
}
```

---

## Key Insights (2023–2024)

- **Release timing:** High-popularity tracks cluster in **Autumn (Aug–Oct)**, making it the best release window.
- **Collaborations:** Top artists collaborate frequently (Bad Bunny, Peso Pluma, Feid lead with 7 each).
- **Genre shift:** Hip-Hop, Latin, and Gaming dominate recent charts, moving away from traditional Pop.
- **Tempo:** Most hits fall in the **120–140 BPM** range.
- **Production:** High-popularity tracks tend to have **low liveness** (studio-recorded) and **high energy**.
- **Opportunity:** Less saturated genres like Rock, R&B, and Punk may offer better entry points for new artists.

---

## Configuration

Database connection is defined in `database.py`:

```
postgresql+psycopg://lpl:lpl01470@localhost:5434/spotify_db
```

Redis connects to `localhost:6379` (configured in `main.py`).

For production, consider moving credentials to environment variables using `python-dotenv` (already listed in `requirements.txt`).

---

## Development Notes

- `main.py` includes optional startup hooks (`create_all` + `load_csv`) that are **commented out** by design — use `reset_database.py` and `csv_loader.py` manually to avoid wiping data on every restart.
- Artist names containing commas (e.g. "Tyler, The Creator") are normalized during cleaning to prevent incorrect splitting in SQL queries.
- The dashboard uses PostgreSQL-specific functions (`string_to_array`, `unnest`, window functions) for artist and genre analysis.

---

## License

This project is licensed under the [MIT License](LICENSE).

## Data Source 

- https://www.kaggle.com/datasets/solomonameh/spotify-music-dataset (just for high-popularity data)
