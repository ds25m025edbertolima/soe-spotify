# Database Setup Guide

This project uses **PostgreSQL** via Supabase for data storage. Choose one of the setups below.

## Option 1: Local Development (PostgreSQL via Docker)

### Prerequisites
- Docker installed and running

### Setup

1. **Start PostgreSQL container:**
   ```bash
   docker run --name soe-spotify-db \
     -e POSTGRES_PASSWORD=postgres \
     -e POSTGRES_DB=soe_spotify \
     -p 5432:5432 \
     -d postgres:16
   ```

2. **Verify connection:**
   ```bash
   psql postgresql://postgres:postgres@localhost:5432/soe_spotify
   ```

3. **Create .env file:**
   ```bash
   cp .env.example .env
   # Leave DATABASE_URL as default (local Docker)
   ```

4. **Run ETL pipeline:**
   ```bash
   python -m soeSpotify.main
   ```

### Stop & Clean Up
```bash
docker stop soe-spotify-db
docker rm soe-spotify-db
```

---

## Option 2: Supabase Cloud (Production)

### Prerequisites
- Supabase account (free tier available at https://supabase.com)

### Setup

1. **Create Supabase project:**
   - Go to https://app.supabase.com
   - Click "New project"
   - Choose region closest to you
   - Set password (save it!)
   - Create project

2. **Get database URL:**
   - In Supabase dashboard, go to Settings → Database
   - Copy "Connection string" (select URI format)
   - Should look like: `postgresql://postgres:[PASSWORD]@[PROJECT-ID].supabase.co:5432/postgres`

3. **Create .env file:**
   ```bash
   cp .env.example .env
   ```

4. **Update .env with Supabase URL:**
   ```
   DATABASE_URL=postgresql://postgres:[YOUR_PASSWORD]@[YOUR_PROJECT].supabase.co:5432/postgres
   ```

5. **Install dependencies:**
   ```bash
   make requirements
   ```

6. **Run ETL pipeline:**
   ```bash
   python -m soeSpotify.main
   ```

### Verify in Supabase UI
- Dashboard → Tables
- Should see: `tracks`, `artists`, `albums` tables

---

## Option 3: Supabase Local Development

Use Supabase's local development environment:

```bash
# Install Supabase CLI
npm install -g supabase

# Initialize local Supabase
supabase init

# Start local instance
supabase start

# Stop local instance
supabase stop
```

---

## Database Schema

The ETL pipeline automatically creates three tables:

### artists
- `artist_id` (PRIMARY KEY)
- `artist_name`
- `popularity`
- `followers`
- `genres`
- `type`

### albums
- `album_id` (PRIMARY KEY)
- `album_name`
- `album_type`
- `artist_id`
- `release_date`
- `release_date_precision`
- `total_tracks`
- `uri`

### tracks
- `track_id` (PRIMARY KEY)
- Audio features (acousticness, danceability, energy, etc.)
- Lyrics features (mean_syllables_word, etc.)
- Metadata (popularity, duration_ms, explicit, etc.)
- References to artist and album

---

## Troubleshooting

### Connection refused
```
psycopg.OperationalError: could not connect to server
```
- **Local:** Ensure Docker container is running: `docker ps`
- **Supabase:** Check DATABASE_URL in .env is correct
- **Supabase:** Check firewall allows your IP (Settings → Network)

### Authentication failed
```
psycopg.OperationalError: FATAL: password authentication failed
```
- Verify password in DATABASE_URL matches Supabase project
- Check no extra spaces in DATABASE_URL

### Table already exists
```
psycopg.ProgrammingError: relation "tracks" already exists
```
- Tables are preserved between runs (ON CONFLICT handles updates)
- Use `--skip-delete` flag to avoid clearing tables first

---

## Quick Commands

```bash
# Run ETL (creates tables if needed, clears existing data)
python -m soeSpotify.main

# Run ETL without clearing tables
python -m soeSpotify.main --skip-delete

# Run ETL without loading to database
python -m soeSpotify.main --no-database

# Install/update dependencies
make requirements

# Format code with ruff
make format

# Check code with ruff
make lint
```
