
from dash import html, dcc
import dash

def app_layout():
    return html.Div(className='container', children=[
    # navbar
    html.Div(className='navbar', children=[
        html.Div(className='links', children=[
            html.Div(
                dcc.Link(f"{page['name']}", href=page["relative_path"]) 
            ) for page in dash.page_registry.values()
        ]),
    ]),
    # page container
    dash.page_container
])