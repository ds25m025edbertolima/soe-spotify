from shiny import App, ui, render, reactive

playlist = [
    "Dua Lipa - Levitating",
    "The Weeknd - Blinding Lights",
    "Taylor Swift - Anti-Hero",
    "Billie Eilish - Birds of a Feather",
    "Sabrina Carpenter - Espresso",
]

app_ui = ui.page_fluid(
    ui.h2("My Playlist"),
    ui.output_text("current_song"),
    ui.br(),
    ui.input_action_button("thumbs_up", "👍 Thumbs Up"),
    ui.input_action_button("thumbs_down", "👎 Thumbs Down"),
    ui.br(),
    ui.br(),
    ui.output_text("result"),
)

def server(input, output, session):
    song_index = reactive.Value(0)
    ratings = reactive.Value([])

    @output
    @render.text
    def current_song():
        index = song_index.get()

        if index >= len(playlist):
            return "You rated all songs!"

        return f"Now playing: {playlist[index]}"

    @reactive.effect
    @reactive.event(input.thumbs_up)
    def rate_up():
        index = song_index.get()

        if index < len(playlist):
            current_ratings = ratings.get()
            current_ratings.append((playlist[index], "👍"))
            ratings.set(current_ratings)
            song_index.set(index + 1)

    @reactive.effect
    @reactive.event(input.thumbs_down)
    def rate_down():
        index = song_index.get()

        if index < len(playlist):
            current_ratings = ratings.get()
            current_ratings.append((playlist[index], "👎"))
            ratings.set(current_ratings)
            song_index.set(index + 1)

    @output
    @render.text
    def result():
        current_ratings = ratings.get()

        if not current_ratings:
            return "No songs rated yet."

        text = "Your ratings:\n"
        for song, rating in current_ratings:
            text += f"{rating} {song}\n"

        return text

app = App(app_ui, server)