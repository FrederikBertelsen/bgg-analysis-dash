import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc

from urllib.parse import parse_qs

from backend.database.db import get_db_session
from backend.repositories import BoardGameRepository
from backend.utils import model_list_to_dataframe

dash.register_page(__name__)


def _fetch_df_for_page(page: int = 1, per_page: int = 10):
    skip = (page - 1) * per_page

    with get_db_session() as session:
        boardgames = BoardGameRepository.get_some(session, skip=skip, take=per_page)
        df_boardgames = model_list_to_dataframe(boardgames)

    return df_boardgames


def layout(*args, **kwargs):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.H1("Boardgames"),
            html.Div(id="table-container"),
            html.Div(id="pagination-container", style={"marginTop": "1rem"}),
        ],
    )


@dash.callback(
    Output("table-container", "children"),
    Output("pagination-container", "children"),
    Input("url", "search"),
)
def render_table(query):
    qs = parse_qs(query.lstrip("?")) if query else {}
    page_str = qs.get("page", ["1"])[0]
    try:
        page = max(1, int(page_str))
    except ValueError:
        page = 1

    per_page = 10
    df = _fetch_df_for_page(page, per_page)

    if df is None or df.empty:
        table = html.Div("No data available")
    else:
        table = dbc.Table.from_dataframe(  # type: ignore
            df, striped=True, bordered=True, hover=True, responsive=True
        )

    prev_disabled = page <= 1
    prev_page = page - 1
    next_page = page + 1

    prev_link = dcc.Link(
        dbc.Button("Previous", color="primary", disabled=prev_disabled),
        href=f"?page={prev_page}",
    )
    next_link = dcc.Link(dbc.Button("Next", color="primary"), href=f"?page={next_page}")
    page_indicator = html.Span(f"Page {page}", style={"margin": "0 1rem"})

    pagination = html.Div([prev_link, page_indicator, next_link])

    return table, pagination
