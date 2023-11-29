import helperFunctions as hf
import helpPlayer as hp
import re
import pandas as pd
import time

teams = {
    'Boston Celtics' : 'BOS',
    'Philadelphia 76ers' : 'PHI',
    'New York Knicks' : 'NYK',
    'Brooklyn Nets' : 'BRK',
    'New Jersey Nets' : 'NJN',
    'Toronto Raptors' : 'TOR',
    'Milwaukee Bucks' : 'MIL',
    'Cleveland Cavaliers' : 'CLE',
    'Chicago Bulls' : 'CHI',
    'Indiana Pacers' : 'IND',
    'Detroit Pistons' : 'DET',
    'Atlanta Hawks' : 'ATL',
    'Miami Heat' : 'MIA',
    'Washington Wizards' : 'WAS',
    'Orlando Magic' : 'ORL',
    'Charlotte Hornets' : 'CHO',
    'Charlotte Bobcats' : 'CHA',
    'Charlotte Horns' : 'CHH',
    'Denver Nuggets' : 'DEN',
    'Minnesota Timberwolves' : 'MIN',
    'Oklahoma City Thunder' : 'OKC',
    'Seattle SuperSonics' : 'SEA',
    'Utah Jazz' : 'UTA',
    'Portland Trail Blazers' : 'POR',
    'Sacramento Kings' : 'SAC',
    'Phoneix Suns' : 'PHO',
    'Los Angeles Clippers' : 'LAC',
    'Los Angeles Lakers' : 'LAL',
    'Golden State Warriors' : 'GSW',
    'Memphis Grizzlies' : 'MEM',
    'New Orleans Pelicans' : 'NOP',
    'New Orleans Hornets' : 'NOH',
    'New Orleans/Oklahoma City Hornets' : 'NOK',
    'Dallas Mavericks' : 'DAL',
    'Houston Rockets' : 'HOU',
    'San Antonio Spurs' : 'SAS',
    'Multiple Teams' : 'TOT'
}

requests = 0

""" Collect team data
Record
Coach(es)
GM(s)
Offensive Rating
Defensive Rating
Net Rating
Playoffs
Championship
Runner-Up
Roster
FG%
3P%
2P%
FT%
eFG%
TOV%
ORB%
Opponent eFG%
Oponnent TOV% 
DRB%
Pace
WS Total
VORP Total
FG Pts Added
TS Pts Added
Total Payroll
Highest Draft Pick
# of Draft Picks
"""
def get_team_data(team, season):
    global requests

    url = 'https://www.basketball-reference.com/teams/' + team + '/' + season[season.find('-')+1:] + '.html'
    html = hf.get_soup(url)
    requests += 1
    check_requests()

    team_dict = {}
    team_dict['Team'] = team
    team_dict['Season'] = season

    meta = html.find(id='meta')
    roster = html.find(id='roster')
    stats = html.find(id='team_and_opponent')
    misc = html.find(id='team_misc')
    advanced = html.find(id='advanced')
    adj_shooting = html.find(id='adj_shooting')
    salaries = html.find(id='salaries2')

    team_dict.update(team_meta(meta))
    # team_dict.update(team_roster(roster))
    team_dict.update(team_stats(stats))
    team_dict.update(team_misc(misc))
    team_dict.update(team_advanced(advanced))
    team_dict.update(team_adj_shooting(adj_shooting))
    team_dict.update(team_salaries(salaries))

    url = 'https://www.basketball-reference.com/teams/' + team + '/' + season[season.find('-')+1:] + '_transactions.html'
    draft = hf.get_soup(url)
    requests += 1
    check_requests()
    
    team_draft(draft)
    team_dict.update(team_draft(draft))
    
    return team_dict

def team_meta(meta):
    meta = meta.findAll('p')

    meta_dict = {}


    meta_dict['Playoffs'] = False
    meta_dict['Champion'] = False
    meta_dict['RunnerUp'] = False
    for item in meta:
        item = item.getText().replace('\n','').replace(' ','')
        
        if 'Record' in item:
            record = item[item.find(':')+1: item.find(',')]
            wins = int(record[:record.find('-')])
            losses = int(record[record.find('-')+1:])
            meta_dict['Wins'] = wins
            meta_dict['Losses'] = losses
            meta_dict['Win%'] = (wins)/(wins+losses)
        if 'Coach' in item:
            coach = item[item.find(':')+1:].split(',')
            coach[:] = map(lambda x: re.sub(r'\([^)]*\)', '', x), coach)
            meta_dict['Coach(s)'] = coach
        if 'Executive' in item:
            exec = item[item.find(':')+1:].split(',')
            meta_dict['Exec(s)'] = exec
        if 'Playoffs' in item:
            meta_dict['Playoffs'] = True
            meta_dict['Champion'] = 'WonNBAFinals' in item
            meta_dict['RunnerUp'] = 'LostNBAFinals' in item

    return meta_dict

def team_roster(roster):
    roster_dict = {}

    roster_arr = []
    roster = roster.find('tbody').findAll('tr')

    for item in roster:
        roster_arr.append(item.find('td').getText())

    roster_dict['Roster'] = roster_arr
    return roster_dict

def team_stats(stats):
    stats_dict = {}

    stats = stats.find('tbody').findAll('tr')
    team_statline = stats[1].findAll('td')[2:]
    opponent_statline = stats[5].findAll('td')[2:]

    for item in team_statline:
        stat = item.get('data-stat').replace('_', ' ').replace('pct', '%').replace(' g', ' game').title()
        stat = stat[:stat.find(' ')].upper() + stat[stat.find(' '):]
        item = float(item.getText())

        stats_dict[stat] = item

    for item in opponent_statline:
        stat = item.get('data-stat').replace('_', ' ').replace('pct', '%').replace(' g', ' game').title()
        temp = stat[stat.find(' ')+1:]

        stat = stat[:stat.find(' ')+1] + temp[:temp.find(' ')].upper() + temp[temp.find(' '):]
        item = float(item.getText())
        stats_dict[stat] = item

    return stats_dict

def team_misc(misc):
    misc_dict = {}

    misc = misc.find('tbody').find('tr').findAll('td')
    off_rtg = 0
    def_rtg = 0

    for item in misc:
        stat = item.get('data-stat').replace('_', ' ').replace('pct', '%').title()
        if stat in ['Wins', 'Losses', 'Wins Pyth', 'Losses Pyth', 'Arena Name', 'Attendance']:
            continue
        
        if ' ' not in stat and stat != 'Pace':
            stat = stat.upper()
        elif '%' in stat and 'Opp' in stat:
            temp = stat[stat.find(' ')+1:]
            stat = stat[:stat.find(' ')+1] + temp[:temp.find(' ')].upper() + temp[temp.find(' '):]
        elif '%' in stat and 'Fga' not in stat:
            stat = stat[:stat.find(' ')].upper() + stat[stat.find(' '):]
        elif stat not in ['Pace', 'Off Rtg', 'Def Rtg']:
            if 'Opp' not in stat:
                stat = stat[:stat.find(' ')].upper() + stat[stat.find(' '):]
            if 'Fga' in stat:
                stat = stat[:stat.find('Fga')] + stat[stat.find('Fga'):].upper()
            if 'Ft' in stat:
                stat = stat[:stat.find('Ft')] + stat[stat.find('Ft'):stat.find('Ft')+2].upper() + stat[stat.find('Ft')+2:]
            
        item = float(item.getText())
        misc_dict[stat] = item
    
    misc_dict['Net Rtg'] = misc_dict['Off Rtg'] - misc_dict['Def Rtg']
    return misc_dict

def team_advanced(advanced):
    advanced_dict = {}

    ows_sum = 0
    dws_sum = 0
    ws_sum = 0
    obpm_sum = 0
    dbpm_sum = 0
    bpm_sum = 0
    vorp_sum = 0

    advanced = advanced.find('tbody').findAll('tr')

    for item in advanced:
        item = item.findAll('td')
        for stat in item:
            data = stat.getText()
            stat = stat.get('data-stat').upper()

            if stat == 'G' and int(data) < 30:
                break
            if stat == 'MP' and int(data) < 410:
                break
            if stat == 'OWS':
                ows_sum += float(data)
            elif stat == 'DWS':
                dws_sum += float(data)
            elif stat == 'WS':
                ws_sum += float(data)
            elif stat == 'OBPM':
                obpm_sum += float(data)
            elif stat == 'DBPM':
                dbpm_sum += float(data)
            elif stat == 'BPM':
                bpm_sum += float(data)
            elif stat == 'VORP':
                vorp_sum += float(data)

    advanced_dict['OWS'] = ows_sum
    advanced_dict['DWS'] = dws_sum
    advanced_dict['WS'] = ws_sum
    advanced_dict['OBPM'] = obpm_sum
    advanced_dict['DBPM'] = dbpm_sum
    advanced_dict['BPM'] = bpm_sum
    advanced_dict['VORP'] = vorp_sum
   
    return advanced_dict

def team_adj_shooting(adj_shooting):
    adj_shooting_dict = {}

    fg_add = 0
    ts_add = 0

    adj_shooting = adj_shooting.find('tbody').findAll('tr')
    
    for item in adj_shooting:
        item = item.findAll('td')
        games_played = int(item[2].getText())
        minutes_played = int(item[3].getText())
        if games_played < 30 or minutes_played < 410:
            continue

        fg_add += float(item[-2].getText())
        ts_add += float(item[-1].getText())

    # adj_shooting = adj_shooting.find('tfoot').find('tr').findAll('td')
    # fg_add = float(adj_shooting[-2].getText())
    # ts_add = float(adj_shooting[-1].getText())

    adj_shooting_dict['FG Pts Added'] = fg_add
    adj_shooting_dict['TS Pts Added'] = ts_add

    return adj_shooting_dict

def team_salaries(salaries):
    salaries_dict = {}

    salary_sum = 0
    salaries = salaries.find('tbody').findAll('tr')

    for item in salaries:
        item = item.findAll('td')[-1].getText().replace('$', '').replace(',', '')
        try:
            salary_sum += int(item)
        except:
            continue

    salaries_dict['Salary Total'] = salary_sum

    return salaries_dict

def team_draft(draft):
    draft_dict = {}

    picks = []
    draft = draft.findAll('p', {'class': 'transaction'})

    for item in draft:
        item = item.getText()
        if 'Drafted' not in item: 
            continue
        
        item = int(re.sub(r'[^0-9]', '',item[item.find('(')+1:item.find(')')]))
        picks.append(item)

    draft_dict['Highest Draft Pick'] = min(picks) if picks else 61
    draft_dict['# of DraftPicks'] = len(picks)
    # draft_dict['Draft Picks'] = picks

    return draft_dict

""" Fills player dictionary
Takes in dictionary of player
Fills their dictionary bio, stats, accolades, contract, etc
"""
def set_player_data(player):
    global requests
    check_requests()
    requests += 1
    html_doc = hf.get_soup('https://www.basketball-reference.com' + player['url'])
    
    # Setting Player Bio
    hp.set_bio(html_doc, player)

    # Setting Player Awards
    hp.set_awards(html_doc, player)

    # Setting Player Contract
    hp.set_contract(html_doc, player)

    # Setting Player Stats
    hp.set_stats(html_doc, player)

    return player

def check_requests():
    global requests
    # print(requests)
    if requests >= 18:
        print('\nPausing\n')
        time.sleep(60)
        requests = 0

# GET ALL TEAM DATA
def extend_team_data(start_year, end_year, file_to_save):
    global requests
    team_data = []
    years = end_year - start_year # 22 ==> end_year = 2023
    curr_season_start = start_year # start_year = 2001
    curr_season_end = start_year+1 # start_year + 1 = 2002

    for i in range(years):
        check_requests()
        curr_season = '{}-{}'.format(curr_season_start, curr_season_end)
        print('Year: {}\nSeason: {}'.format(i, curr_season))

        for team_abbrev in teams.values():
            
            if team_abbrev == 'TOT':
                continue
            if team_abbrev == 'BRK' and curr_season_start < 2012:
                continue
            if team_abbrev == 'NJN' and curr_season_start > 2012:
                continue
            if team_abbrev == 'CHO' and curr_season_start < 2014:
                continue
            if team_abbrev == 'CHA' and (curr_season_start < 2004 or curr_season_start > 2013):
                continue
            if team_abbrev == 'CHH' and curr_season_start > 2001:
                continue
            if team_abbrev == 'NOP' and curr_season_start < 2013:
                continue
            if team_abbrev == 'NOK' and (curr_season_start < 2005 or curr_season_start > 2006):
                continue
            if team_abbrev == 'NOH' and (curr_season_start < 2002 or curr_season_start > 2012):
                continue
            if team_abbrev == 'OKC' and curr_season_start < 2008:
                continue
            if team_abbrev == 'SEA' and curr_season_start > 2007:
                continue

            check_requests()

            requests += 2
            
            # try:
            print('Team: {}'.format(team_abbrev))
            team_data.append(get_team_data(team_abbrev, curr_season))
            # except:
            #     print('BAD BAD BAD {}'.format(team_abbrev))
            #     continue

        curr_season_start += 1
        curr_season_end += 1

    df = pd.DataFrame(team_data)
    df.to_csv(file_to_save) #new_data.csv

# GET DICTIONARY FROM TEAM DATA FOR EASY MANIPULATION
def team_data_to_dict(file_to_read, save_file=None, to_return=True):
    global requests
    df = pd.read_csv(file_to_read, index_col=0)
    d = df.to_dict('records')

    temp_dict = {}
    for hash in d:
        team_name = hash['Team']
        team_season = hash['Season']
        key = team_season + ':' + team_name
        temp_dict[key] = hash

    if save_file != None or not to_return:
        hf.save_data(save_file, temp_dict)
    else:
        return temp_dict

team_data = team_data_to_dict('NBA2022-2024Spreadsheet.csv', to_return=True)

for key in team_data.keys():
    check_requests()

    print(key)
    requests += 1
    url = 'https://www.basketball-reference.com/teams/' + key[key.find(':')+1:] + '/' + key[key.find('-')+1:key.find(':')] + '.html'
    html = hf.get_soup(url)
    roster = html.find(id='roster')
    meta = html.find(id='meta') 

    team_data[key].update(team_meta(meta))
    team_data[key].update(team_roster(roster))


# ADD OFFSEASON CHANGES

# team_data = hf.retrieve_data('dict_data.txt')
player_data = hf.retrieve_data('biggy_data.txt')

for team_abbrev in teams.values():
    # if team_abbrev in ['BOS', 'PHI', 'NYK', 'BRK', 'NJN', 'TOR', 
    #                    'MIL', 'CLE', 'CHI', 'IND', 'DET', 
    #                    'ATL', 'MIA', 'WAS', 'ORL', 'CHO', 'CHA', 'CHH',
    #                    'DEN', 'MIN', 'OKC', 'SEA', 'UTA', 'POR',
    #                    'SAC', 'PHO', 'LAC', 'LAL', 'GSW',
    #                    'MEM', 'VAN', 'NOP', 'NOH', 'NOK', 'DAL', 'HOU', 'SAS']:
    #     continue
    
    for curr_year in range(2024, 2022, -1): #range(2023,2001,-1)

        if team_abbrev == 'TOT':
            continue
        if team_abbrev == 'BRK' and curr_year-1 < 2012:
            continue
        if team_abbrev == 'NJN' and curr_year-1 > 2012:
            continue
        if team_abbrev == 'CHO' and curr_year-1 < 2014:
            continue
        if team_abbrev == 'CHA' and (curr_year-1 < 2004 or curr_year-1 > 2013):
            continue
        if team_abbrev == 'CHH' and curr_year-1 > 2001:
            continue
        if team_abbrev == 'NOP' and curr_year-1 < 2013:
            continue
        if team_abbrev == 'NOK' and (curr_year-1 < 2005 or curr_year-1 > 2006):
            continue
        if team_abbrev == 'NOH' and (curr_year-1 < 2002 or curr_year-1 > 2012):
            continue
        if team_abbrev == 'OKC' and curr_year-1 < 2008:
            continue
        if team_abbrev == 'SEA' and curr_year-1 > 2007:
            continue

        curr_season = f'{curr_year-1}-{curr_year}'
        prev_season = f'{curr_year-2}-{curr_year-1}'
        
        key = f'{curr_season}:{team_abbrev}'
        prev_key = f'{prev_season}:{team_abbrev}'

        print(f"Key: {key}")

        player_dict = {}
        
        check_requests()
        url = f'https://www.basketball-reference.com/teams/{team_abbrev}/{curr_year}.html'
        html = hf.get_soup(url)
        requests += 1
        check_requests()

        curr_roster = []
        try:
            curr_roster = html.find(id='roster').find('tbody').findAll('tr')
        except:
            continue

        for player in curr_roster:
            player = player.find('td')
            player_url = player.find('a', href=True)['href']
            player = player.getText()
            if player in player_data:
                continue
            
            check_requests()

            name = player.split(' ')
            fname = name[0]
            lname = name[1]
            suffix = '' if len(name) == 2 else name[2]

            player_dict[player] = {
                'bio' : {
                    'fname' : fname,
                    'lname' : lname,
                    'suffix' : suffix,
                },
                'url' : player_url
            }
            print(player)
            set_player_data(player_dict[player])

        check_requests()
        url = f'https://www.basketball-reference.com/teams/{team_abbrev}/{curr_year-1}.html'
        html = hf.get_soup(url)
        requests += 1
        check_requests()

        prev_roster = []
        try:
            prev_roster = html.find(id='roster').find('tbody').findAll('tr')
        except: # url doesn't exist for team ==> Team Name Change
            team_abbrev2 = ''
            if team_abbrev == 'BRK':
                team_abbrev2 = 'NJN'
            elif team_abbrev == 'WAS':
                team_abbrev2 = 'WSB'
            elif team_abbrev == 'CHO':
                team_abbrev2 = 'CHA'
            elif team_abbrev == 'CHA':
                continue
            elif team_abbrev == 'OKC':
                team_abbrev2 = 'SEA'
            elif team_abbrev == 'MEM':
                team_abbrev2 = 'VAN'
            elif team_abbrev == 'NOP':
                team_abbrev2 = 'NOH'
            elif team_abbrev == 'NOH':
                if curr_year == 2003:
                    continue
                team_abbrev2 = 'NOK'
            elif team_abbrev == 'NOK':
                team_abbrev2 = 'NOH'
            else:
                raise ValueError
            
            prev_key = f'{prev_season}:{team_abbrev2}'
            url = f'https://www.basketball-reference.com/teams/{team_abbrev2}/{curr_year-1}.html'
            html = hf.get_soup(url)
            requests += 1
            check_requests()

        for player in prev_roster:
            player = player.find('td')
            player_url = player.find('a', href=True)['href']
            player = player.getText()
            if player in player_data:
                continue
            
            check_requests()

            print(player)
            name = player.split(' ')
            fname = name[0]
            lname = '' if len(name) <= 1 else name[1]
            suffix = '' if len(name) <= 2 else name[2]

            player_dict[player] = {
                'bio' : {
                    'fname' : fname,
                    'lname' : lname,
                    'suffix' : suffix,
                },
                'url' : player_url
            }

            set_player_data(player_dict[player])

        check_requests()
        print(list(player_dict.keys()))
        player_data.update(player_dict)

        # CHECK FOR HIRED NEW COACH &/OR NEW EXECUTIVE IN OFFSEASON
        try:
            new_coach = team_data[key]['Coach(s)'][-1] != team_data[prev_key]['Coach(s)'][0]
        except:
            new_coach = 'NA'
        try:
            new_executive = team_data[key]['Exec(s)'][-1] != team_data[prev_key]['Exec(s)'][0]
        except:
            new_executive = 'NA'

        team_data[key]['New Coach'] = new_coach
        team_data[key]['New Exec'] = new_executive 

        if curr_season == '2022-2023': # == '2001-2002
            continue
        # CALCULATE ADDED VORP/WINS/BPM
        # ADD VALUES FROM PLAYERS ON CURR_TEAM THAT WERE NOT ON PREV_TEAM
        # SUBTRACT VALUES FROM PLAYERS ON PREV_TEAM BUT NOT ON CURR_TEAM
        
        curr_team = set(team_data[key]['Roster'])
        prev_team = set(team_data[prev_key]['Roster'])
        added_vorp = 0
        added_win_share = 0
        added_owin_share = 0
        added_dwin_share = 0
        added_bpm = 0
        added_obpm = 0
        added_dbpm = 0

        intersection = curr_team.intersection(prev_team)
        players_added = curr_team - intersection
        players_lost = prev_team - intersection
        
        for player in players_added:
            try:
                if player_data[player]['reg-stats'][prev_season]['g'] < 30:
                    continue
                if player_data[player]['reg-stats'][prev_season]['mp'] < 410:
                    continue
                added_vorp += player_data[player]['reg-stats'][prev_season]['advanced']['vorp']
                added_win_share += player_data[player]['reg-stats'][prev_season]['advanced']['ws']
                added_owin_share += player_data[player]['reg-stats'][prev_season]['advanced']['ows']
                added_dwin_share += player_data[player]['reg-stats'][prev_season]['advanced']['dws']
                added_bpm += player_data[player]['reg-stats'][prev_season]['advanced']['bpm']
                added_obpm += player_data[player]['reg-stats'][prev_season]['advanced']['obpm']
                added_dbpm += player_data[player]['reg-stats'][prev_season]['advanced']['dbpm']
            except KeyError as e: # different errors handled (wrong year key, player doesn't exist in dictionary)
                if '-' in str(e):
                    print('{} Has Year Error'.format(player))
                else:
                    print('{} Doesn\'t Exist in Dictionary'.format(player))

                continue
        
        for player in players_lost:
            try:
                if player_data[player]['reg-stats'][prev_season]['g'] < 30:
                    continue
                if player_data[player]['reg-stats'][prev_season]['mp'] < 410:
                    continue
                added_vorp -= player_data[player]['reg-stats'][prev_season]['advanced']['vorp']
                added_win_share -= player_data[player]['reg-stats'][prev_season]['advanced']['ws']
                added_owin_share -= player_data[player]['reg-stats'][prev_season]['advanced']['ows']
                added_dwin_share -= player_data[player]['reg-stats'][prev_season]['advanced']['dws']
                added_bpm -= player_data[player]['reg-stats'][prev_season]['advanced']['bpm']
                added_obpm -= player_data[player]['reg-stats'][prev_season]['advanced']['obpm']
                added_dbpm -= player_data[player]['reg-stats'][prev_season]['advanced']['dbpm']
            except KeyError as e: # different errors handled (wrong year key, player doesn't exist in dictionary)
                if '-' in str(e):
                    print('{} Has Year Error'.format(player))
                else:
                    print('{} Doesn\'t Exist in Dictionary'.format(player))

                continue


        team_data[key]['# of Players Added'] = len(players_added)
        team_data[key]['# of Players Lost'] = len(players_lost)
        team_data[key]['Added VORP'] = added_vorp
        team_data[key]['Added WS'] = added_win_share
        team_data[key]['Added OWS'] = added_owin_share
        team_data[key]['Added DWS'] = added_dwin_share
        team_data[key]['Added BPM'] = added_bpm
        team_data[key]['Added OBPM'] = added_obpm
        team_data[key]['Added DBPM'] = added_dbpm

        print(added_vorp, added_win_share, added_owin_share, added_dwin_share, added_bpm, added_obpm, added_dbpm)
        # print(team_data[key])
        # break
    # hf.save_data('biggy_data.txt', player_data)
    # hf.save_data('dict_data.txt', team_data)
    # break

# hf.save_data('biggy_data.txt', player_data)
# hf.save_data('dict_data.txt', team_data)


# GOAL: TAKE DATA FROM PREV. SEASON AND OFFSEASON TO PROJECT WINS FOR CURRENT SEASON
# E.G. PROJECT WINS FOR 2022-2023 SEASON, LOOK AT 2021-2022 SEASON STATS AND 2022 SUMMER OFFSEASON MOVES (DRAFT, ADDED VORP/WINS/BPM)

# team_data = hf.retrieve_data('dict_data.txt')
team_dict = []

flag = False
flag2 = False
flag3 = False

for key in team_data.keys():
    hash = team_data[key]

    temp_dict = {}

    # KEEP CURR. SEASON RESULT  (Team, Season, Playoffs, Champion, RunnerUp, Wins, Losses, Win%)
    # KEEP OFFSEASON ADDITIONS  (New Coach, New Exec, Salary Total, Added VORP, Added WS, Added OWS, Added DWS, 
    #                           Added BPM, Added OBPM, Added DBPM, # of Players Added, # of Players Lost
    curr_points = ['Team', 'Season', 'Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%', 'New Coach', 
                   'New Exec', 'Salary Total', 'Added VORP', 'Added WS', 'Added OWS', 'Added DWS', 'Added BPM', 
                   'Added OBPM', 'Added DBPM', '# of Players Added', '# of Players Lost']
    for temp_key in hash.keys():
        if temp_key not in curr_points:
            continue

        temp_dict[temp_key] = hash[temp_key] if type(hash[temp_key]) != float else round(hash[temp_key], 3)


    # GET PREV. SEASON STATS    
    """
    FG Per Game, FGA Per Game, FG %, FG3 Per Game, FG3A Per Game, FG3 %, 
    FG2 Per Game, FG2A Per Game, FG2 %, FT Per Game, FTA Per Game, FT %, 
    ORB Per Game, DRB Per Game, TRB Per Game, AST Per Game, STL Per Game, BLK Per Game, 
    TOV Per Game, PF Per Game, PTS Per Game, Opp FG Per Game, Opp FGA Per Game, Opp FG %, 
    Opp FG3 Per Game, Opp FG3A Per Game, Opp FG3 %, Opp FG2 Per Game, Opp FG2A Per Game, 
    Opp FG2 %, Opp FT Per Game, Opp FTA Per Game, Opp FT %, Opp ORB Per Game, Opp DRB Per Game, 
    Opp TRB Per Game, Opp AST Per Game, Opp STL Per Game, Opp BLK Per Game, Opp TOV Per Game, 
    Opp PF Per Game, Opp PTS Per Game, MOV, SOS, SRS, Off Rtg, Def Rtg, Pace, FTA Per FGA %, 
    FG3A Per FGA %, EFG %, TOV %, ORB %, FT Rate, Opp EFG %, Opp TOV %, DRB %, Opp FT Rate, 
    Net Rtg, OWS, DWS, WS, OBPM, DBPM, BPM, VORP, FG Pts Added, TS Pts Added, Salary Total, 
    Highest Draft Pick, # of DraftPicks, Playoffs, Champion, RunnerUp, Wins, Losses, Win%
    """

    prev_points = ['Playoffs', 'Champion', 'RunnerUp', 'Wins', 'Losses', 'Win%', 'FG Per Game', 'FGA Per Game', 
                   'FG %', 'FG3 Per Game', 'FG3A Per Game', 'FG3 %', 'FG2 Per Game', 'FG2A Per Game', 'FG2 %', 
                   'FT Per Game', 'FTA Per Game', 'FT %', 'ORB Per Game', 'DRB Per Game', 'TRB Per Game', 
                   'AST Per Game', 'STL Per Game', 'BLK Per Game', 'TOV Per Game', 'PF Per Game', 'PTS Per Game', 
                   'Opp FG Per Game', 'Opp FGA Per Game', 'Opp FG %', 'Opp FG3 Per Game', 'Opp FG3A Per Game', 
                   'Opp FG3 %', 'Opp FG2 Per Game', 'Opp FG2A Per Game', 'Opp FG2 %', 'Opp FT Per Game', 
                   'Opp FTA Per Game', 'Opp FT %', 'Opp ORB Per Game', 'Opp DRB Per Game', 'Opp TRB Per Game', 
                   'Opp AST Per Game', 'Opp STL Per Game', 'Opp BLK Per Game', 'Opp TOV Per Game', 'Opp PF Per Game', 
                   'Opp PTS Per Game', 'MOV', 'SOS', 'SRS', 'Off Rtg', 'Def Rtg', 'Pace', 'FTA Per FGA %', 
                   'FG3A Per FGA %', 'EFG %', 'TOV %', 'ORB %', 'FT Rate', 'Opp EFG %', 'Opp TOV %', 'DRB %', 
                   'Opp FT Rate', 'Net Rtg', 'OWS', 'DWS', 'WS', 'OBPM', 'DBPM', 'BPM', 'VORP', 'FG Pts Added', 
                   'TS Pts Added', 'Highest Draft Pick', '# of DraftPicks']
    
    curr_season = temp_dict['Season']
    
    curr_season_start = int(curr_season[:curr_season.find("-")])
    curr_season_end = int(curr_season[curr_season.find("-")+1:])
    team_abbrev = temp_dict['Team']

    prev_season = f'{curr_season_start-1}-{curr_season_end-1}'
    prev_key = f'{prev_season}:{team_abbrev}'

    prev_hash = {}

    try:
        prev_hash = team_data[prev_key]
    except:
        # if team_abbrev == 'BRK':
        #     prev_key = f'{prev_season}:NJN'
        #     prev_hash = team_data[prev_key]
        # elif team_abbrev == 'CHO':
        #     prev_key = f'{prev_season}:CHA'
        #     prev_hash = team_data[prev_key]
        # elif team_abbrev == 'OKC':
        #     prev_key = f'{prev_season}:SEA'
        #     prev_hash = team_data[prev_key]
        # elif team_abbrev == 'NOP':
        #     prev_key = f'{prev_season}:NOH'
        #     prev_hash = team_data[prev_key]
        # elif team_abbrev == 'NOH' and curr_season_end > 2003:
        #     prev_key = f'{prev_season}:NOK'
        #     prev_hash = team_data[prev_key]
        # elif team_abbrev == 'NOK':
        #     prev_key = f'{prev_season}:NOH'
        #     prev_hash = team_data[prev_key]
        # else:
        temp_dict['New Coach'] = 'NA'
        temp_dict['New Exec'] = 'NA'
        temp_dict['Added VORP'] = 'NA'
        temp_dict['Added WS'] = 'NA'
        temp_dict['Added OWS'] = 'NA'
        temp_dict['Added DWS'] = 'NA'
        temp_dict['Added BPM'] = 'NA'
        temp_dict['Added OBPM'] = 'NA'
        temp_dict['Added DBPM'] = 'NA'
        temp_dict['# of Players Lost'] = 'NA'
        temp_dict['# of Players Added'] = 'NA'
        for point in prev_points:
            temp_dict[f'Prev. {point}'] = 'NA'

    for temp_key in prev_hash.keys():
        if temp_key not in prev_points:
            continue

        temp_dict[f'Prev. {temp_key}'] = prev_hash[temp_key] if type(prev_hash[temp_key]) != float else round(prev_hash[temp_key], 3)

    # print(temp_dict)
    team_dict.append(temp_dict)

    # break

df = pd.DataFrame(team_dict)
df.to_csv('NBA2022-2024Spreadsheet.csv')
