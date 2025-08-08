import dash
from dash import html
from core.utils import load_roadmap
from ui.layout import make_figure, build_layout
from ui.callbacks import register_callbacks

# načti roadmapu (JSON → Pydantic → dict pro snadné použití v UI)
ROADMAP_PATH = "data/roadmap.json"
roadmap_model = load_roadmap(ROADMAP_PATH)
roadmap = roadmap_model.model_dump()   # pydantic v2 → dict

# postav obrázek a layout
fig = make_figure(roadmap)

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = build_layout(fig)

# napoj callbacky
register_callbacks(app, roadmap)
