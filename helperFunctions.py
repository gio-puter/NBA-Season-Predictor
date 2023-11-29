import re
import requests
from bs4 import BeautifulSoup
import json

def get_soup(url):
    page = requests.get(url)
    page = page.text.replace("<!--", "").replace("-->", "")
    soup = BeautifulSoup(page, 'html.parser')
    return soup

def save_data(save_file, store_data, sort=False):
    with open(save_file, 'w') as save_data:
        save_data.write(json.dumps(store_data, sort_keys=sort, indent=4))
        
def retrieve_data(get_file):
    try:
        with open(get_file) as f:
            data = f.read()
        return json.loads(data)
    except:
        return None
  
squads = {
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
    'Washington Bullets' : 'WSB',
    'Orlando Magic' : 'ORL',
    'Charlotte Hornets' : 'CHO',
    'Charlotte Horns' : 'CHH',
    'Charlotte Bobcats' : 'CHA',
    'Denver Nuggets' : 'DEN',
    'Minnesota Timberwolves' : 'MIN',
    'Oklahoma City Thunder' : 'OKC',
    'Seattle SuperSonics' : 'SEA',
    'Utah Jazz' : 'UTA',
    'Portland Trail Blazers' : 'POR',
    'Sacramento Kings' : 'SAC',
    'Kansas City Kings' : 'KCK',
    'Phoenix Suns' : 'PHX',
    'Phoneix Suns' : 'PHO',
    'Los Angeles Clippers' : 'LAC',
    'Los Angeles Lakers' : 'LAL',
    'Golden State Warriors' : 'GSW',
    'Memphis Grizzlies' : 'MEM',
    'Vancouver Grizzlies' : 'VAN',
    'New Orleans Pelicans' : 'NOP',
    'New Orleans Hornets' : 'NOH',
    'New Orleans/Oklahoma City Hornets' : 'NOK',
    'Dallas Mavericks' : 'DAL',
    'Houston Rockets' : 'HOU',
    'San Antonio Spurs' : 'SAS',
    'Multiple Teams' : 'TOT'
}

def getTeamDict():
    return squads
def teamAbbrev(team_name):
    return squads[team_name]
def monthConvert(month):
    monthConvert = {
        'January' : 1,
        'February' : 2,
        'March' : 3,
        'April' : 4,
        'May' : 5,
        'June' : 6,
        'July' : 7,
        'August' : 8,
        'September' : 9,
        'October' : 10,
        'November' : 11,
        'December' : 12
    }
    return monthConvert[month]
def countryConvert(country):
    countryConvert = {
        'AO' : 'Angola',
        'AR' : 'Argentina',
        'AG' : 'Antigua and Barbuda',
        'AT' : 'Austria',
        'AU' : 'Australia',
        'BS' : 'Bahamas',
        'BE' : 'Belgium',
        'BA' : 'Bosnia & Herzegovina',
        'BR' : 'Brazil',
        'VG' : 'British Virgin Islands',
        'CV' : 'Cabo Verde',
        'CA' : 'Canada',
        'CM' : 'Cameroon',
        'CN' : 'China',
        'CO' : 'Colombia',
        'HR' : 'Croatia',
        'CY' : 'Cyprus',
        'CZ' : 'Czechia',
        'DK' : 'Denmark',
        'DM' : 'Dominica',
        'DO' : 'Dominican Republic',
        'CD' : 'D.R.C.',
        'EG' : 'Egypt',
        'FI' : 'Finland',
        'FR' : 'France',
        'GF' : 'French Guiana',
        'GA' : 'Gabon',
        'DE' : 'Germany',
        'GE' : 'Georgia',
        'GH' : 'Ghana',
        'GP' : 'Guadeloupe',
        'GY' : 'Guyana',
        'GR' : 'Greece',
        'GN' : 'Guinea',
        'HT' : 'Haiti',
        'HU' : 'Hungary',
        'IR' : 'Iran',
        'IE' : 'Ireland',
        'IL' : 'Israel',
        'IT' : 'Italy',
        'JM' : 'Jamaica',
        'JP' : 'Japan',
        'LV' : 'Latvia',
        'LB' : 'Lebanon',
        'LT' : 'Lithuania',
        'LU' : 'Luxembourg',
        'ML' : 'Mali',
        'MQ' : 'Martinique',
        'MX' : 'Mexico',
        'ME' : 'Montenegro',
        'NL' : 'Netherlands',
        'NG' : 'Nigeria',
        'MK' : 'North Macedonia',
        'NZ' : 'New Zealand',
        'PA' : 'Panama',
        'PL' : 'Poland',
        'PT' : 'Portugal',
        'PR' : 'Puerto Rico',
        'DR' : 'Quebec',
        'CG' : 'Republic of the Congo',
        'RU' : 'Russia',
        'VC' : 'Saint Vincent and the Grenadines',
        'SN' : 'Senegal',
        'SD' : 'Sudan',
        'RS' : 'Serbia',
        'SI' : 'Slovenia',
        'ZA' : 'South Africa',
        'SS' : 'South Sudan',
        'ES' : 'Spain',
        'LC' : 'St. Lucia',
        'KR' : 'South Korea',
        'SE' : 'Sweden',
        'CH' : 'Switzerland',
        'TW' : 'Taiwan',
        'TZ' : 'Tanzania',
        'TN' : 'Tunisia',
        'TR' : 'Turkey',
        'UA' : 'Ukraine',
        'UY' : 'Uruguay',
        'US' : 'U.S.A.',
        'VI' : 'U.S. Virgin Islands',
        'GB' : 'United Kingdom',
        'VE' : 'Venezuela',
    }
    return countryConvert[country]

def cleanAwardID(id):
    id = re.sub(r'^leaderboard_(.*)$', r'\1', id)
    if len(id) < 5:
        return False
    if re.search('rtg$', id):
        return False
    if re.search('pct$', id):
        return False
    if re.search('48$', id):
        return False
    if re.search('prob$', id):
        return False
    if re.search('shares$', id):
        return False
    if re.search('_awards$', id):
        return False
    if re.search('dbl', id):
        return False
    if re.search('honors$', id):
        return False
    if re.search('^mp', id):
        return False
    
    return re.sub(r'(.*)_per_g$', r'\1', id)
def cleanAwardText(text):
    if re.search('^Career', text):
        return False
    if re.search('^Active', text):
        return False
    if re.search('Sporting News', text):
        return False
    if re.search('J. Walter', text):
        return False
    if re.search('Anniversary', text):
        return False
    if re.search('Twyman', text):
        return False
    if re.search('ABA', text):
        return False
    if re.search('Comeback', text):
        return False
    if re.search('Hustle', text):
        return False
    if re.search('Justice', text):
        return False
    if re.search('Coach', text):
        return False
    if re.search('Executive', text):
        return False
    if re.search('Seeding', text):
        return False
    return True
def getAward(id, text):
    if id == 'notable-awards':
        year = yearConvert(text[:7])

        text = text[text.find('(') + 1 : -1]
        if text == 'Michael Jordan Trophy':
            text = 'mvp'
        if text == 'Wilt Chamberlain Trophy':
            text = 'roty'
        if text == 'Hakeem Olajuwon Trophy':
            text = 'dpoy'
        if text == 'John Havlicek Trophy':
            text = 'smoy'
        if text == 'George Mikan Trophy':
            text = 'mip'
        if text == 'Bill Russell Trophy':
            text = 'finals-mvp'
        if text == 'Larry Bird Trophy':
            text = 'east-mvp'
        if text == 'Earvin "Magic" Johnson Trophy':
            text = 'west-mvp'
        if text == 'Kobe Bryant Trophy':
            text = 'allstar-mvp'

        return (year, text)
    if id == 'championships':
        year = yearConvert(text)
        return (year, 'champion')
    if id == 'allstar':
        year = yearConvert(text)
        return (year, id)
    if id == 'all_league':
        year = yearConvert(text[:7])
        if 'Rookie' in text:
            text = 'all-rookie' + text[-5:]
        if 'NBA' in text:
            text = 'all-nba' + text[-5:]
        if 'Defensive' in text:
            text = 'all-defensive' + text[-5:]

        return (year, text)
    if id == 'three_point_contests':
        if 'Winner' not in text:
            return None
        
        year = yearConvert(text)
        text = '3pt-contest-winner'
        return (year, text)
    if id == 'slam_dunk_contests':
        if 'Winner' not in text:
            return None
        
        year = yearConvert(text)
        text = 'dunk-contest-winner'
        return (year, text)
    if id == 'pts':
        if '1st' not in text:
            return None
        
        year = yearConvert(text)
        text = 'scoring-champ'
        return (year, text)
    if id == 'ast':
        if '1st' not in text:
            return None
        
        year = yearConvert(text)
        text = 'ast-champ'
        return (year, text)
    if id == 'trb':
        if '1st' not in text:
            return None
        
        year = yearConvert(text)
        text = 'reb-champ'
        return (year, text)
    if id =='stl':
        if '1st' not in text:
            return None
        
        year = yearConvert(text)
        text = 'stl-champ'
        return (year, text)
    if id =='blk':
        if '1st' not in text:
            return None
        
        year = yearConvert(text)
        text = 'blk-champ'
        return (year, text)
    return None

def yearConvert(text):
    if '-' in text:
        year = text[:4] + '-' + str(int(text[:4])+1)
    else:
        year = str(int(text[:4])-1) + '-' + text[:4]
    return year
def salaryConvert(text):
    return int(re.sub(r'[$,]', '', text))
