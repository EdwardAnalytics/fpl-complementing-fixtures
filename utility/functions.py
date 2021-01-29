import copy
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

    return fix, fix_name, bgw, max_val


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

    return fixture_pair, df


def prep_fixture_output_all(fix):
    for team in fix.keys():
        for gw in list(fix[team].keys())[::]:
            if len(gw.split('_')[0]) == 1:
                fix[team][f'0{gw}'] = fix[team][gw]
                del fix[team][gw]
    return fix


def compare_fixtures_name(fix,team1,team2):
    comp = {key: {f'{team1}': fix[team1].get(key, '-'), f'{team2}': fix[team2].get(key, '-')} for key in
           sorted(set(list(fix[team1].keys()) + list(fix[team2].keys())))}
    comp = dict(sorted(comp.items(), key=lambda t: t[0]))
    return comp


def compare_fixtures_val(fix,team1,team2,val):
    comp = {key: {f'{team1}': fix[team1].get(key, val), f'{team2}': fix[team2].get(key, val)} for key in
           sorted(set(list(fix[team1].keys()) + list(fix[team2].keys())))}
    comp = dict(sorted(comp.items(), key=lambda t: t[0]))
    return comp


def prep_fixture_output(fix_name, fix_val, team1, team2, mgw, max_val):
    # Filter fixtures
    df_name = compare_fixtures_name(fix_name, team1, team2)
    df_val = compare_fixtures_val(fix_val, team1, team2, max_val)

    # Add leading 0 to mgw list
    mgw_fix = [f'0{x}' if len(x) == 1 else x for x in mgw]

    # Append MGW flag
    for k, v in df_name.items():
        k_update = k
        if '_' in k:
            k_update = k.rsplit('_', 1)[0]
        if set([k_update]) <= set(mgw):
            df_name[k]['MGW'] = True

    # Append MGW flag
    for k, v in df_val.items():
        k_update = k
        if '_' in k:
            k_update = k.rsplit('_', 1)[0]
        if set([k_update]) <= set(mgw_fix):
            df_val[k]['MGW'] = True

    min_val = {}
    for k, v in df_val.items():
        if v[team1] < v[team2]:
            min_val[k] = team1
        else:
            min_val[k] = team2
        if 'MGW' in df_val[k]:
            k_update = k.rsplit('_', 1)[0]
            stg = {k2: v for k2, v in df_val.items() if k_update in k2}
            val_team1 = 0
            for k3, v in stg.items():
                val_team1 += v[team1]

            val_team2 = 0
            for k4, v in stg.items():
                val_team2 += v[team2]

            if val_team1 < val_team2:
                min_val[k] = team1
            else:
                min_val[k] = team2

    for k, v in df_name.items():
        v['BEST_OPPONENT'] = v[min_val[k]]

    for k in list(df_name):
        for j in list(df_name[k]):
            if j == 'MGW':
                df_name[k].pop('MGW', None)

    for k in list(df_val):
        for j in list(df_val[k]):
            if j == 'MGW':
                df_val[k].pop('MGW', None)

    df_name = pd.DataFrame.from_dict(df_name)
    df_val = pd.DataFrame.from_dict(df_val)

    return df_name, df_val


# Calculate complementing fixtures
def complimenting_fixtures_calc(kpi, custom_kpi, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
                                skip_blank_gameweeks):
    data, fixtures = load_data()
    fixtures_updated = update_fixture_information(data, fixtures, custom_kpi)
    fix, fix_name = reshape_fixtures(fixtures_updated, kpi)
    fix, fix_name, bgw, max_val = blank_gameweek_calc(fix, fix_name)


    fix_val = prep_fixture_output_all(copy.deepcopy(fix))
    fix_name = prep_fixture_output_all(fix_name)

    mgw = multi_gw_id(copy.deepcopy(fix))
    fix = multi_gameweek_weight(copy.deepcopy(fix))
    fixture_pair, all_fixture_vals = fixture_calc(copy.deepcopy(fix), start_gameweek, end_gameweek, mgw, exclude_gameweeks, skip_multi_gameweeks,
                                skip_blank_gameweeks)

    return fixture_pair, fix_val, fix_name, mgw, bgw, max_val, all_fixture_vals


def filter_fixtures(df, start_gameweek, end_gameweek, exclude_gameweeks, skip_multi_gameweeks,
                    skip_blank_gameweeks, mgw, bgw):
    # Add any missing gameweeks

    all_gw = list(map(str, range(1, 39)))
    for i in all_gw:
        if len(i) == 1:
            i = f'0{i}'
        if i not in df.columns:
            df[i] = ['-', '-', '-']
    df = df.reindex(sorted(df.columns), axis=1)

    cols = df.columns
    col_renamed = []
    for i in cols:
        new_name = i.rsplit('_', 1)[0]
        new_name = new_name.lstrip("0")
        col_renamed.append(new_name)

    df.columns = col_renamed

    if skip_multi_gameweeks:
        df = df.drop(mgw, axis=1, errors='ignore')

    if skip_blank_gameweeks:
        df = df.drop(bgw, axis=1, errors='ignore')

    df = df.drop(exclude_gameweeks, axis=1, errors='ignore')

    df = df[df.columns & list(map(str, range(start_gameweek, end_gameweek + 1)))]

    return df


def generate_hover_data(df):
    hover_data = {}
    for i in list(range(0, len(df.columns))):
        opp = df.iloc[0, i]
        if i != 0:
            if df.columns[i] == df.columns[i - 1]:
                opp_prv = df.iloc[0, i - 1]
                opp = f'{opp_prv}, {opp}'
                del hover_data[str(i - 1)]

        hover_data[str(i)] = opp

    team1 = list(hover_data.values())

    for i in list(range(0, len(df.columns))):
        opp = df.iloc[1, i]
        if i != 0:
            if df.columns[i] == df.columns[i - 1]:
                opp_prv = df.iloc[0, i - 1]
                opp = f'{opp_prv}, {opp}'
                del hover_data[str(i - 1)]

        hover_data[str(i)] = opp

    team2 = list(hover_data.values())

    return team1, team2


def rename_columns(df):
    cols = pd.Series(df.columns)

    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in
                                                         range(sum(cols == dup))]

    # rename the columns with the cols list.
    df.columns = cols

    return df
