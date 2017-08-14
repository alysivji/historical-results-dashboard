# standard library
import os

# dash libs
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.figure_factory as ff
import plotly.graph_objs as go

# pydata stack
import pandas as pd
from sqlalchemy import create_engine

# set params
conn = create_engine(os.environ['DB_URI'])


###############
# Data Analysis
###############

def fetch_data(q):
    result = pd.read_sql(
        sql=q,
        con=conn
    )
    return result


def get_divisions():
    '''Returns the list of divisions that are stored in the database'''

    division_query = (
        f'''
        SELECT DISTINCT division
        FROM results
        '''
    )
    divisions = fetch_data(division_query)
    divisions = list(divisions['division'].sort_values(ascending=True))
    return divisions


def get_seasons(division):
    '''Returns the seasons of the datbase store'''

    seasons_query = (
        f'''
        SELECT DISTINCT season
        FROM results
        WHERE division='{division}'
        '''
    )
    seasons = fetch_data(seasons_query)
    seasons = list(seasons['season'].sort_values(ascending=False))
    return seasons


def get_teams(division, season):
    '''Returns all teams playing in the division in the season'''

    teams_query = (
        f'''
        SELECT DISTINCT team
        FROM results
        WHERE division='{division}'
        AND season='{season}'
        '''
    )
    teams = fetch_data(teams_query)
    teams = list(teams['team'].sort_values(ascending=True))
    return teams


def get_match_results(division, season, team):
    '''Returns match results for the selected prompts'''

    results_query = (
        f'''
        SELECT date, team, opponent, goals, goals_opp, result, points
        FROM results
        WHERE division='{division}'
        AND season='{season}'
        AND team='{team}'
        ORDER BY date ASC
        '''
    )
    match_results = fetch_data(results_query)
    return match_results


def calculate_season_summary(results):
    record = results.groupby(by=['result'])['team'].count()
    summary = pd.DataFrame(
        data={
            'W': record['W'],
            'L': record['L'],
            'D': record['D'],
            'Points': results['points'].sum()
        },
        columns=['W', 'D', 'L', 'Points'],
        index=results['team'].unique(),
    )
    return summary


##################
# Dashboard Layout
##################

def generate_table(dataframe, max_rows=10):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))]
    )


def onLoad_division_options():
    '''Actions to perform upon initial page load'''
    
    division_options = (
        [{'label': division, 'value': division}
         for division in get_divisions()]
    )
    return division_options


# Set up Dashboard and create layout
app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

app.layout = html.Div([

    # Page Header
    html.Div([
        html.H1('Soccer Results Viewer')
    ]),

    # Dropdown Grid
    html.Div([
        html.Div([
            # Select Division Dropdown
            html.Div([
                html.Div('Select Division', className='three columns'),
                html.Div(dcc.Dropdown(id='division-selector',
                                      options=onLoad_division_options()),
                         className='nine columns')
            ]),

            # Select Season Dropdown
            html.Div([
                html.Div('Select Season', className='three columns'),
                html.Div(dcc.Dropdown(id='season-selector'),
                         className='nine columns')
            ]),

            # Select Team Dropdown
            html.Div([
                html.Div('Select Team', className='three columns'),
                html.Div(dcc.Dropdown(id='team-selector'),
                         className='nine columns')
            ]),
        ], className='six columns'),

        # Empty
        html.Div(className='six columns'),
    ], className='twleve columns'),

    # Match Results Grid
    html.Div([

        # Match Results Table
        html.Div(
            html.Table(id='match-results'),
            className='six columns'
        ),

        # Season Summary Table and Graph
        html.Div([
            # summary table
            dcc.Graph(id='season-summary'),

            # graph
            dcc.Graph(id='season-graph')
            # style={},

        ], className='six columns')
    ]),
])


#############
# Interaction
#############

# Load Seasons in Dropdown
@app.callback(
    Output(component_id='season-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value')
    ]
)
def populate_season_selector(division):
    seasons = get_seasons(division)
    return [
        {'label': season, 'value': season}
        for season in seasons
    ]


# Load Teams into dropdown
@app.callback(
    Output(component_id='team-selector', component_property='options'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value')
    ]
)
def populate_team_selector(division, season):
    teams = get_teams(division, season)
    return [
        {'label': team, 'value': team}
        for team in teams
    ]


# Load Match results
@app.callback(
    Output(component_id='match-results', component_property='children'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value'),
        Input(component_id='team-selector', component_property='value')
    ]
)
def load_match_results(division, season, team):
    results = get_match_results(division, season, team)
    return generate_table(results, max_rows=50)


# Update Season Summary Table
@app.callback(
    Output(component_id='season-summary', component_property='figure'),
    [
        Input(component_id='division-selector', component_property='value'),
        Input(component_id='season-selector', component_property='value'),
        Input(component_id='team-selector', component_property='value')
    ]
)
def load_season_summary(division, season, team):
    results = get_match_results(division, season, team)

    table = []
    if len(results) > 0:
        summary = calculate_season_summary(results)
        table = ff.create_table(summary)

    return table


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
