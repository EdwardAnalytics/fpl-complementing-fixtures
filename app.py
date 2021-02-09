import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc  # pip install dash-bootstrap-components
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output, ALL, State
from dash.exceptions import PreventUpdate
from utility import functions

external_stylesheets = [dbc.themes.BOOTSTRAP]

# Specify gameweeks for exclusion dropdown
gw = []
for i in range(1, 39):
    x = {'label': i, 'value': i}
    gw.append(x)

# Specify teams and load in data
data, fixtures = functions.load_data()
teams = functions.get_teams(data)


teams_list = []
for i in teams:
    teams_stage = {'label': i, 'value': i}
    teams_list.append(teams_stage)

# Get current gameweek:
current_gw = 38
for i in data['events']:
    if i['is_next']:
        current_gw = i['id']

end_gw = 35
if current_gw >= 35:
    end_gw = 38
if current_gw < 10:
    end_gw = 18

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

intro = html.Div(
    [
        dbc.Row([
            dbc.Col(html.H2(children=["FPL Tool | Complementing Fixtures"])),
            dbc.Col(children=[
                html.Div(children=[html.Img(src='assets/pwt.png', style={'max-height': '100%'})]
                         , style={'height': '50px', 'overflow': 'hidden', 'text-align': 'right'}
                         )
            ])
        ]
        ),
        dbc.Row(
            [
                dbc.Col(className='ml-3', children=[
                    html.H6('Definition of “complementing fixtures”'),
                    html.P(
                        'If two teams have complementing fixtures: this means when one has a difficult opponent, '
                        'the other has an easy opponent.'),
                    html.Br(),
                    html.H6('Example Application'),
                    html.P(
                        'If you have one player from each of two teams with complementing fixtures you can rotate '
                        'each week with one starting and one one your bench, starting whoever has the easier fixture. '
                        'This way you can potentially always have a position in your team who has an easy '
                        'opponent.'),
                    html.P(
                        "E.g. If you selected a player from Southampton and Brighton for the first 15 gameweeks of the "
                        "20/21 season, by rotating these players their opponents' would be: CRY, NEW, BUR, WBA, CRY, "
                        "WBA, AVL, NEW, AVL, MUN, BHA, SHU, FUL, SHU and FUL."),
                    html.Br(),
                    html.H6('Tips and Notes'),
                    html.P(
                        'If you still have your wildcard, only look up to gameweek 19 for the first half of the '
                        'season, and a few weeks off gameweek 38 if in the second half.'),
                    html.P(
                        'If know when you are using your freehit, exclude that specific game week from the calculation.'),
                    html.P(
                        'The value for multigameweeks is the average value for the team\'s opponent, divided by the '
                        'number of games the team has that week.'),
                    html.P(children=[
                        html.A(href='https://github.com/edwer-listl/ff-complementing-fixtures',
                               children='Link to GitHub repo.')
                    ]),
                    # html.P(children = [
                    #    html.A(href='https://www.shelter.org.uk/', children='Donate to UK housing and homelessness charity Shelter.')
                    # ])
                ])

                ,
            ]
        ),
    ]
)
store = dcc.Store(id='hidden-data',
                  data={
                  }
                  )

select_inputs = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(width=3, children=[
            html.H6('Select Measure to Minimise'),
            dcc.Dropdown(
                id='kpi-select',
                options=[
                    {'label': 'Difficulty ', 'value': 'difficulty'},
                    {'label': 'Strength Attack', 'value': 'stength_attack'},
                    {'label': 'Strength Overall', 'value': 'stength_overall'},
                    {'label': 'Custom', 'value': 'custom_kpi'}
                ],
                value='difficulty',
                clearable=False
            )
        ]),
        dbc.Col(children=[
            html.H6('Select Gameweek Range'),
            dcc.RangeSlider(
                id='gw-select',
                count=1,
                min=1,
                max=38,
                step=1,
                value=[current_gw, end_gw],
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
                }),
            html.I(id='gw-selected', style={'text-align': 'right'})])
    ]),
    dbc.Row(children=[
        dbc.Col(children=[
            html.Div(id='custom-kpi-text'),
            # Create Div to place a conditionally visible element inside
            html.Div(id='custom_kpi_holder', style={'display': 'block', 'columnCount': 5}, children=[
                dcc.Input(
                    id={
                        'type': 'custom-kpi-value',
                        'id': f'input_{i}'
                    },
                    type="number",
                    min=0,
                    max=1000000,
                    step=0.0000000001,
                    placeholder=f"{i}"
                ) for i in teams
            ])
        ])
    ])
])

exclusions = html.Div(
    [
        dbc.Row([
            dbc.Col(width=3, children=[html.H6('Exclusions'),
                                       dcc.Checklist(
                                           id='mgw-bgw',
                                           options=[
                                               {'label': ' Exclude Multi Gameweeks', 'value': 'MGW'},
                                               {'label': ' Exclude Blank Gameweeks', 'value': 'BGW'}
                                           ],
                                           value=[],
                                           labelStyle={'display': 'inline-block'}
                                       )]),
            dbc.Col(width=3, children=[html.H6('Exclude Specific Gameweeks'),
                                       dcc.Dropdown(
                                           id='exclude-specific-gws',
                                           options=gw,
                                           value=[],
                                           multi=True
                                       )])
        ]),
        dbc.Row(children=[html.Div(id='gw-exclusions')])
    ])

output = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(width=3, children=[
            html.H4('Team Pairs Ordered')
        ]),
        dbc.Col(width={'size': 1,
                       'offset': 8},
                children=[
                    dcc.Loading(
                        type="circle",
                        className='pt-5',
                        children=[
                            html.P(id='loading-spinner',
                                   children=[''
                                             ]
                                   )
                        ]
                    )
                ])
    ]),

    dbc.Row(children=[
        dbc.Col(width=4, children=[
            dcc.Loading(type="circle", children=[
                html.Div(id='table-holder', children=[
                    ''
                ]
                         )
            ])
        ]),
        dbc.Col(width=4, children=[
            html.H6('Select number of rows in output table'),
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
            html.H6('Filter Output by Team'),
            dcc.Dropdown(
                id='team-filter',
                options=teams_list,
                value='ALL'
            )
        ])

    ])
])

compare_fixtures = html.Div(children=[
    dbc.Row(children=[
        dbc.Col(width=5, children=[
            html.H4("Compare Two Teams' Fixtures")
        ]),
        dbc.Col(width={'size': 1,
                       'offset': 6},
                children=[
                    dcc.Loading(
                        type="circle",
                        className='pt-5',
                        children=[
                            html.P(id='loading-spinner-comp',
                                   children=[''
                                             ]
                                   )
                        ]
                    )
                ])

    ]),

    dbc.Row(children=[
        dbc.Col(width=3, children=[
            html.H6('Select two teams'),
            dcc.Dropdown(
                id='team-fix-1',
                options=teams_list,
                value=teams[0],
                clearable=False
            ),
            dcc.Dropdown(
                id='team-fix-2',
                options=teams_list,
                value=teams[1],
                clearable=False
            )
        ])
    ]),
    dbc.Row(children=[
        dbc.Col(children=[
            dcc.Loading(
                type="circle",
                className='pt-3',
                children=[
                    html.Div(className='pt-3', id='table-holder-fix', children=[
                        ''
                    ])
                ]
            )
        ])
    ]),
    dbc.Row(children=[
        dbc.Col(children=[
            dcc.Graph(id="line-chart")
        ])
    ])
])

app.title = 'FPL - Complimenting Fixtures'
app.layout = dbc.Container([

    store,
    intro,
    html.Hr(),
    select_inputs,
    exclusions,
    html.Hr(),
    output,
    html.Hr(),
    compare_fixtures,
])


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
        to_return = [html.I(children=['Enter a value for each team. E.g. goals per game this season'])]
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
     Output(component_id='table-limit', component_property='value'),
     Output(component_id='team-filter', component_property='value'),
     Output(component_id='loading-spinner', component_property='children'),
     Output(component_id='loading-spinner-comp', component_property='children'),
     Output(component_id='gw-exclusions', component_property='children')],
    Input(component_id='kpi-select', component_property='value'),
    Input(component_id='mgw-bgw', component_property='value'),
    Input(component_id='exclude-specific-gws', component_property='value'),
    Input(component_id='gw-select', component_property='value'),
    Input(component_id={'type': 'custom-kpi-value',
                        'id': ALL}, component_property='value'),
    [State(component_id='hidden-data', component_property='data'),
     State(component_id='table-limit', component_property='value'), ]
)
def generate_table(kpi_selected, mgw_bgw, exclude_specific_gws, slider_vals, custom_kpi_input,
                   hidden_data, val):
    # Only calculate if all values are submitted
    if None in custom_kpi_input and kpi_selected == 'custom_kpi':
        raise PreventUpdate

    skip_multi_gameweeks = False
    if 'MGW' in mgw_bgw:
        skip_multi_gameweeks = True

    skip_blank_gameweeks = False
    if 'BGW' in mgw_bgw:
        skip_blank_gameweeks = True

    start_gameweek = slider_vals[0]
    end_gameweek = slider_vals[1]

    exclude_gameweeks = [str(i) for i in exclude_specific_gws]

    # Set customer KPI dictionary
    for idx, item in enumerate(custom_kpi_input):
        if item == None:
            custom_kpi_input[idx] = 0
    custom_kpi = {}
    for i in range(0, 20):
        custom_kpi[teams[i]] = custom_kpi_input[i]

    df, fix_val, fix_name, mgw, bgw, max_val, all_fixture_vals = functions.complimenting_fixtures_calc(kpi_selected,
                                                                                                       custom_kpi,
                                                                                                       start_gameweek,
                                                                                                       end_gameweek,
                                                                                                       exclude_gameweeks,
                                                                                                       skip_multi_gameweeks,
                                                                                                       skip_blank_gameweeks)

    # if team_filter != 'ALL':
    #     df = df[(df['TEAM_1'] == team_filter) | (df['TEAM_2'] == team_filter)]

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

    # Print gameweeks removing
    all_gws_excluded = []
    if skip_blank_gameweeks:
        all_gws_excluded = all_gws_excluded + bgw

    if skip_multi_gameweeks:
        all_gws_excluded = all_gws_excluded + mgw

    all_gws_excluded = all_gws_excluded + exclude_specific_gws
    all_gws_excluded = [int(x) for x in all_gws_excluded]
    all_gws_excluded = list(set(all_gws_excluded))
    all_gws_excluded.sort()
    all_gws_excluded = [x for x in all_gws_excluded if x >= int(start_gameweek) and x <= int(end_gameweek)]
    if all_gws_excluded == []:
        gw_message = None
    else:
        gw_message = f'Excluding gameweeks: {all_gws_excluded}'.replace('[', '').replace(']', '')
        gw_message = html.I(children=[gw_message])

    return hidden_data, val, None, '', '', gw_message


@app.callback(
    Output(component_id='table-holder', component_property='children'),
    Input(component_id='table-limit', component_property='value'),
    Input(component_id='team-filter', component_property='value'),
    [State(component_id='hidden-data', component_property='data')]
)
def select_column_row(table_limit, team_filter, hidden_data):
    # but did we even click on anything??
    if dash.callback_context.triggered[0]['prop_id'] == '.':
        raise PreventUpdate
    df = pd.read_json(hidden_data['fixtures_pair'])

    if team_filter is None:
        df = df.head(table_limit)

    else:
        df = df[(df['TEAM_1'] == team_filter) | (df['TEAM_2'] == team_filter)]

    df.columns = ['Team 1', 'Team 2', 'Value']

    return dash_table.DataTable(
        id='df',
        columns=[
            {"name": i, "id": i} for i in sorted(df.columns)
        ],
        style_cell={'textAlign': 'center'},
        data=df.to_dict(orient='records'),
        export_format="csv"
    )


@app.callback(
    [Output(component_id='table-holder-fix', component_property='children'),
     Output(component_id="line-chart", component_property="figure")],
    Input(component_id='team-fix-1', component_property='value'),
    Input(component_id='team-fix-2', component_property='value'),
    Input(component_id='hidden-data', component_property='data')
)
def generate_fixture_output(team1, team2, hidden_data):
    # but did we even click on anything??
    if dash.callback_context.triggered[0]['prop_id'] == '.':
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

    fix_name = functions.filter_fixtures(fix_name, start_gameweek, end_gameweek, exclude_gameweeks,
                                         skip_multi_gameweeks,
                                         skip_blank_gameweeks, mgw, bgw)
    fix_name = fix_name.replace('BGW', '-')

    fix_name_disct_cols = functions.rename_columns(fix_name.copy())

    # Add index as first column with no column title
    col1 = [team1, team2, 'Best']
    fix_name_disct_cols.insert(0, '', col1)

    # Populate graph
    graph_data = all_fixture_vals[[team1, team2]]

    # Add fixtures as hover data
    team1_hd, team2_hd = functions.generate_hover_data(fix_name.copy())

    if team1 == 'MUN':
        team1_hd = [x.replace('TOT', "Lads it's TOT") for x in team1_hd]
    if team2 == 'MUN':
        team2_hd = [x.replace('TOT', "Lads it's TOT") for x in team2_hd]

    if team1 == 'BHA':
        team1_hd = [x.replace('CRY', "CRY - UTA!") for x in team1_hd]
    if team2 == 'BHA':
        team2_hd = [x.replace('CRY', "CRY - UTA!") for x in team2_hd]

    if team1 == 'CRY':
        team1_hd = [x.replace('BHA', "BHA - UTA!") for x in team1_hd]
    if team2 == 'CRY':
        team2_hd = [x.replace('BHA', "BHA - UTA!") for x in team2_hd]

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
    fig.update_layout(hovermode="x",
                      legend=dict(
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
        export_format="csv",
        style_data_conditional=[
            {
                'if': {'row_index': 2},
                'fontWeight': 'bold'
            }],
        style_cell={
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
            'maxWidth': 0,
            'textAlign': 'center'
        }

    ), fig


if __name__ == '__main__':
    app.run_server(debug=True)
