import pandas as pd
from sqlalchemy.orm import Session
from database import engine, SessionLocal
from models import SpotifyTrack
from sqlalchemy import text

def load_csv():
    try:
        # use cleaned version .csv after running clean_spotify_data.py
        df = pd.read_csv("spotify_cleaned.csv")
        df.to_sql('spotify_tracks', engine, if_exists='replace', index=False, method=None)
        print(f"CSV is completely imported to the PostgreSQL database with {len(df)} records。")
        # No rollback is needed, as `to_sql` handles it internally.
    except Exception as e:
        print(f"❌ Fail to import: {e}")
if __name__ == "__main__":
    load_csv()