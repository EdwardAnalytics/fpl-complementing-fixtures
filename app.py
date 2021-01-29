import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc #pip install dash-bootstrap-components
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, ALL, State
from dash.exceptions import PreventUpdate
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
teams_list = teams_list_all[1:]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Store(id='hidden-data',
              data={
              }
              ),
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
    html.Div(id='custom_kpi_holder', children=[
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
        value=[17, 21],
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
        id='mgw-sgw',
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
        id='exclude-specific-gws',
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
    )
    ,

    html.Br(),
    dcc.Loading(
        type="circle",
        children=[
            html.Div(className='pb-2 text-center m-auto', id='table-holder-fix', children=[
                ''
            ])
        ],
    ),
    html.Br(),
    dcc.Graph(id="line-chart")

], style={'columnCount': 1})


@app.callback(
    Output(component_id='custom_kpi_holder', component_property='style'),
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
    [Output(component_id='hidden-data', component_property='data'),
     Output(component_id='table-limit', component_property='value')],
    Input(component_id='kpi-select', component_property='value'),
    Input(component_id='mgw-sgw', component_property='value'),
    Input(component_id='exclude-specific-gws', component_property='value'),
    Input(component_id='gw-select', component_property='value'),
    Input(component_id='team-filter', component_property='value'),
    Input(component_id='team-fix-1', component_property='value'),
    Input(component_id='team-fix-2', component_property='value'),
    [State(component_id='hidden-data', component_property='data'),
     State(component_id='table-limit', component_property='value'), ]
)
def generate_table(kpi_selected, mgw_sgw, exclude_specific_gws, slider_vals, team_filter, team_fix_1, team_fix_2,
                   hidden_data, val):
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

    df, fix_val, fix_name, mgw, bgw, max_val, all_fixture_vals = functions.complimenting_fixtures_calc(kpi_selected, custom_kpi,
                                                                                start_gameweek, end_gameweek,
                                                                                exclude_gameweeks, skip_multi_gameweeks,
                                                                                skip_blank_gameweeks)

    if team_filter != 'ALL':
        df = df[(df['TEAM_1'] == team_filter) | (df['TEAM_2'] == team_filter)]


    hidden_data['fixtures_pair'] = df.to_json()
    hidden_data['kpi_selected'] = kpi_selected
    hidden_data['fix_val'] = fix_val
    hidden_data['fix_name'] = fix_name
    hidden_data['mgw'] = mgw
    hidden_data['bgw'] = bgw
    hidden_data['max_val'] = max_val
    hidden_data['skip_multi_gameweeks'] = skip_multi_gameweeks
    hidden_data['skip_blank_gameweeks'] = skip_blank_gameweeks
    hidden_data['start_gameweek'] = start_gameweek
    hidden_data['end_gameweek'] = end_gameweek
    hidden_data['exclude_gameweeks'] = exclude_gameweeks
    hidden_data['all_fixture_vals'] = all_fixture_vals.to_json()


    return hidden_data, val


@app.callback(
    Output(component_id='table-holder', component_property='children'),
    Input(component_id='table-limit', component_property='value'),
    [State(component_id='hidden-data', component_property='data')]
)
def select_column_row(table_limit, hidden_data):
    # but did we even click on anything??
    if dash.callback_context.triggered[0]['prop_id'] == '.':
        print('preventing update')
        raise PreventUpdate

    df = pd.read_json(hidden_data['fixtures_pair'])
    df = df.head(table_limit)
    return dash_table.DataTable(
        id='df',
        columns=[
            {"name": i, "id": i} for i in sorted(df.columns)
        ],
        data=df.to_dict(orient='records'),
        export_format="csv"
    )

@app.callback(
    Output(component_id='table-holder-fix', component_property='children'),
    Output(component_id="line-chart", component_property="figure"),
    Input(component_id='team-fix-1', component_property='value'),
    Input(component_id='team-fix-2', component_property='value'),
    [State(component_id='hidden-data', component_property='data')]
)
def generate_fixture_output(team1,team2, hidden_data):
    # but did we even click on anything??
    if dash.callback_context.triggered[0]['prop_id'] == '.':
        print('preventing update')
        raise PreventUpdate

    kpi_selected = hidden_data['kpi_selected']
    fix_val = hidden_data['fix_val']
    fix_name = hidden_data['fix_name']
    mgw = hidden_data['mgw']
    bgw = hidden_data['bgw']
    max_val = hidden_data['max_val']
    skip_multi_gameweeks = hidden_data['skip_multi_gameweeks']
    skip_blank_gameweeks = hidden_data['skip_blank_gameweeks']
    start_gameweek = hidden_data['start_gameweek']
    end_gameweek = hidden_data['end_gameweek']
    exclude_gameweeks = hidden_data['exclude_gameweeks']
    all_fixture_vals = pd.read_json(hidden_data['all_fixture_vals'])

    fix_name, fix_val = functions.prep_fixture_output(fix_name, fix_val, team1, team2, mgw, max_val)

    fix_name = functions.filter_fixtures(fix_name, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
                    skip_blank_gameweeks, mgw, bgw)
    fix_name = fix_name.replace('BGW', '-')

    fix_name_disct_cols = functions.rename_columns(fix_name.copy())


    # Populate graph
    graph_data = all_fixture_vals[[team1,team2]]

    # Add fixtures as hover data
    team1_hd, team2_hd = functions.generate_hover_data(fix_name.copy())
    graph_data['team1_hd'] = team1_hd
    graph_data['team2_hd'] = team2_hd

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=graph_data.index,
            y=graph_data[team1],
            text=graph_data['team1_hd'],
            name=team1
        ))
    fig.add_trace(
        go.Scatter(
            x=graph_data.index,
            y=graph_data[team2],
            text=graph_data['team2_hd'],
            name=team2
        ))
    fig.update_layout(legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
        xaxis=dict(
            title="Gameweek", tickformat='d'
        ),
        yaxis=dict(
            title=kpi_selected.replace('_', ' ').title()
        ))

    return dash_table.DataTable(
        id='df-fixtures',
        columns=[
            {"name": i, "id": i} for i in fix_name_disct_cols.columns
        ],
        data=fix_name_disct_cols.to_dict(orient='records'),
        export_format="csv"
    ),fig




if __name__ == '__main__':
    app.run_server(debug=True)
