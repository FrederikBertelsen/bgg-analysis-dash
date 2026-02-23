from dash import Dash
import dash_bootstrap_components as dbc

from backend.db import get_db_session, init_db
from backend.repositories import BoardGameRepository
from frontend.page_container import app_layout

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    health_endpoint="/health",
)

app.layout = app_layout()

# expose the underlying Flask server so WSGI servers (gunicorn) can find it
server = app.server

if __name__ == "__main__":
    init_db()

    app.run(debug=True, dev_tools_hot_reload=True)
