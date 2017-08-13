# standard library
import os

# dash libs
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html

# pydata stack
import pandas as pd
from sqlalchemy import create_engine

# set params
conn = create_engine(os.environ['DB_URI'])


##########
# DB Query
##########
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
        '''
    )
    match_results = fetch_data(results_query)
    return match_results


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


# Set up Dashboard and create layout
app = dash.Dash()
app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

app.layout = html.Div([

    # Page Header
    html.Div([
        # Page Header
        html.H1('Soccer Results Viewer')
    ]),

    # Dropdown Grid
    html.Div([
        html.Div([
            # Select Division Dropdown
            html.Div([
                html.Div('Select Division', className='three columns'),
                html.Div(
                    dcc.Dropdown(
                        id='division-selector',
                        options=[{'label': division, 'value': division}
                                 for division in get_divisions()]
                    ), className='nine columns'
                )
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
        ], className='eight columns'),

        # Empty
        html.Div(className='four columns'),
    ]),

    # Match Results Table
    html.Div(
        html.Table(id='match-results'),
    ),
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
def populate_match_results(division, season, team):
    results = get_match_results(division, season, team)
    return generate_table(results, max_rows=50)


# start Flask server
if __name__ == '__main__':
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
