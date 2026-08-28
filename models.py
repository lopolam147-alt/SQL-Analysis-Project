from sqlalchemy import Column, Integer, String, Date, Numeric
from database import Base

class SpotifyTrack(Base):
    __tablename__ = "spotify_tracks"
    ### Define the Spotify song data table structure for Object-relational mapping (ORM) mapping.
    # ORM: A programming technique that allows developers to interact with relational databases 
    # using objects and data structures from object-oriented programming languages.
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(String(50), unique=True, nullable=False)
    track_name = Column(String(255))
    track_artist = Column(String(255))
    track_album_name = Column(String(255))
    track_album_release_date = Column(Date)      
    release_year = Column(Integer)              # NEW ADD from clean_spotify_data.py
    release_month = Column(Integer)             # NEW ADD from clean_spotify_data.py
    playlist_genre = Column(String(50))
    playlist_subgenre = Column(String(50))
    
    energy = Column(Numeric(5,4))
    tempo = Column(Numeric(6,3))
    danceability = Column(Numeric(5,4))
    loudness = Column(Numeric(6,3))
    liveness = Column(Numeric(5,4))
    valence = Column(Numeric(5,4))
    speechiness = Column(Numeric(5,4))
    acousticness = Column(Numeric(5,4))
    instrumentalness = Column(Numeric(5,4))
    
    track_popularity = Column(Integer)
    duration_ms = Column(Integer)
    mode = Column(Integer)
    key = Column(Integer)
    time_signature = Column(Integer)
    
