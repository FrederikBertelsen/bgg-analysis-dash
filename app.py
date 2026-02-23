from dash import Dash

from backend.db import init_db
from frontend.page_container import app_layout

app = Dash(__name__, use_pages=True, health_endpoint='/health')

app.layout = app_layout()

# expose the underlying Flask server so WSGI servers (gunicorn) can find it
server = app.server

if __name__ == '__main__':
    init_db()
    
    app.run(debug=True, dev_tools_hot_reload=True)