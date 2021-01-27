import os
import json
import pandas as pd
import numpy as np


# Load in data
def load_data():
    # Bootstrap Static Data
    # List files in data direcory
    file_list = os.listdir("ff\\data\\bootstrap_static")

    # Sort and select first (latest) data set
    file_list.sort()
    file_list = file_list[0]

    # Import data
    path = f'ff\\data\\bootstrap_static\\{file_list}'
    with open(path) as f:
        data = json.load(f)

    # Fixtures
    # List files in data direcory
    file_list = os.listdir("ff\\data\\fixtures")

    # Sort and select first (latest) data set
    file_list.sort()
    file_list = file_list[0]

    # Import data
    path = f'ff\\data/fixtures/{file_list}'
    with open(path) as f:
        fixtures = json.load(f)

    return data, fixtures

# Get team short names
def get_teams(data):
    teams = []
    for i in data['teams']:
        teams.append(i['short_name'])
    teams = tuple(teams)
    return teams


# Create look up for team IDs

# Create look up dict
def add_team_kpis(data):
    name_lookup = {}
    kpis_to_add = ['short_name',
                   'strength_overall_home',
                   'strength_overall_away',
                   'strength_attack_home',
                   'strength_attack_away',
                   'strength_defence_home',
                   'strength_defence_away']

    for j in kpis_to_add:
        for i in data['teams']:
            id = i['id']
            kpi_value = i[j]
            if id not in name_lookup.keys():
                name_lookup[id] = {}
            name_lookup[id][j] = kpi_value

    return name_lookup


# Add additional information to fixtures
def update_fixture_information(data, fixtures, custom_kpi):
    name_lookup = add_team_kpis(data)

    for i in fixtures:
        # Away team
        # Select away team ID
        team_a_id = i['team_a']

        # Add team short name
        kpi_key = 'short_name'
        kpi_name = 'team_a_short_name'
        kpi_value = name_lookup[team_a_id][kpi_key]
        i[kpi_name] = kpi_value

        # Add custom KPI
        kpi_name = 'team_h_custom_kpi'  # Note we are defining "h" here as this this will be the stats for the opponant
        i[kpi_name] = custom_kpi[kpi_value]

        # Add strength attack
        kpi_key = 'strength_attack_away'
        kpi_name = 'team_h_stength_attack'  # Note we are defining "h" here as this this will be the stats for the opponant
        kpi_value = name_lookup[team_a_id][kpi_key]
        i[kpi_name] = kpi_value

        # Add strength overall
        kpi_key = 'strength_overall_away'
        kpi_name = 'team_h_stength_overall'  # Note we are defining "h" here as this this will be the stats for the opponant
        kpi_value = name_lookup[team_a_id][kpi_key]
        i[kpi_name] = kpi_value

        # Home team
        team_h_id = i['team_h']

        # Add team short name
        kpi_key = 'short_name'
        kpi_name = 'team_h_short_name'
        kpi_value = name_lookup[team_h_id][kpi_key]
        i[kpi_name] = kpi_value

        # Add custom KPI
        kpi_name = 'team_a_custom_kpi'  # Note we are defining "h" here as this this will be the stats for the opponant
        i[kpi_name] = custom_kpi[kpi_value]

        # Add strength attack
        kpi_key = 'strength_attack_home'
        kpi_name = 'team_a_stength_attack'  # Note we are defining "h" here as this this will be the stats for the opponant
        kpi_value = name_lookup[team_h_id][kpi_key]
        i[kpi_name] = kpi_value

        # Add strength overall
        kpi_key = 'strength_overall_home'
        kpi_name = 'team_a_stength_overall'  # Note we are defining "h" here as this this will be the stats for the opponant
        kpi_value = name_lookup[team_h_id][kpi_key]
        i[kpi_name] = kpi_value

    return fixtures


def multi_gw_check(fix, team, gameweek):
    if gameweek in fix[team]:

        # Get list of gameweeks
        key_list = list(fix[team].keys())

        # get last gameweek key
        key = [k for k in key_list if gameweek == k or k.startswith(f'{gameweek}_')][-1]

        # Redfine new gameweek by appending an '_' and increment integer
        if '_' in key:
            new_key = int(key.rsplit('_', 1)[-1]) + 1
            gameweek_new = f'{gameweek}_{new_key}'

        else:
            gameweek_new = f'{gameweek}_2'

        return gameweek_new

    else:
        return gameweek


def reshape_fixtures(fixtures, kpi):
    fix = {}
    fix_name = {}
    for i in fixtures:
        gameweek = str(i['event'])

        # Skip if match not scheduled
        if gameweek == 'None':
            continue

        away_team = str(i['team_a_short_name'])

        if away_team not in fix:
            fix[away_team] = {}
            fix_name[away_team] = {}

        # check if double gameweek
        gameweek = multi_gw_check(fix, team=away_team, gameweek=gameweek)

        fix[away_team][gameweek] = i[f'team_a_{kpi}']
        fix_name[away_team][gameweek] = i[f'team_h_short_name']

        home_team = str(i['team_h_short_name'])

        if home_team not in fix:
            fix[home_team] = {}
            fix_name[home_team] = {}

        fix[home_team][gameweek] = i[f'team_h_{kpi}']
        fix_name[home_team][gameweek] = i[f'team_a_short_name']

    return fix, fix_name


def blank_gameweek_calc(fix,fix_name):
    # Identify max value for kpi
    max_val = 0
    for i in fix:
        for j in fix[i]:
            if fix[i][j] > max_val:
                max_val = fix[i][j]

    # ## Identify and fill missing game weeks

    # In[18]:

    bgw = []
    for i in fix:
        for j in range(1, 39):
            if str(j) not in fix[i]:
                fix[i][str(j)] = max_val
                bgw.append(str(j))
    bgw = list(set(bgw))
    bgw.sort()

    for i in fix_name:
        for j in range(1, 39):
            if str(j) not in fix_name[i]:
                fix_name[i][str(j)] = 'BGW'

    return fix, fix_name, bgw


# Identify multi gameweeks:
def multi_gw_id(fix):
    # ## Identify multi gameweeks

    # In[20]:

    mgw = []
    for i in fix:
        for j in fix[i]:
            if '_' in j:
                gw = j.rsplit('_', 1)[0]
                mgw.append(gw)

    mgw = list(set(mgw))
    mgw.sort()

    return mgw


# Merge multi gameweeks into one value
def multi_gameweek_weight(fix):
    for i in fix:
        key_list = list(fix[i].keys())
        for j in range(1, 39):
            keys = [k for k in key_list if str(j) == k or k.startswith(f'{str(j)}_')]
            if len(keys) <= 1:
                continue
            gameweek = keys[0]

            # Identify total kpi for the multi game week
            val = 0
            for k in keys:
                val += fix[i][k]

            # Average opponent
            val = val / len(keys)

            # Gameweek weighting
            val = val / len(keys)

            # Remove keys from dictionary
            for l in keys:
                del fix[i][l]

            fix[i][gameweek] = int(val)

    return fix


# Reshape data to identify complimenting fixtures
def fixture_calc(fix, start_gameweek, end_gameweek, mgw, exclude_gameweeks, skip_multi_gameweeks, skip_blank_gameweeks):
    df = pd.DataFrame(fix)
    df = df.reindex(sorted(df.columns), axis=1)
    df.index = pd.to_numeric(df.index, errors='coerce')

    # Remove required weeks
    # Create list of all gameweeks within range
    gameweeks = list(range(start_gameweek, end_gameweek + 1))
    gameweeks = [str(i) for i in gameweeks]

    if skip_multi_gameweeks:
        gameweeks = list(set(gameweeks) - set(mgw))
        gameweeks.sort()

    if skip_blank_gameweeks:
        gameweeks = list(set(gameweeks) - set(exclude_gameweeks))
        gameweeks.sort()

    # Remove specified gameweeks
    gameweeks = list(set(gameweeks) - set(exclude_gameweeks))
    gameweeks.sort()

    # Convert gameweeks to int
    gameweeks = [int(i) for i in gameweeks]
    gameweeks.sort()

    # Filter to only select required gameweeks
    df = df.loc[gameweeks].sort_index()

    # Calculate differences between teams

    fixture_pair = pd.DataFrame(columns=['TEAM_1', 'TEAM_2', 'VALUE'])

    for i in df.columns[0:]:
        for j in df.columns[0:]:
            value = df[[i, j]].min(axis=1).sum()
            fixture_pair.loc[len(fixture_pair)] = [i, j, value]

    # Remove cases comparing each team to itself
    fixture_pair = fixture_pair[fixture_pair['TEAM_1'] != fixture_pair['TEAM_2']]
    fixture_pair = fixture_pair.reset_index()

    # Remove Duplication
    fixture_pair[['TEAM_1', 'TEAM_2']] = pd.DataFrame(np.sort(fixture_pair[['TEAM_1', 'TEAM_2']].values))
    del fixture_pair['index']
    fixture_pair = fixture_pair.drop_duplicates()
    fixture_pair = fixture_pair.sort_values('VALUE')

    return fixture_pair


def prep_fixture_output(fix):
    for team in fix.keys():
        for gw in list(fix[team].keys())[::]:
            if len(gw.split('_')[0]) == 1:
                fix[team][f'0{gw}'] = fix[team][gw]
                del fix[team][gw]
    return fix


def compare_fixtures(fix,team1,team2):
    comp = {key: {f'{team1}': fix[team1].get(key, '-'), f'{team2}': fix[team2].get(key, '-')} for key in
           sorted(set(list(fix[team1].keys()) + list(fix[team2].keys())))}
    comp = dict(sorted(comp.items(), key=lambda t: t[0]))
    return comp


# Calculate complementing fixtures
def complimenting_fixtures_calc(kpi, custom_kpi, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
                                skip_blank_gameweeks):
    data, fixtures = load_data()
    fixtures_updated = update_fixture_information(data, fixtures, custom_kpi)
    fix, fix_name = reshape_fixtures(fixtures_updated, kpi)
    fix, fix_name, bgw = blank_gameweek_calc(fix, fix_name)

    fix_val = prep_fixture_output(fix)
    fix_name = prep_fixture_output(fix_name)

    mgw = multi_gw_id(fix)
    fix = multi_gameweek_weight(fix)
    fixture_pair = fixture_calc(fix, start_gameweek, end_gameweek, mgw, exclude_gameweeks, skip_multi_gameweeks,
                                skip_blank_gameweeks)

    return fixture_pair, fix_val, fix_name
#
#
# kpi = 'stength_overall'
# skip_multi_gameweeks = False
# skip_blank_gameweeks = False
# start_gameweek = 20
# end_gameweek = 35
# exclude_gameweeks = []
# # Exmaple custom KPI, goals scored last seasion (new teams given relgated teams values)
# custom_kpi = {
#     "ARS": 56,
#     "AVL": 41,
#     "BHA": 39,
#     "BUR": 43,
#     "CHE": 69,
#     "CRY": 31,
#     "EVE": 44,
#     "FUL": 26,
#     "LEE": 40,
#     "LEI": 67,
#     "LIV": 85,
#     "MCI": 102,
#     "MUN": 66,
#     "NEW": 38,
#     "SHU": 39,
#     "SOU": 51,
#     "TOT": 61,
#     "WBA": 36,
#     "WHU": 49,
#     "WOL": 51
# }
#
# complimenting_fixtures_calc(kpi, custom_kpi, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
#                             skip_blank_gameweeks)

