from urllib.parse import parse_qs

import dash
from dash import Input, Output, html, dcc
import dash_bootstrap_components as dbc

from backend.database.db import get_db_session
from backend.repositories.scrape_log_repository import ScrapeLogRepository
from backend.repositories.scrape_task_repository import ScrapeTaskRepository


dash.register_page(__name__)


layout = html.Div(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(id="task_info_container"),
    ]
)


@dash.callback(
    Output("task_info_container", "children"),
    Input("url", "search"),
)
def render_table(query):
    qs = parse_qs(query.lstrip("?")) if query else {}
    task_id_str = qs.get("id", ["1"])[0]

    if task_id_str is None:
        return html.Div("No task ID provided")
    elif not task_id_str.isdigit():
        return html.Div("Invalid task ID")

    task_id = int(task_id_str)

    with get_db_session() as session:
        task = ScrapeTaskRepository.get_by_id(session, task_id)

        if task is None:
            return html.Div(f"No task found with ID {task_id}")

        task_info = html.Div(
            [
                html.H2("Task Information"),
                html.P(f"ID: {task.id}"),
                html.P(f"Name: {task.name}"),
                html.P(f"Status: {task.status.value}"),
                html.P(f"Progress: {task.progress*100:.0f}%"),
                html.P(f"Current Page: {task.current_page}"),
                html.P(f"Items Processed: {task.items_processed}"),
                html.P(f"Message: {task.message}"),
                html.P(f"Created At: {task.created_at}"),
                html.P(f"Last Update: {task.last_update}"),
            ]
        )

        task_logs = ScrapeLogRepository.get_recent_logs(session, task_id)

        logs_str = "\n".join(f"{log.line_no}: {log.text}" for log in task_logs)

        return html.Div(
            [
                html.H1(f"{str(task.name)} ({task.status.value})"),
                task_info,
                html.Div(
                    [
                        html.H3("Recent Logs"),
                        html.P(
                            logs_str,
                            style={
                                "whiteSpace": "pre-wrap",
                                "fontFamily": "monospace",
                                "backgroundColor": "#f0f0f0",
                                "padding": "1rem",
                            },
                        ),
                    ],
                    style={"marginTop": "2rem"},
                ),
            ]
        )
