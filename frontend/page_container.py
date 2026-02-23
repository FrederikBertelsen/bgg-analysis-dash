from dash import html
import dash
import dash_bootstrap_components as dbc


def app_layout():
    # build nav items from registered pages
    nav_items = []
    for page in dash.page_registry.values():
        nav_items.append(
            dbc.NavItem(dbc.NavLink(page["name"], href=page["relative_path"]))
        )

    navbar = dbc.NavbarSimple(
        children=nav_items,
        brand=dbc.NavbarBrand("BGG Analysis"),
        brand_href="/",
        color="dark",
        dark=True,
    )

    return html.Div([navbar, dash.page_container])
