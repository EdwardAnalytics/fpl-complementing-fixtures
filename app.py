import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, ALL, State
from ff.utility import functions

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Specficy gameweeks
gw = []
for i in range(1, 39):
    x = {}
    x['label'] = i
    x['value'] = i
    gw.append(x)

# Specify teams
data, fixtures = functions.load_data()
teams = functions.get_teams(data)

teams_list_all = [{'label': 'ALL', 'value': 'ALL'}]
for i in teams:
    teams_stage = {'label': i, 'value': i}
    teams_list_all.append(teams_stage)
teams_list=teams_list_all[1:]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.H5('KPI'),
    dcc.Dropdown(
        id='kpi-select',
        options=[
            {'label': 'Difficulty ', 'value': 'difficulty'},
            {'label': 'Strength Attack', 'value': 'stength_attack'},
            {'label': 'Strength Overall', 'value': 'stength_overall'},
            {'label': 'Custom', 'value': 'custom_kpi'}
        ],
        value='difficulty'
    ),

    html.Div(id='custom-kpi-text'),
    # Create Div to place a conditionally visible element inside
    html.Div(id = 'custom_kpi_holder', children = [
        dcc.Input(
            # id=f"input_{i}",
            id={
                'type': 'custom-kpi-value',
                'id': f'input_{i}'
            },
            type="number",
            placeholder=f"{i}"
        ) for i in teams

    ], style={'display': 'block', 'columnCount': 5}
        # <-- This is the line that will be changed by the dropdown callback
    ),


    html.Br(),
    html.H5('Select Gameweek Range'),
    dcc.RangeSlider(
        id='gw-select',
        count=1,
        min=1,
        max=38,
        step=1,
        value=[22, 35],
        marks={
            1: '1',
            5: '5',
            10: '10',
            15: '15',
            20: '20',
            25: '25',
            30: '30',
            35: '35',
            38: '38'
        }

    ),
    html.Br(),
    html.Div(id='gw-selected'),

    html.Br(),
    html.H5('Exclude Multi or Single Gameweeks'),
    dcc.Checklist(
        id = 'mgw-sgw',
        options=[
            {'label': 'Exclude Multi Gameweeks', 'value': 'MGW'},
            {'label': 'Exclude Single Gameweeks', 'value': 'SGW'}
        ],
        value=[],
        labelStyle={'display': 'inline-block'}
    ),

    html.Br(),
    html.H5('Exclude Specific Gameweeks'),
    dcc.Dropdown(
        id = 'exclude-specific-gws',
        options=gw,
        value=[],
        multi=True
    ),

    html.Br(),
    html.H5('Filter Output by Team'),
    dcc.Dropdown(
        id='team-filter',
        options=teams_list_all,
        value='ALL'
    ),

    html.Br(),
    html.H5('Select number of rows in output table'),
    dcc.Slider(
        id='table-limit',
        min=0,
        max=190,
        value=10,
        marks={
            1: '1',
            190: '190'
        }
    ),

    html.Br(),
    dcc.Loading(
        type="circle",
        children=[
            html.Div(className='pb-2 text-center m-auto', id='table-holder', children=[
                'Please select options'
            ])
        ],
    ),

    html.Br(),
    html.H5('Compare two teams fixtures'),
    dcc.Dropdown(
        id='team-fix-1',
        options=teams_list,
        value=teams[0]
    ),
    dcc.Dropdown(
        id='team-fix-2',
        options=teams_list,
        value=teams[1]
    ),

    html.Br(),
    dcc.Loading(
        type="circle",
        children=[
            html.Div(className='pb-2 text-center m-auto', id='table-holder-fix-name', children=[
                ''
            ])
        ],
    ),


], style={'columnCount': 1})


@app.callback(
    Output(component_id= 'custom_kpi_holder', component_property='style'),
    Input(component_id='kpi-select', component_property='value'))
def show_hide_element(kpi_select):
    if kpi_select == 'custom_kpi':
        return {'display': 'block', 'columnCount': 5}

    else:
        return {'display': 'none', 'columnCount': 5}


@app.callback(
    Output(component_id='custom-kpi-text', component_property='children'),
    Input(component_id='kpi-select', component_property='value')
)
def update_output(kpi_select):
    if kpi_select == 'custom_kpi':
        to_return = []
        to_return.append(html.Br())
        to_return.append(html.I(children=['Enter a value for each team']))
        return to_return
    else:
        return


@app.callback(
    Output(component_id='gw-selected', component_property='children'),
    Input(component_id='gw-select', component_property='value')
)
def update_output(value):
    return f'Gameweeks {str(value[0])} to {str(value[1])} selected'


@app.callback(
    Output(component_id='table-holder', component_property='children'),
    Output(component_id='table-holder-fix-name', component_property='children'),
    Input(component_id='kpi-select', component_property='value'),
    Input(component_id='mgw-sgw', component_property='value'),
    Input(component_id='exclude-specific-gws', component_property='value'),
    Input(component_id='gw-select', component_property='value'),
    Input(component_id='team-filter', component_property='value'),
    Input(component_id='table-limit', component_property='value'),
    Input(component_id='team-fix-1', component_property='value'),
    Input(component_id='team-fix-2', component_property='value')
)
def generate_table(kpi_selected,mgw_sgw,exclude_specific_gws,slider_vals,team_filter,table_limit,team_fix_1,team_fix_2):
    skip_multi_gameweeks = False
    if 'MGW' in mgw_sgw:
        skip_multi_gameweeks = True

    skip_blank_gameweeks = False
    if 'SGW' in mgw_sgw:
        skip_blank_gameweeks = True

    start_gameweek = slider_vals[0]
    end_gameweek = slider_vals[1]

    exclude_gameweeks = [str(i) for i in exclude_specific_gws]

    custom_kpi = {
            "ARS": 56,
            "AVL": 41,
            "BHA": 39,
            "BUR": 43,
            "CHE": 69,
            "CRY": 31,
            "EVE": 44,
            "FUL": 26,
            "LEE": 40,
            "LEI": 67,
            "LIV": 85,
            "MCI": 102,
            "MUN": 66,
            "NEW": 38,
            "SHU": 39,
            "SOU": 51,
            "TOT": 61,
            "WBA": 36,
            "WHU": 49,
            "WOL": 51
        }


    df, fix_val, fix_name = functions.complimenting_fixtures_calc(kpi_selected, custom_kpi, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
                                 skip_blank_gameweeks)

    if team_filter != 'ALL':
        df = df[(df['TEAM_1'] == team_filter) | (df['TEAM_2'] == team_filter)]

    # Limit table
    df = df.head(table_limit)

    fix_val = functions.compare_fixtures(fix=fix_val, team1=team_fix_1, team2=team_fix_2)
    fix_name = functions.compare_fixtures(fix=fix_name, team1=team_fix_1, team2=team_fix_2)

    print(f'{team_fix_1} Fixtures')

    return dash_table.DataTable(
        id='df',
        columns=[
            {"name": i, "id": i} for i in sorted(df.columns)
        ],
        data = df.to_dict(orient='records')
    ), dash_table.DataTable(
        id='df-fix-name',
        columns=[
            {"name": i, "id": i} for i in sorted(df.columns)
        ],
        data = fix_name
    )


if __name__ == '__main__':
    app.run_server(debug=True)
