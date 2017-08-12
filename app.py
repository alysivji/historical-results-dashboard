# standard library
import os

# dash libs
import dash
import dash_core_components as dcc
import dash_html_components as html

# pydata stack
import pandas as pd
from sqlalchemy import create_engine

# set params
conn = create_engine(os.environ['DB_URI'])


def fetch_data(q):
    result = pd.read_sql(
        sql=q,
        con=conn
    )
    return result


def get_divisions():
    '''Returns the list of divisions that are stored in the database'''

    division_query = (
        f'''SELECT DISTINCT division
        FROM results
        '''
    )
    divisions = fetch_data(division_query)
    divisions = list(divisions['division'].sort_values(ascending=True))
    return divisions


def get_seasons(division):
    '''Returns the years that are stored in the database
    '''

    seasons_query = (
        f'''SELECT DISTINCT season
        FROM results
        WHERE division='{division}'
        '''
    )
    seasons = fetch_data(seasons_query)
    seasons = list(seasons['season'].sort_values(ascending=False))
    return seasons


def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


# Set up Dashboard and create layout
app = dash.Dash()
app.layout = html.Div(children=[
    html.H1(children='US Agriculture Exports (2011)'),

    dcc.Dropdown(
        options=[
            {'label': division, 'value': division}
            for division in get_divisions()
        ]
    )
])

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})


if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
