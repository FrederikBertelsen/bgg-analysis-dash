import dash
from dash import html, Input, Output, dcc

from backend.database.db import get_db_session
from backend.repositories.scrape_task_repository import ScrapeTaskRepository
from backend.utils import model_list_to_dataframe
import dash_bootstrap_components as dbc

dash.register_page(__name__)

app = dash.get_app()


def _fetch_tasks_df():
    with get_db_session() as session:
        tasks = ScrapeTaskRepository.get_all_tasks(session)
        df_tasks = model_list_to_dataframe(tasks)

    df_tasks = df_tasks[
        ["id", "name", "status", "progress", "last_update", "created_at"]
    ]

    df_tasks["progress"] = (df_tasks["progress"] * 100).round(0).astype(int).astype(
        str
    ) + "%"

    return df_tasks


layout = html.Div(
    children=[
        html.H1("Scraping"),
        html.H2("Scrape Tasks"),
        dcc.Interval(id="tasks-interval", interval=5000, n_intervals=0),
        html.Div(
            id="tasks-table-container",
            children=[
                dbc.Table.from_dataframe(  # type: ignore
                    _fetch_tasks_df(),
                    id="tasks-table",
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                )
            ],
        ),
        html.Div(id="dummy-output", style={"display": "none"}),
    ]
)

app.clientside_callback(
    """
    function(children) {
        const table = document.getElementById('tasks-table');
        if (!table) return '';
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(function(tr){
            tr.style.cursor = 'pointer';
            tr.onclick = function(){
                const idCell = tr.querySelector('td:first-child');
                const id = idCell && idCell.textContent.trim();
                if (id) window.open(`/task?id=${id}`, '_blank');
            };
        });
        return '';
    }
    """,
    Output("dummy-output", "children"),
    Input("tasks-table-container", "children"),
)
