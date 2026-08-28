import pandas as pd
import re
from collections import Counter

df = pd.read_csv('d:\SQLproject\data\high_popularity_spotify_data.csv', encoding='utf-8')

print(f"Original number of data records: {len(df)}")
print(f"Original number of data columns: {len(df.columns)}")

# Because this .csv have some unuseful records (repeat columns, all records with same result), I choose some important columns
# Then, column part is also reordering to a suitable dataset order
main_cols = [
    'track_id', 'track_name', 'track_artist', 'track_album_name',
    'track_album_release_date', 'playlist_genre', 'playlist_subgenre',
    'energy', 'tempo', 'danceability', 'loudness', 'liveness',
    'valence', 'speechiness', 'acousticness', 'instrumentalness',
    'track_popularity', 'duration_ms', 'mode', 'key', 'time_signature'
]
df = df[main_cols]

# When completing dates that consist only of a year (e.g. 1976), 
# the year is supplemented using the month that appears most frequently for that year in the dataset,
# thereby bringing the date closer to the actual month of release.
# Add a "Month" column (1–12) to the cleaned data to facilitate aggregate analysis by month later.
def extract_year_month(date_str):
    """
    return: (year, month, has_month)
        - year: int OR None
        - month: int OR None (if just year --> None)
        - has_month: bool, 表示是否能确定月份
    """
    if pd.isna(date_str) or date_str == '':
        return None, None, False
    date_str = str(date_str).strip()
    # Format: YYYY-MM-DD
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
    if m:
        return int(m.group(1)), int(m.group(2)), True
    # Format: YYYY-MM
    m = re.match(r'^(\d{4})-(\d{2})$', date_str)
    if m:
        return int(m.group(1)), int(m.group(2)), True
    # Format: YYYY
    m = re.match(r'^(\d{4})$', date_str)
    if m:
        return int(m.group(1)), None, False
    # Other format: try to use pandas to solve 
    try:
        dt = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(dt):
            return dt.year, dt.month, True
    except:
        pass
    return None, None, False

# Extract no longer needed column part
df['_year'] = df['track_album_release_date'].apply(lambda x: extract_year_month(x)[0])
df['_month'] = df['track_album_release_date'].apply(lambda x: extract_year_month(x)[1])
df['_has_month'] = df['track_album_release_date'].apply(lambda x: extract_year_month(x)[2])

# Group by year and calculate the mode of the month.
year_month_counts = df[df['_has_month']].groupby('_year')['_month'].apply(
    lambda x: Counter(x).most_common(1)[0][0] if len(x) > 0 else None
)
# The month with the highest frequency of occurrence
global_mode_month = df[df['_has_month']]['_month'].mode()[0] if not df[df['_has_month']].empty else 1

# Returns the default month for the specified year 
# The month that appears most frequently in that year; if none, returns the global mode
def get_default_month(year):
    if year in year_month_counts.index and pd.notna(year_month_counts[year]):
        return int(year_month_counts[year])
    return global_mode_month

# Generate a standard date string (YYYY-MM-01) based on the year and month.
# If the month is not provided, use get_default_month() to supply it.
def build_date_str(year, month=None):
    if year is None:
        return None
    if month is None:
        month = get_default_month(year)
    month = int(month) if month else 1
    month = max(1, min(12, month))   
    return f"{year:04d}-{month:02d}-01"

# Apply date completion from build_date_str(year) and get_default_month(year)
df['track_album_release_date'] = df.apply(
    lambda row: build_date_str(row['_year'], row['_month']) if row['_has_month'] else build_date_str(row['_year'], None),
    axis=1
)

# Extract the year and month (for analysis later).
df['release_year'] = df['track_album_release_date'].apply(lambda x: int(x[:4]) if pd.notna(x) else None)
df['release_month'] = df['track_album_release_date'].apply(lambda x: int(x[5:7]) if pd.notna(x) else None)

# Convert to Pandas nullable integer type (allowing missing values)
df['release_year'] = df['release_year'].astype('Int64')
df['release_month'] = df['release_month'].astype('Int64')

# Delete the extract no longer needed column part
df.drop(['_year', '_month', '_has_month'], axis=1, inplace=True)

# Handle outliers for numeric types
numeric_cols = [
    'energy', 'tempo', 'danceability', 'loudness', 'liveness',
    'valence', 'speechiness', 'acousticness', 'instrumentalness',
    'track_popularity', 'duration_ms', 'mode', 'key', 'time_signature'
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Handle the mode of `playlist_genre`.
def assign_final_genre(group):
    # Select the genre with the highest frequency; in the event of a tie, choose the first one (or follow a priority order).
    mode_series = group['playlist_genre'].mode()
    return mode_series.iloc[0] if not mode_series.empty else group.iloc[0]['playlist_genre']

df['playlist_genre'] = df.groupby('track_id')['playlist_genre'].transform(lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0])

# Then removing duplicate 
df = df.drop_duplicates(subset=['track_id'], keep='first')
print(f"Number of records after removing duplicate data: {len(df)}")

# Numeric columns: Impute with the mean
for col in numeric_cols:
    if df[col].isna().sum() > 0:
        mean_val = df[col].mean()
        df[col] = df[col].fillna(mean_val)

# Categorical field: Fill with 'Unknown' for missing value, remove leading and trailing spaces
df['track_artist'] = df['track_artist'].fillna('Unknown')
df['track_artist'] = df['track_artist'].str.strip()
# Special protection: Replace "Tyler, The Creator" with "Tyler, The Creator|"
# (Add the '|' marker to prevent "Tyler" and "The Creator" from being incorrectly split when subsequently splitting by commas)
df['track_artist'] = df['track_artist'].str.replace('Tyler, The Creator', 'Tyler TheCreator', regex=False)

# Album Title (Fill in missing values)
df['track_album_name'] = df['track_album_name'].fillna('Unknown')

# Date-related columns: If there are still missing values ​​(very few), drop the rows.
df = df.dropna(subset=['track_album_release_date', 'release_year', 'release_month', 'release_quarter'])
print(f"Final number of records after handing missing value in some records: {len(df)}")

# Export the cleaned data
df.to_csv('spotify_cleaned.csv', index=False, encoding='utf-8')
print("✅ Save to 'spotify_cleaned.csv' after data cleaning")

## "docker exec -it spotify-postgres psql -U lpl -d spotify_db --> DROP TABLE IF EXISTS alembic_version;" remove all old version