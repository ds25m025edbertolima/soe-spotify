import streamlit as st
import pandas as pd
from pathlib import Path
import sys

#### Project paths

# The Streamlit app is stored inside the "shiny" folder.
# Path(__file__) points to the current app.py file.
# .resolve() converts it into the full absolute path.
# .parents[1] moves one folder up, from "shiny/" to the main project folder.
# goal is to access the path to the folder where the trained recommender model is stored and import the relevant functions
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"
TRACKS_PATH = PROJECT_ROOT / "data" / "analytics" / "analytics_tracks.parquet"

sys.path.append(str(MODELS_DIR))

from recommender import load_recommender, recommend_selected_neighbors


#### Page setup

st.set_page_config(
    page_title="Spotify Song Recommender",
    page_icon="🎧",
    layout="centered"
)

st.title("🎧 Spotify Song Recommender")
st.write("Listen to 10 songs, like or dislike them and get personalized recommendations.")


#### Load data and model

@st.cache_data # important to have since we do not want to reload the data every time a user presses like/dislike in the app. This tells the app I already loaded this data before, so I will reuse it.
def load_tracks():
    df = pd.read_parquet(TRACKS_PATH)

    # Remove podcasts
    df = df[df["is_podcast"] == "no"].copy()

    # Keep only playable songs
    df = df[df["preview_url"].notna()].copy()
    df = df[df["preview_url"].astype(str).str.strip() != ""].copy()

    # Remove duplicate track IDs if any (should not be since we already did the cleaning but just in case)
    df = df.drop_duplicates(subset=["track_id"]).reset_index(drop=True)

    # Extract release year from release_date (usefull for filtering)
    df["release_year"] = df["release_date"].astype(str).str[:4]
    df["release_year"] = pd.to_numeric(df["release_year"], errors="coerce")

    # Clean genre column for reliable filtering
    # For filtering artist_primary_genre_broad is taken into consideration
    df["genre_clean"] = (
        df["artist_primary_genre_broad"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return df

# Load the saved recommender components and cache them.
# @st.cache_resource tells Streamlit to load these objects only once and reuse them across reruns of the app.
#
# The function loads:
# - the fitted scaler used during model training,
# - the trained KNN recommender model,
# - and the selected features used by the recommender.
@st.cache_resource
def load_model():
    scaler, knn, df_selected_features = load_recommender(models_dir=MODELS_DIR)
    return scaler, knn, df_selected_features


df_tracks = load_tracks()
scaler, knn, df_selected_features = load_model()

# Find the track IDs that exist in both datasets:
# 1. df_tracks contains the playable song metadata
# 2. df_selected_features contains the audio feature matrix used by the KNN model indexed by track_id.
#
# The recommender can only work with songs that exist in both places since we also want to play the songs.
# Therefore, we take the intersection of both track_id lists.
available_track_ids = set(df_tracks["track_id"]).intersection(set(df_selected_features.index))
df_tracks = df_tracks[df_tracks["track_id"].isin(available_track_ids)].reset_index(drop=True)
df_selected_features = df_selected_features.loc[df_selected_features.index.isin(available_track_ids)]


# Get all information for one specific track.
# The function receives a track_id and searches df_tracks for the matching row.
#
# The returned row contains metadata such as track name, artist name, genre, release year and URL, which are later displayed in the app.
def get_track_info(track_id):
    row = df_tracks[df_tracks["track_id"] == track_id].iloc[0]
    return row


def build_initial_rating_queue(selected_genres=None, release_year_range=None):
    """
    Build the first 10 songs that the user will rate.
    The random first song is selected from the filtered pool.
    Then KNN finds similar songs and we filter those too.
    """

    candidate_pool = df_tracks.copy()

    # Clean selected genres
    selected_genres_clean = []
    if selected_genres:
        selected_genres_clean = [
            str(g).strip().lower()
            for g in selected_genres
        ]

    # Apply genre filter to initial song pool
    if selected_genres_clean:
        candidate_pool = candidate_pool[
            candidate_pool["genre_clean"].isin(selected_genres_clean)
        ].copy()

    # Apply release year filter to initial song pool
    if release_year_range is not None:
        candidate_pool = candidate_pool[
            candidate_pool["release_year"].between(
                release_year_range[0],
                release_year_range[1]
            )
        ].copy()

    # If filters are too strict, meaning if there are no songs left after applying the filters, return an empty list 
    if candidate_pool.empty:
        return []

    # Select first random song from filtered pool
    random_song = candidate_pool.sample(1).iloc[0]
    random_track_id = random_song["track_id"]

    try:
        neighbors = recommend_selected_neighbors(
            liked_track_ids=[random_track_id],
            df_tracks=df_tracks,
            df_selected_features=df_selected_features,
            scaler=scaler,
            knn=knn,
            models_dir=MODELS_DIR,
            n_neighbors=100
        )

        # Add genre_clean and release_year to neighbors
        neighbors = neighbors.merge(
            df_tracks[["track_id", "genre_clean", "release_year"]],
            on="track_id",
            how="left"
        )

        # Apply genre filter to KNN neighbors
        if selected_genres_clean:
            neighbors = neighbors[
                neighbors["genre_clean"].isin(selected_genres_clean)
            ].copy()

        # Apply release year filter to KNN neighbors
        if release_year_range is not None:
            neighbors = neighbors[
                neighbors["release_year"].between(
                    release_year_range[0],
                    release_year_range[1]
                )
            ].copy()

        queue = [random_track_id] + neighbors["track_id"].tolist()

    except Exception:
        queue = candidate_pool.sample(min(10, len(candidate_pool)))["track_id"].tolist()

    # Remove duplicates
    queue = list(dict.fromkeys(queue))

    # If fewer than 10 songs, fill with random songs from filtered pool
    # The KNN model may not always return enough songs after applying the genre/year filters. For example, the app starts with one random song and tries to add 9 KNN 
    # neighbors, but after filtering, maybe only 5 neighbors are left. Then the queue has only 6 songs total. To avoid this, we add random songs (not neighbours) from the filtered list
    if len(queue) < 10:
        extra_needed = 10 - len(queue)

        extra_pool = candidate_pool[
            ~candidate_pool["track_id"].isin(queue)
        ]

        if len(extra_pool) > 0:
            extra_tracks = (
                extra_pool
                .sample(min(extra_needed, len(extra_pool)))["track_id"]
                .tolist()
            )
            queue.extend(extra_tracks)

    return queue[:10]


def recommend_final_songs(
    liked_track_ids,
    disliked_track_ids,
    selected_genres=None,
    release_year_range=None,
    n_recommendations=10
):
    """
    Recommend final songs based on liked songs.
    Disliked songs are excluded.
    Genre and release year filters are applied.
    """

    if len(liked_track_ids) == 0:
        return pd.DataFrame()

    rated_track_ids = set(liked_track_ids + disliked_track_ids)

    # Get candidates 
    recs = recommend_selected_neighbors(
        liked_track_ids=liked_track_ids,
        df_tracks=df_tracks,
        df_selected_features=df_selected_features,
        scaler=scaler,
        knn=knn,
        models_dir=MODELS_DIR,
        n_neighbors=500
    )

    # Remove songs the user already rated
    recs = recs[~recs["track_id"].isin(rated_track_ids)].copy()

    # Add only columns that are not already returned by the recommender
    extra_cols = [
        "track_id",
        "preview_url",
        "track_popularity",
        "release_year",
        "genre_clean"
    ]

    recs = recs.merge(
        df_tracks[extra_cols],
        on="track_id",
        how="left"
    )

    # Keep only playable recommendations
    recs = recs[recs["preview_url"].notna()].copy()
    recs = recs[recs["preview_url"].astype(str).str.strip() != ""].copy()

    # Clean selected genres
    selected_genres_clean = []
    if selected_genres:
        selected_genres_clean = [
            str(g).strip().lower()
            for g in selected_genres
        ]

    # Apply genre filter 
    if selected_genres_clean:
        recs = recs[recs["genre_clean"].isin(selected_genres_clean)].copy()

    # Apply release year filter
    if release_year_range is not None:
        recs = recs[
            recs["release_year"].between(
                release_year_range[0],
                release_year_range[1]
            )
        ].copy()

    recs = recs.drop_duplicates(subset=["track_id"])

    return recs.sort_values("distance").head(n_recommendations).reset_index(drop=True)


def reset_app(selected_genres=None, release_year_range=None):
    st.session_state.rating_queue = build_initial_rating_queue(
        selected_genres=selected_genres,
        release_year_range=release_year_range
    )
    st.session_state.current_index = 0
    st.session_state.liked_tracks = []
    st.session_state.disliked_tracks = []
    st.session_state.finished_rating = False



#### Sidebar filters

st.sidebar.header("Recommendation Filters")

# Genre filter
available_genres = sorted(
    df_tracks["artist_primary_genre_broad"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

selected_genres = st.sidebar.multiselect(
    "Select genre(s)",
    options=available_genres,
    default=[]
)

# Release year filter
valid_years = df_tracks["release_year"].dropna()

if not valid_years.empty:
    min_year = int(valid_years.min())
    max_year = int(valid_years.max())

    release_year_range = st.sidebar.slider(
        "Release year range",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year),
        step=1
    )
else:
    release_year_range = None
    st.sidebar.warning("No valid release year values found.")


#### Basic session state initialization

# These variables must be initialized before they are shown in the sidebar.
# Otherwise Streamlit raises an error because liked_tracks or disliked_tracks
# do not exist yet.
if "liked_tracks" not in st.session_state:
    st.session_state.liked_tracks = []

if "disliked_tracks" not in st.session_state:
    st.session_state.disliked_tracks = []

if "current_index" not in st.session_state:
    st.session_state.current_index = 0

if "finished_rating" not in st.session_state:
    st.session_state.finished_rating = False


#### Rating queue initialization

# The rating queue depends on the selected genre and year filters.
# Therefore, it is created only after the filters exist.
if "rating_queue" not in st.session_state:
    reset_app(
        selected_genres=selected_genres,
        release_year_range=release_year_range
    )


#### Sidebar status

st.sidebar.header("App Status")

st.sidebar.write(f"Songs loaded: {len(df_tracks):,}")
st.sidebar.write(
    f"Rated songs: "
    f"{len(st.session_state.liked_tracks) + len(st.session_state.disliked_tracks)} / 10"
)
st.sidebar.write(f"Liked: {len(st.session_state.liked_tracks)}")
st.sidebar.write(f"Disliked: {len(st.session_state.disliked_tracks)}")

if st.sidebar.button("Start Recommender"):
    reset_app(
        selected_genres=selected_genres,
        release_year_range=release_year_range
    )
    st.rerun()


#### Rating phase

if not st.session_state.finished_rating:

    # Safety check in case the selected filters return no songs
    if len(st.session_state.rating_queue) == 0:
        st.warning(
            "No songs are available with the selected filters. "
            "Please choose a wider year range or fewer genre filters."
        )

        if st.button("Restart with new filters"):
            reset_app(
                selected_genres=selected_genres,
                release_year_range=release_year_range
            )
            st.rerun()

    else:
        current_index = st.session_state.current_index
        current_track_id = st.session_state.rating_queue[current_index]
        current_track = get_track_info(current_track_id)

        st.subheader(f"Song {current_index + 1} of 10")

        st.markdown(f"### {current_track['track_name']}")
        st.write(f"**Artist:** {current_track['artist_name']}")

        if pd.notna(current_track.get("artist_primary_genre_broad")):
            st.write(f"**Genre:** {current_track['artist_primary_genre_broad']}")

        if pd.notna(current_track.get("release_year")):
            st.write(f"**Release Year:** {int(current_track['release_year'])}")

        st.audio(current_track["preview_url"])

        col1, col2 = st.columns(2)

        with col1:
            if st.button("👍 Like", use_container_width=True):
                st.session_state.liked_tracks.append(current_track_id)

                if st.session_state.current_index < len(st.session_state.rating_queue) - 1:
                    st.session_state.current_index += 1
                else:
                    st.session_state.finished_rating = True

                st.rerun()

        with col2:
            if st.button("👎 Dislike", use_container_width=True):
                st.session_state.disliked_tracks.append(current_track_id)

                if st.session_state.current_index < len(st.session_state.rating_queue) - 1:
                    st.session_state.current_index += 1
                else:
                    st.session_state.finished_rating = True

                st.rerun()

        st.progress((current_index + 1) / len(st.session_state.rating_queue))


#### Recommendation phase

else:
    st.subheader("Your Ratings Are Complete")

    liked_track_ids = st.session_state.liked_tracks
    disliked_track_ids = st.session_state.disliked_tracks

    st.write(f"You liked **{len(liked_track_ids)}** songs.")
    st.write(f"You disliked **{len(disliked_track_ids)}** songs.")

    if len(liked_track_ids) == 0:
        st.warning(
            "You disliked all songs, so the app does not have enough positive preference information yet."
        )
        st.write(
            "For this first version, the recommender needs at least one liked song to build your music profile."
        )

        if st.button("Start Again"):
            reset_app(
                selected_genres=selected_genres,
                release_year_range=release_year_range
            )
            st.rerun()

    else:
        recommendations = recommend_final_songs(
            liked_track_ids=liked_track_ids,
            disliked_track_ids=disliked_track_ids,
            selected_genres=selected_genres,
            release_year_range=release_year_range,
            n_recommendations=10
        )

        st.markdown("## 🎵 Recommended Songs")

        if recommendations.empty:
            st.warning(
                "No recommendations could be generated with the selected filters. "
                "Try selecting a wider year range or fewer genre filters."
            )

            if st.button("Start Again"):
                reset_app(
                    selected_genres=selected_genres,
                    release_year_range=release_year_range
                )
                st.rerun()

        else:
            st.info(
                "The distance shows how close a recommended song is to the average sound "
                "profile of the songs you liked. A smaller distance means the song is more similar."
            )

            for i, row in recommendations.iterrows():
                st.markdown("---")
                st.markdown(f"### {i + 1}. {row['track_name']}")
                st.write(f"**Artist:** {row['artist_name']}")

                if pd.notna(row.get("artist_primary_genre_broad")):
                    st.write(f"**Genre:** {row['artist_primary_genre_broad']}")

                if pd.notna(row.get("release_year")):
                    st.write(f"**Release Year:** {int(row['release_year'])}")

                if "distance" in row and pd.notna(row["distance"]):
                    st.write(f"**Distance:** {row['distance']:.3f}")

                st.audio(row["preview_url"])

        st.markdown("---")

        if st.button("Start New Recommendation"):
            reset_app(
                selected_genres=selected_genres,
                release_year_range=release_year_range
            )
            st.rerun()