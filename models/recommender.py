from pathlib import Path

def load_recommender(models_dir=None):
    models_dir = Path(models_dir or Path(__file__).parent)
    scaler = joblib.load(models_dir / "selected_audio_scaler.joblib")
    knn = joblib.load(models_dir / "selected_audio_knn.joblib")
    feature_matrix = pd.read_pickle(models_dir / "selected_audio_features.pkl")
    return scaler, knn, feature_matrix

def recommend_selected_neighbors(
    liked_track_ids,
    df_tracks,
    df_selected_features=None,
    scaler=None,
    knn=None,
    models_dir=None,
    n_neighbors=20,
):
    if isinstance(liked_track_ids, (str, int)):
        liked_track_ids = [liked_track_ids]

    if scaler is None or knn is None or df_selected_features is None:
        scaler, knn, df_selected_features = load_recommender(models_dir=models_dir)

    liked_track_ids = list(dict.fromkeys(liked_track_ids))
    missing = [tid for tid in liked_track_ids if tid not in df_selected_features.index]
    if missing:
        raise ValueError(f"Track ids not found in selected feature matrix: {missing}")

    liked_vectors = df_selected_features.loc[liked_track_ids].values
    centroid = liked_vectors.mean(axis=0).reshape(1, -1)
    scaled_centroid = scaler.transform(centroid)

    query_k = min(len(df_selected_features), n_neighbors + len(liked_track_ids) + 50)
    distances, indices = knn.kneighbors(scaled_centroid, n_neighbors=query_k)

    neighbor_ids = df_selected_features.index[indices[0]]
    recommendations = pd.DataFrame({"track_id": neighbor_ids, "distance": distances[0]})

    liked_meta = df_tracks.set_index("track_id").loc[liked_track_ids]
    liked_artists = set(liked_meta["artists_id"])
    liked_albums = set(liked_meta["album_id"])

    recommendations = recommendations[~recommendations["track_id"].isin(liked_track_ids)]
    recommendations = recommendations.merge(
        df_tracks[
            ["track_id", "artist_name", "artists_id", "album_id", "track_name", "artist_primary_genre_broad"]
        ],
        on="track_id",
        how="left",
    )
    recommendations = recommendations[
        ~recommendations["artists_id"].isin(liked_artists)
        & ~recommendations["album_id"].isin(liked_albums)
    ]
    return recommendations.sort_values("distance").head(n_neighbors).reset_index(drop=True)
