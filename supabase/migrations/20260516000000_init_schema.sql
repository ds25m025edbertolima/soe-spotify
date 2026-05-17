-- Create home schema
CREATE SCHEMA IF NOT EXISTS home;

-- 1. Artists Table
CREATE TABLE IF NOT EXISTS artists (
    artist_id TEXT PRIMARY KEY,
    artist_name TEXT,
    artist_popularity INTEGER,
    followers INTEGER,
    type TEXT,
    genres TEXT
);

-- 2. Albums Table
CREATE TABLE IF NOT EXISTS albums (
    album_id TEXT PRIMARY KEY,
    album_name TEXT,
    album_type TEXT,
    release_date TEXT,
    total_tracks INTEGER,
    uri TEXT,
    artist_id TEXT REFERENCES artists(artist_id),
    artist_name TEXT,
    artist_followers INTEGER,
    artist_popularity INTEGER
);

-- 3. Tracks Table
CREATE TABLE IF NOT EXISTS tracks (
    track_id TEXT PRIMARY KEY,
    track_name TEXT,
    track_popularity INTEGER,
    duration_ms INTEGER,
    preview_url TEXT,
    uri TEXT,
    album_id TEXT REFERENCES albums(album_id),
    album_name TEXT,
    album_type TEXT,
    release_date TEXT,
    artists_id TEXT REFERENCES artists(artist_id),
    artist_name TEXT,
    artist_popularity INTEGER,
    artist_followers INTEGER,
    genres TEXT,
    acousticness FLOAT,
    danceability FLOAT,
    energy FLOAT,
    instrumentalness FLOAT,
    key INTEGER,
    liveness FLOAT,
    loudness FLOAT,
    mode INTEGER,
    speechiness FLOAT,
    tempo FLOAT,
    time_signature INTEGER,
    valence FLOAT,
    mean_syllables_word FLOAT,
    mean_words_sentence FLOAT,
    n_sentences FLOAT,
    n_words FLOAT,
    sentence_similarity FLOAT,
    vocabulary_wealth FLOAT
);

-- 4. Genres Table
CREATE TABLE IF NOT EXISTS genres (
    id SERIAL PRIMARY KEY,
    artist_id TEXT REFERENCES artists(artist_id),
    artist_name TEXT,
    genre TEXT
);

-- 5. Track Features Table
CREATE TABLE IF NOT EXISTS track_features (
    track_id TEXT PRIMARY KEY REFERENCES tracks(track_id),
    acousticness FLOAT,
    danceability FLOAT,
    energy FLOAT,
    instrumentalness FLOAT,
    key INTEGER,
    liveness FLOAT,
    loudness FLOAT,
    mode INTEGER,
    speechiness FLOAT,
    tempo FLOAT,
    time_signature INTEGER,
    valence FLOAT,
    mean_syllables_word FLOAT,
    mean_words_sentence FLOAT,
    n_sentences FLOAT,
    n_words FLOAT,
    sentence_similarity FLOAT,
    vocabulary_wealth FLOAT
);

-- =============================================================================
-- BASE VIEWS (home schema)
-- =============================================================================

CREATE OR REPLACE VIEW home.artists AS SELECT * FROM public.artists;
CREATE OR REPLACE VIEW home.albums AS SELECT * FROM public.albums;
CREATE OR REPLACE VIEW home.tracks AS SELECT * FROM public.tracks;
CREATE OR REPLACE VIEW home.genres AS SELECT * FROM public.genres;
CREATE OR REPLACE VIEW home.track_features AS SELECT * FROM public.track_features;

-- =============================================================================
-- ANALYSIS VIEWS
-- =============================================================================

-- V_1_1: Total Artists
CREATE OR REPLACE VIEW home.v_1_1_total_artists AS
SELECT COUNT(*) as total_artists
FROM home.artists;

-- V_1_2: Artists by Popularity
CREATE OR REPLACE VIEW home.v_1_2_artists_popularity AS
SELECT artist_name,
       artist_popularity,
       followers
FROM home.artists
ORDER BY artist_popularity DESC;

-- V_1_3: Artists by Followers
CREATE OR REPLACE VIEW home.v_1_3_artists_followers AS
SELECT artist_name,
       followers,
       artist_popularity
FROM home.artists
ORDER BY followers DESC;

-- V_1_4: Artist Summary
CREATE OR REPLACE VIEW home.v_1_4_artist_summary AS
SELECT artist_name,
       artist_popularity,
       followers
FROM home.artists;

-- V_1_5: Artist-Album Relationships
CREATE OR REPLACE VIEW home.v_1_5_artist_albums AS
SELECT ar.artist_id,
       ar.artist_name,
       ar.followers as artist_followers,
       ar.artist_popularity,
       ab.album_id,
       ab.album_name,
       ab.release_date,
       ab.total_tracks,
       ab.album_type
FROM home.artists ar
LEFT JOIN home.albums ab ON ar.artist_id = ab.artist_id;

-- V_1_6: Artist-Genre Relationships
CREATE OR REPLACE VIEW home.v_1_6_artist_genres AS
SELECT ar.artist_name,
       ar.followers,
       ar.artist_popularity,
       ge.genre
FROM home.artists ar
JOIN home.genres ge ON ar.artist_id = ge.artist_id;

-- V_3_1: Track Features Full
CREATE OR REPLACE VIEW home.v_3_1_track_features_full AS
SELECT tr.track_id,
       tr.artist_name,
       tr.album_name,
       tr.track_name,
       tr.track_popularity,
       tf.danceability,
       tf.energy,
       tf.loudness,
       tf.speechiness,
       tf.acousticness,
       tf.instrumentalness,
       tr.liveness,
       tf.valence,
       tf.tempo,
       tr.duration_ms,
       tf.time_signature,
       tf.key,
       tf.mode
FROM home.tracks tr
LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;

-- V_1_7: Artist-Track Analysis
CREATE OR REPLACE VIEW home.v_1_7_artist_tracks AS
SELECT ar.artist_name,
       ar.followers,
       ar.artist_popularity,
       tr.track_id,
       tr.track_name,
       tr.track_popularity,
       tf.danceability,
       tf.energy,
       tf.tempo,
       tf.valence
FROM home.artists ar
LEFT JOIN home.tracks tr ON ar.artist_id = tr.artists_id
LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;

-- V_2_1: Album-Track Analysis
CREATE OR REPLACE VIEW home.v_2_1_album_tracks AS
SELECT ab.album_name,
       ab.release_date,
       ab.total_tracks,
       ab.album_type,
       ar.artist_name,
       tr.track_id,
       tr.track_name,
       tr.track_popularity,
       tf.danceability,
       tf.energy,
       tf.tempo,
       tf.valence
FROM home.albums ab
LEFT JOIN home.artists ar ON ab.artist_id = ar.artist_id
LEFT JOIN home.tracks tr ON ab.album_id = tr.album_id
LEFT JOIN home.track_features tf ON tr.track_id = tf.track_id;
