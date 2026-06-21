def select_same_genre_neighbor(neighbors_df, liked_track_ids, df_tracks, genre_col='artist_primary_genre_broad'):
    if isinstance(liked_track_ids, (str, int)):
        liked_track_ids = [liked_track_ids]

    liked_track_ids = list(dict.fromkeys(liked_track_ids))
    missing = [tid for tid in liked_track_ids if tid not in df_tracks['track_id'].values]
    if missing:
        raise ValueError(f'Track ids not found in df_tracks: {missing}')

    liked_meta = df_tracks.set_index('track_id').loc[liked_track_ids]
    liked_genres = set(
        liked_meta[genre_col]
        .dropna()
        .astype(str)
        .tolist()
    )

    if not liked_genres:
        raise ValueError(
            f"No genre values found for liked tracks in column '{genre_col}'."
        )

    same_genre_neighbors = neighbors_df[
        neighbors_df[genre_col].isin(liked_genres)
    ].copy()

    if not same_genre_neighbors.empty:
        return same_genre_neighbors.sort_values('distance').head(1).reset_index(drop=True)

    return neighbors_df.sort_values('distance').head(1).reset_index(drop=True)
