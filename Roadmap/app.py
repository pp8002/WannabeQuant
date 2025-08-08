import dash
from dash import html

# vytvoříme instanci aplikace a rovnou i server (hodí se pro deploy)
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # pro gunicorn / render apod.

# úplně základní layout – jen placeholder
app.layout = html.Div(
    [
        html.H1("WannabeQuant – Roadmap (Python/Dash)", style={"textAlign": "center"}),
        html.P(
            "Fáze 0: kostra projektu. Další kroky: data/, src/, UI, 3D graf…",
            style={"textAlign": "center", "opacity": 0.8},
        ),
    ],
    style={"maxWidth": "960px", "margin": "40px auto", "fontFamily": "system-ui"},
)
