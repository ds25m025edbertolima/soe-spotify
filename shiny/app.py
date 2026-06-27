import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Setup project paths

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
TRACKS_PATH = PROJECT_ROOT / "data" / "analytics" / "analytics_tracks.parquet"

sys.path.append(str(MODELS_DIR))

from recommender import load_recommender, recommend_selected_neighbors


# Page setup
st.set_page_config(
    page_title="Spotify Song Recommender",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 Spotify Song Recommender")
st.write("Listen to 10 songs, like or dislike them, and get personalized recommendations.")



# Load data and model
@st.cache_data
def load_tracks():
    df = pd.read_parquet(TRACKS_PATH)

    # Remove podcasts
    df = df[df["is_podcast"] == "no"].copy()

    # Keep only playable songs
    df = df[df["preview_url"].notna()].copy()
    df = df[df["preview_url"].astype(str).str.strip() != ""].copy()

    # Remove duplicate track IDs is any (should be since we did the cleaning but just in case)
    df = df.drop_duplicates(subset=["track_id"]).reset_index(drop=True)

    return df


@st.cache_resource
def load_model():
    scaler, knn, df_selected_features = load_recommender(models_dir=MODELS_DIR)
    return scaler, knn, df_selected_features


df_tracks = load_tracks()
scaler, knn, df_selected_features = load_model()

# Keep only tracks that exist in both the playable tracks data and the KNN feature matrix
available_track_ids = set(df_tracks["track_id"]).intersection(set(df_selected_features.index))
df_tracks = df_tracks[df_tracks["track_id"].isin(available_track_ids)].reset_index(drop=True)
df_selected_features = df_selected_features.loc[df_selected_features.index.isin(available_track_ids)]


def get_track_info(track_id):
    row = df_tracks[df_tracks["track_id"] == track_id].iloc[0]
    return row


def build_initial_rating_queue():
    """
    Select one random playable song.
    Then use KNN to find 9 similar songs.
    The first random song can later be liked or disliked by the user.
    """
    random_song = df_tracks.sample(1).iloc[0]
    random_track_id = random_song["track_id"]

    try:
        neighbors = recommend_selected_neighbors(
            liked_track_ids=[random_track_id],
            df_tracks=df_tracks,
            df_selected_features=df_selected_features,
            scaler=scaler,
            knn=knn,
            models_dir=MODELS_DIR,
            n_neighbors=9
        )

        queue = [random_track_id] + neighbors["track_id"].tolist()

    except Exception:
        # Fallback: if KNN fails, use 10 random playable songs
        queue = df_tracks.sample(10)["track_id"].tolist()

    # Make sure queue has exactly 10 unique songs
    queue = list(dict.fromkeys(queue))

    if len(queue) < 10:
        extra_needed = 10 - len(queue)
        extra_tracks = (
            df_tracks[~df_tracks["track_id"].isin(queue)]
            .sample(extra_needed)["track_id"]
            .tolist()
        )
        queue.extend(extra_tracks)

    return queue[:10]


def recommend_final_songs(liked_track_ids, disliked_track_ids, n_recommendations=10):
    """
    Recommend final songs based on liked songs.
    Disliked songs and already rated songs are excluded.
    """
    if len(liked_track_ids) == 0:
        return pd.DataFrame()

    rated_track_ids = set(liked_track_ids + disliked_track_ids)

    recs = recommend_selected_neighbors(
        liked_track_ids=liked_track_ids,
        df_tracks=df_tracks,
        df_selected_features=df_selected_features,
        scaler=scaler,
        knn=knn,
        models_dir=MODELS_DIR,
        n_neighbors=50
    )

    recs = recs[~recs["track_id"].isin(rated_track_ids)].copy()

    # Add preview_url and popularity for displaying
    display_cols = [
        "track_id",
        "track_name",
        "artist_name",
        "preview_url",
        "track_popularity",
        "artist_primary_genre_broad"
    ]

    recs = recs.merge(
        df_tracks[display_cols],
        on=["track_id", "track_name", "artist_name", "artist_primary_genre_broad"],
        how="left"
    )

    recs = recs[recs["preview_url"].notna()]
    recs = recs.drop_duplicates(subset=["track_id"])

    return recs.head(n_recommendations).reset_index(drop=True)


def reset_app():
    st.session_state.rating_queue = build_initial_rating_queue()
    st.session_state.current_index = 0
    st.session_state.liked_tracks = []
    st.session_state.disliked_tracks = []
    st.session_state.finished_rating = False
    st.session_state.final_recommendations = pd.DataFrame()


# Session state initialization
if "rating_queue" not in st.session_state:
    reset_app()



# Sidebar
st.sidebar.header("App Status")
st.sidebar.write(f"Songs loaded: {len(df_tracks):,}")
st.sidebar.write(f"Rated songs: {len(st.session_state.liked_tracks) + len(st.session_state.disliked_tracks)} / 10")
st.sidebar.write(f"Liked: {len(st.session_state.liked_tracks)}")
st.sidebar.write(f"Disliked: {len(st.session_state.disliked_tracks)}")

if st.sidebar.button("Restart App"):
    reset_app()
    st.rerun()


# Rating phase
if not st.session_state.finished_rating:

    current_index = st.session_state.current_index
    current_track_id = st.session_state.rating_queue[current_index]
    current_track = get_track_info(current_track_id)

    st.subheader(f"Song {current_index + 1} of 10")

    st.markdown(f"### {current_track['track_name']}")
    st.write(f"**Artist:** {current_track['artist_name']}")

    if pd.notna(current_track.get("artist_primary_genre_broad")):
        st.write(f"**Genre:** {current_track['artist_primary_genre_broad']}")

    st.audio(current_track["preview_url"])

    col1, col2 = st.columns(2)

    with col1:
        if st.button("👍 Like", use_container_width=True):
            st.session_state.liked_tracks.append(current_track_id)

            if st.session_state.current_index < 9:
                st.session_state.current_index += 1
            else:
                st.session_state.finished_rating = True

            st.rerun()

    with col2:
        if st.button("👎 Dislike", use_container_width=True):
            st.session_state.disliked_tracks.append(current_track_id)

            if st.session_state.current_index < 9:
                st.session_state.current_index += 1
            else:
                st.session_state.finished_rating = True

            st.rerun()

    st.progress((current_index + 1) / 10)



# Recommendation phase
else:
    st.subheader("Your Ratings Are Complete")

    liked_track_ids = st.session_state.liked_tracks
    disliked_track_ids = st.session_state.disliked_tracks

    st.write(f"You liked **{len(liked_track_ids)}** songs.")
    st.write(f"You disliked **{len(disliked_track_ids)}** songs.")

    if len(liked_track_ids) == 0:
        st.warning(
            "You disliked all 10 songs, so the app does not have enough positive preference information yet."
        )
        st.write(
            "For this first version, the recommender needs at least one liked song to build your music profile."
        )

        if st.button("Start Again"):
            reset_app()
            st.rerun()

    else:
        if st.session_state.final_recommendations.empty:
            st.session_state.final_recommendations = recommend_final_songs(
                liked_track_ids=liked_track_ids,
                disliked_track_ids=disliked_track_ids,
                n_recommendations=10
            )

        recommendations = st.session_state.final_recommendations

        st.markdown("## 🎵 Recommended Songs")

        if recommendations.empty:
            st.warning("No recommendations could be generated. Try restarting the app.")
        else:
            for i, row in recommendations.iterrows():
                st.markdown("---")
                st.markdown(f"### {i + 1}. {row['track_name']}")
                st.write(f"**Artist:** {row['artist_name']}")

                if pd.notna(row.get("artist_primary_genre_broad")):
                    st.write(f"**Genre:** {row['artist_primary_genre_broad']}")

                if "distance" in row:
                    st.write(f"**Distance:** {row['distance']:.3f}")

                st.audio(row["preview_url"])

        st.markdown("---")

        if st.button("Start New Recommendation"):
            reset_app()
            st.rerun()