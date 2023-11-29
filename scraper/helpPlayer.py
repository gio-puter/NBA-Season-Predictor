import datetime
import re
import json
from helperFunctions import monthConvert, countryConvert, cleanAwardID, cleanAwardText, getAward, yearConvert, salaryConvert, getTeamDict


""" Adds player's metadata to their bio
Position
Height/Weight
Birthday/Nationality
Education
Draft Position
NBA Debut Date
Experience
Jersey Number
"""
def set_bio(html, player):
    bio = html.find(id = 'meta').findAll('p')
    for item in bio:
        item = ' '.join(item.getText().split())
        if 'Position' in item: # get position(s) and shooting hand
            item = item.replace('and ', '')
            hand = item.find('Shoots: ')
            player['bio']['hand'] = item[hand + 8]

            position = item[item.find(':') + 2 : hand-3]

            if ', ' in position: # 3+ positions
                player['bio']['position'] = position.split(', ')
            else: # 2- positions "Point Guard Shooting Guard"
                position = position.split() # [Point, Guard, Shooting, Guard]
                del position[1::2] # [Point, Shooting]
                for index in range(len(position)):
                    if position[index] == 'Point' or position[index] == 'Shooting':
                        position[index] += ' Guard'
                    elif position[index] == 'Small' or position[index] == 'Power':
                        position[index] += ' Foward'
                player['bio']['position'] = position
        elif item[0].isdigit(): # height (inches) and weight (pounds)
            height = item[:item.find(',')]
            height = int(height[0]) * 12 + int(height[-1])
            weight = item[item.find(',') + 2: item.find('l')]

            player['bio']['height'] = height
            player['bio']['weight'] = int(weight)
        elif 'Born:' in item: # birthday + age
            bdate = item[item.find(':') + 2: item.find('in') - 1].replace(',', '')
            bloc = item[-2:].upper()
            bmonth, bday, byear = bdate.split(' ')
            age = datetime.datetime.now().year - int(byear) - 1
            if monthConvert(bmonth) < datetime.datetime.now().month:
                age += 1
            elif monthConvert(bmonth) == datetime.datetime.now().month and int(bday) <= datetime.datetime.now().day:
                age += 1
            
            player['bio']['birth-info'] = {
                'birth-month' : bmonth,
                'birth-day' : int(bday),
                'birth-year' : int(byear)
            }
            player['bio']['age'] = int(age)
            try:
                player['bio']['country'] = countryConvert(bloc)
            except:
                print("Don't know what " + bloc + " is")
                inp = input("Country?\n")
                player['bio']['country'] = inp
                print("Got it")
        elif 'College' in item: # show multiple colleges if applicable
            player['bio']['school'] = item[item.find(':') + 2:]
        elif 'High School' in item and 'school' not in player['bio']: #  might need to fix for multiple HS's like Jalen Green
            player['bio']['school'] = item[item.find(':') + 2 : item.find(' in ')]
        elif 'Draft' in item: # get draft info
            item = item[item.find(':') + 2:]
            if player['url'] == '/players/s/sabonar01.html':
                item = 'Portland Trail Blazers, 1st round (24th pick, 24th overall), 1986 NBA Draft'
            team, round, pick, draft = item.split(', ')
            draft = draft[:4]
            pick = round[round.find('(') + 1:]
            if pick[1].isdigit():
                pick = int(pick[0] + pick[1])
            else:
                pick = pick[0]

            round = round[0]
            player['bio']['draft-info'] = {
                'round' : int(round),
                'pick' : int(pick),
                'year' : int(draft),
                'team' : team
            }
        elif 'NBA Debut' in item: # get NBA debut date
            player['bio']['debut'] = item[item.find(':') + 2:]
        elif 'Experience' in item: # get years of NBA exp.
            item = item[item.find(':') + 2:].split()
            if item[0] == 'Rookie':
                player['bio']['experience'] = 0
            else:
                player['bio']['experience'] = int(item[0])

    jersey_num = html.findAll('svg', {'class' : 'jersey'})
    jersey_num = None if not jersey_num else int(jersey_num[-1].getText()) # get most recent jersey number
    player['bio']['jersey-num'] = jersey_num

    if 'draft-info' not in player['bio']: player['bio']['draft-info'] = {'round' : 'Undrafted'}

""" Adds player's awards to their awards list by year
e.g.
'awards' : {
    '2019-2020' : {
        'all-star' : True
    },
    '2020-2021' : {
        'all-star' : True
    },
    '2022-2023' : {
        'all-star' : True,
        'all-nba' : '3rd',
        'league-leader' : {'reb'}
    }
}
"""
def set_awards(html, player):
    awards = {}
    collection = html.find_all('div', {'class' : 'data_grid_box'})
    for category in collection:
        id = cleanAwardID(category.get('id'))
        if not id:
            continue
        
        category = category.find_all('td', {'class' : 'single'})
        for award in category:
            awardText = award.getText()
            if not cleanAwardText(awardText):
                continue
            
            award = getAward(id, awardText)
            if not award:
                continue
            
            year, awardText = award

            try:
                awards[year].append(awardText)
            except:
                awards[year] = []
                awards[year].append(awardText)
                
    player['awards'] = dict(sorted(awards.items()))

""" Adds player's contract info
Year
Salary
Option
Team
"""
def set_contract(html, player):
    contract = {}
    collection = html.find(id = 'div_contract')

    if not collection:
        player['contract'] = contract
        return
    
    collection = collection.find('div', {'class' : 'table_container'})
    if not collection:
        player['contract'] = contract
        return
    
    years = collection.find_all('th')[1:]
    salaries = collection.find_all('td')[1:]

    team = collection.find('a').getText()
    contract['team'] = team

    for i in range(len(years)):
        year = years[i].getText()
        year = yearConvert(year)

        salary = salaries[i].getText()
        salary = salaryConvert(salary)

        option = salaries[i].find('span').get('class')
        if not option:
            option = ''
        elif 'tm' in option[0]:
            option = 'Team'
        elif 'pl' in option[0]:
            option = 'Player'

        contract[year] = {'salary': salary, 'option' : option}


    player['contract'] = contract

""" Adds player's reg. and playoff total stats (per game can be extrapolated by rounding to nearest tenth)
Season/Year
Team
G
GS
MP
FG
FGA (percentage can be extrapolated by rounding to nearest thousandth, same with effective field goal percentage)
3P
3PA
2P
2PA
FT
FTA
ORB
DRB
TRB
AST
STL
BLK
TOV
PF
PTS
Triple-Doubles
"""
def set_stats(html, player):
    reg_totals_html = html.find(id = 'totals')
    reg_per_poss_html = html.find(id = 'per_poss')
    reg_advanced_html = html.find(id = 'advanced')
    reg_adjusted_shooting_html = html.find(id = 'adj_shooting')
    reg_pbp_html = html.find(id = 'pbp')
    reg_shooting_html = html.find(id = 'shooting')

    player['reg-stats'] = set_reg_stats(reg_totals_html)
    set_reg_per_poss(reg_per_poss_html, player['reg-stats'])
    set_reg_advanced(reg_advanced_html, player['reg-stats'])
    set_reg_adjusted_shooting(reg_adjusted_shooting_html, player['reg-stats'])
    set_reg_pbp(reg_pbp_html, player['reg-stats'])
    set_reg_shooting(reg_shooting_html, player['reg-stats'])

    playoff_totals_html = html.find(id = 'playoffs_totals')
    playoff_per_poss_html = html.find(id = 'playoffs_per_poss')
    playoff_advanced_html = html.find(id = 'playoffs_advanced')
    playoff_pbp_html = html.find(id = 'playoffs_pbp')
    playoff_shooting_html = html.find(id = 'playoffs_shooting')

    player['playoff-stats'] = set_playoff_stats(playoff_totals_html)
    set_playoff_per_poss(playoff_per_poss_html, player['playoff-stats'])
    set_playoff_advanced(playoff_advanced_html, player['playoff-stats'])
    set_playoff_pbp(playoff_pbp_html, player['playoff-stats'])
    set_playoff_shooting(playoff_shooting_html, player['playoff-stats'])

def set_reg_stats(html):
    reg_stats = {}
    if not html:
        return reg_stats
    
    rows = html.find('tbody').find_all('tr')
    abbrevTeam = {v: k for k, v in getTeamDict().items()}

    teamCount = 0
    for row in rows:
        year = yearConvert(row.find('th').getText())

        try:
            key = 'team' + str(teamCount)
            reg_stats[year][key] = {}
            start = reg_stats[year][key]
            teamCount += 1
        except:
            reg_stats[year] = {}
            start = reg_stats[year]
            teamCount = 0

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            if type in ('age', 'lg', 'DUMMY', 'pos'): #or re.search(r'pct$', type):
                continue
            
            if type == 'team':
                # print(data_stat.getText())
                stat = abbrevTeam[data_stat.getText()]
            else:
                try:
                    stat = int(data_stat.getText())
                except:
                    try:
                        stat = float(data_stat.getText())
                    except:
                        continue

            # stat = abbrevTeam[data_stat.getText()] if type == 'team' else int(data_stat.getText())
            start[type] = stat

    return reg_stats

def set_reg_per_poss(html, reg_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        reg_per_poss = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = reg_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = reg_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if 'poss' not in type and 'rtg' not in type:
                continue
            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            reg_per_poss[type] = stat

        try:
            start['advanced'].update(reg_per_poss)
        except:
            start['advanced'] = reg_per_poss

def set_reg_advanced(html, reg_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        reg_advanced = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = reg_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = reg_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            if type not in ('per', 'ts-pct', 'fg3a-per-fga-pct', 
                            'fta-per-fga-pct', 'orb-pct', 'drb-pct', 
                            'trb-pct', 'ast-pct', 'stl-pct', 'blk_pct',
                            'tov-pct', 'usg-pct', 'ows', 'dws', 'ws', 
                            'ws-per-48', 'obpm', 'dbpm', 'bpm', 'vorp'):
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            if 'per-fga-pct' in type:
                index = type.find('-per-fga-pct')
                type = type[:index] + '-rate'

            reg_advanced[type] = stat

        try:
            start['advanced'].update(reg_advanced)
        except:
            start['advanced'] = reg_advanced

def set_reg_adjusted_shooting(html, reg_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        reg_adjusted_shooting = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = reg_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = reg_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if 'adj' not in type and 'added' not in type:
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except: 
                    continue

            if 'per-fga-pct' in type:
                index = type.find('-per-fga-pct')
                type = type[:index] + '-rate'

            reg_adjusted_shooting[type] = stat

        try:
            start['advanced'].update(reg_adjusted_shooting)
        except:
            start['advanced'] = reg_adjusted_shooting

def set_reg_pbp(html, reg_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        reg_pbp = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = reg_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = reg_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if type in ['season', 'age', 'team', 'lg', 'pos', 'g', 'mp'] or 'pct' in type:
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            reg_pbp[type] = stat

        try:
            start['advanced'].update(reg_pbp)
        except:
            start['advanced'] = reg_pbp

def set_reg_shooting(html, reg_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        reg_shooting = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = reg_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = reg_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if ('fg' not in type and 'pct' not in type and 'dist' not in type):
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            if 'pct-fga-' in type:
                index = len('pct-fga-')
                type = type[index:] + '-rate'
            elif 'fg-pct-' in type: 
                index = len('fg-pct-')
                type = type[index:] + '-pct'
                type = type.replace('a', '')
            elif 'pct-ast-' in type:
                index = len('pct-ast-')
                type = 'assisted-' + type[index:] + '-pct'
            elif 'pct-fg3a-corner3' == type:
                type = 'corner3-rate'
                
            reg_shooting[type] = stat

        try:
            start['advanced'].update(reg_shooting)
        except:
            start['advanced'] = reg_shooting

def set_playoff_stats(html):
    playoff_stats = {}
    if not html:
        return playoff_stats

    rows = html.find('tbody').find_all('tr')
    abbrevTeam = {v: k for k, v in getTeamDict().items()}

    for row in rows:
        year = yearConvert(row.find('th').getText())
        playoff_stats[year] = {}

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            if type in ('age', 'lg', 'DUMMY', 'pos') or re.search(r'pct$', type):
                continue
            
            stat = abbrevTeam[data_stat.getText()] if type == 'team' else int(data_stat.getText())
            playoff_stats[year][type] = stat

    return playoff_stats
    
def set_playoff_per_poss(html, playoff_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        playoff_per_poss = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = playoff_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = playoff_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if 'poss' not in type and 'rtg' not in type:
                continue
            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            playoff_per_poss[type] = stat

        try:
            start['advanced'].update(playoff_per_poss)
        except:
            start['advanced'] = playoff_per_poss

def set_playoff_advanced(html, playoff_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        playoff_advanced = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = playoff_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = playoff_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            if type not in ('per', 'ts-pct', 'fg3a-per-fga-pct', 
                            'fta-per-fga-pct', 'orb-pct', 'drb-pct', 
                            'trb-pct', 'ast-pct', 'stl-pct', 'blk_pct',
                            'tov-pct', 'usg-pct', 'ows', 'dws', 'ws', 
                            'ws-per-48', 'obpm', 'dbpm', 'bpm', 'vorp'):
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            if 'per-fga-pct' in type:
                index = type.find('-per-fga-pct')
                type = type[:index] + '-rate'

            playoff_advanced[type] = stat

        try:
            start['advanced'].update(playoff_advanced)
        except:
            start['advanced'] = playoff_advanced

def set_playoff_pbp(html, playoff_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        playoff_pbp = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = playoff_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = playoff_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if type in ['season', 'age', 'team', 'lg', 'pos', 'g', 'mp'] or 'pct' in type:
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            playoff_pbp[type] = stat

        try:
            start['advanced'].update(playoff_pbp)
        except:
            start['advanced'] = playoff_pbp

def set_playoff_shooting(html, playoff_stats):
    if not html:
        return {}

    rows = html.find('tbody').find_all('tr')

    teamCount = 0
    lastYear = ''
    for row in rows:
        playoff_shooting = {}
        year = yearConvert(row.find('th').getText())

        if lastYear == year:
            string = 'team' + str(teamCount)
            start = playoff_stats[year][string]
            teamCount += 1
        else:
            teamCount = 0
            start = playoff_stats[year]
            lastYear = year

        season = row.find_all('td')
        for data_stat in season:
            type = re.sub(r'_', '-', re.sub(r'_id$', '', data_stat.get('data-stat')))
            
            if ('fg' not in type and 'pct' not in type and 'dist' not in type):
                continue

            try:
                stat = int(data_stat.getText())
            except:
                try:
                    stat = float(data_stat.getText())
                except:
                    continue

            if 'pct-fga-' in type:
                index = len('pct-fga-')
                type = type[index:] + '-rate'
            elif 'fg-pct-' in type: 
                index = len('fg-pct-')
                type = type[index:] + '-pct'
                type = type.replace('a', '')
            elif 'pct-ast-' in type:
                index = len('pct-ast-')
                type = 'assisted-' + type[index:] + '-pct'
            elif 'pct-fg3a-corner3' == type:
                type = 'corner3-rate'
                
            playoff_shooting[type] = stat

        try:
            start['advanced'].update(playoff_shooting)
        except:
            start['advanced'] = playoff_shooting


