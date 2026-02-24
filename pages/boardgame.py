from urllib.parse import parse_qs

import dash
from dash import Input, Output, html, dcc
import dash_bootstrap_components as dbc

from backend.database.db import get_db_session
from backend.repositories.boardgame_repository import BoardGameRepository
from backend.repositories.clean_data_repository import CleanDataRepository
from backend.repositories.scrape_log_repository import ScrapeLogRepository
from backend.repositories.scrape_task_repository import ScrapeTaskRepository


dash.register_page(__name__)


def layout(*args, **kwargs):
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            html.Div(id="boardgame_info_container"),
        ]
    )


@dash.callback(
    Output("boardgame_info_container", "children"),
    Input("url", "search"),
)
def render_table(query):
    qs = parse_qs(query.lstrip("?")) if query else {}
    boardgame_id_str = qs.get("id", [""])[0]

    if boardgame_id_str is None:
        return html.Div("No boardgame ID provided")
    elif boardgame_id_str == "":
        return html.Div("Empty boardgame ID provided")
    elif not boardgame_id_str.isdigit():
        return html.Div("Invalid boardgame ID")

    boardgame_id = int(boardgame_id_str)

    with get_db_session() as session:
        boardgame = BoardGameRepository.get_by_id(session, boardgame_id)

        if boardgame is None:
            return html.Div(f"No boardgame found with ID {boardgame_id}")

        boardgame_data = CleanDataRepository.get_by_source_id_and_table(
            session, "boardgames", boardgame_id
        )

        if boardgame_data is None:
            return html.Div(
                f"No clean data found for boardgame '{boardgame.name}' (ID {boardgame_id})"
            )

        def _format_value(val):
            if val is None:
                return html.Span("—", className="text-muted")
            if isinstance(val, (list, tuple)):
                return html.Ul([html.Li(str(x)) for x in val], style={"margin": "0"})
            if isinstance(val, dict):
                return html.Div(
                    [html.Div([html.Strong(f"{k}: "), str(v)]) for k, v in val.items()]
                )
            if isinstance(val, float):
                return f"{val:,.2f}"
            return str(val)

        info_rows = []
        for key, value in boardgame_data.payload.items():
            display_key = key.replace("_", " ").title()
            info_rows.append(
                dbc.Row(
                    [
                        dbc.Col(html.Div(html.Strong(display_key)), width=2),
                        dbc.Col(html.Div(_format_value(value)), width=8),
                    ],
                    className="mb-2",
                )
            )

        card = dbc.Card(
            dbc.CardBody(
                [
                    html.H1(
                        f"Boardgame: {boardgame.name} (ID {boardgame.id})",
                        className="h4",
                    ),
                    html.H2("Cleaned Data:", className="h6 mt-3"),
                    dbc.Container(info_rows, fluid=True),
                ]
            ),
            className="mt-3",
        )

        return html.Div([card])
