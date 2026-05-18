
import base64
import mimetypes
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import requests
from nicegui import app, ui

# Serve image files from both the repo root and /assets folder.
# This lets uploaded image assets load correctly on Railway.
if Path('assets').exists():
    app.add_static_files('/assets', 'assets')
app.add_static_files('/static', '.')

GREEN = '#4DDB68'
API_BASE_URL = 'https://api.golfcourseapi.com'
ROUNDS_FILE = Path('rounds.json')
CUSTOM_COURSES_FILE = Path('custom_courses.json')
APP_STATE_FILE = Path('app_state.json')


# Optional GitHub-backed storage. If GitHub fails, app falls back to local files.
GITHUB_STORAGE_TOKEN = os.getenv('GITHUB_STORAGE_TOKEN', '').strip()
GITHUB_STORAGE_REPO = os.getenv('GITHUB_STORAGE_REPO', 'MarioMercurio/golf-app-nicegui').strip()
GITHUB_STORAGE_BRANCH = os.getenv('GITHUB_STORAGE_BRANCH', 'main').strip()
GITHUB_STORAGE_PREFIX = os.getenv('GITHUB_STORAGE_PREFIX', 'data').strip().strip('/')


def github_storage_enabled():
    return bool(GITHUB_STORAGE_TOKEN and GITHUB_STORAGE_REPO)


def github_storage_path(filename):
    return f'{GITHUB_STORAGE_PREFIX}/{filename}' if GITHUB_STORAGE_PREFIX else filename


def github_headers():
    return {
        'Authorization': f'Bearer {GITHUB_STORAGE_TOKEN}',
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    }


def local_read_json(path, default_value):
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception:
        pass
    return default_value


def local_write_json(path, data):
    try:
        path.write_text(json.dumps(data, indent=2))
        return True
    except Exception:
        return False


def github_read_json(filename, default_value):
    if not github_storage_enabled():
        return default_value

    try:
        url = f'https://api.github.com/repos/{GITHUB_STORAGE_REPO}/contents/{github_storage_path(filename)}'
        response = requests.get(url, headers=github_headers(), params={'ref': GITHUB_STORAGE_BRANCH}, timeout=2)

        if response.status_code == 404:
            return default_value
        if response.status_code >= 400:
            return default_value

        payload = response.json()
        encoded = payload.get('content', '')
        if not encoded:
            return default_value

        decoded = base64.b64decode(encoded).decode('utf-8')
        return json.loads(decoded)
    except Exception:
        return default_value


def github_write_json(filename, data):
    if not github_storage_enabled():
        return False

    try:
        url = f'https://api.github.com/repos/{GITHUB_STORAGE_REPO}/contents/{github_storage_path(filename)}'
        current = requests.get(url, headers=github_headers(), params={'ref': GITHUB_STORAGE_BRANCH}, timeout=2)

        sha = None
        if current.status_code == 200:
            sha = current.json().get('sha')
        elif current.status_code != 404:
            return False

        content_text = json.dumps(data, indent=2)
        body = {
            'message': f'Golf app saved {filename}',
            'content': base64.b64encode(content_text.encode('utf-8')).decode('ascii'),
            'branch': GITHUB_STORAGE_BRANCH,
        }
        if sha:
            body['sha'] = sha

        saved = requests.put(url, headers=github_headers(), json=body, timeout=3)
        if saved.status_code >= 400:
            return False

        try:
            Path(filename).write_text(content_text)
        except Exception:
            pass

        return True
    except Exception:
        return False


def read_storage_json(filename, path, default_value):
    if github_storage_enabled():
        data = github_read_json(filename, default_value)
        try:
            path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass
        return data
    return local_read_json(path, default_value)


def write_storage_json(filename, path, data):
    if github_storage_enabled() and github_write_json(filename, data):
        return True
    return local_write_json(path, data)


US_STATES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR',
    'California': 'CA', 'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE',
    'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID',
    'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS',
    'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
    'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE',
    'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC',
    'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
    'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT',
    'Vermont': 'VT', 'Virginia': 'VA', 'Washington': 'WA',
    'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
}


MAIN_IMAGES = {
    'SCORE': 'Main - Score.png',
    'PUTTS': 'Main - Putts.png',
}

PENALTY_IMAGES = {
    'OB': 'Penalty - OB.png',
    'GREEN BUNKER': 'Penalty - Green Bunker .png',
    'FAIRWAY BUNKER': 'Penalty - Fairway Bunker.png',
    'WATER': 'Penalty - Water.png',
    'DROP': 'Penalty - Drop.png',
}

GASH_IMAGES = {
    'DUFF': 'Gash - Duff Chunk.png',
    'HERO SHOT': 'Gash - Hero Shot.png',
    'MISREAD': 'Gash - Misread.png',
    'UNDER CLUB': 'Gash - Under Club.png',
    'BAD TARGET': 'Gash - Bad Target.png',
}

CLUBS = [
    'DRIVER',
    '3 WOOD',
    '3 HYBRID',
    '4 HYBRID',
    '7 HYBRID',
    '8 HYBRID',
    '6 IRON',
    '7 IRON',
    '8 IRON',
    '9 IRON',
    'PITCHING WEDGE',
    'APPROACH WEDGE',
    '52° WEDGE',
    '56° WEDGE',
    '58° WEDGE',
    '64° WEDGE',
]
TEE_LOCATIONS = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']
TEE_QUALITIES_PAR_3 = ['TOO LONG', 'LITTLE LONG', 'PERFECT', 'LITTLE SHORT', 'MIS-HIT SHORT']
TEE_QUALITIES_PAR_4_5 = ['TOO LONG', 'CRUSHED', 'AVERAGE', 'MIS-HIT SHORT']
HAZARDS = ['OB', 'GREEN BUNKER', 'FAIRWAY BUNKER', 'WATER', 'DROP']
GASHES = ['DUFF', 'HERO SHOT', 'MISREAD', 'UNDER CLUB', 'BAD TARGET']

SAMPLE_HOLES = [
    {'hole': 1, 'par': 5, 'yards': 523, 'handicap': 5},
    {'hole': 2, 'par': 4, 'yards': 398, 'handicap': 11},
    {'hole': 3, 'par': 3, 'yards': 171, 'handicap': 17},
    {'hole': 4, 'par': 4, 'yards': 421, 'handicap': 3},
    {'hole': 5, 'par': 4, 'yards': 366, 'handicap': 13},
    {'hole': 6, 'par': 5, 'yards': 548, 'handicap': 1},
    {'hole': 7, 'par': 3, 'yards': 188, 'handicap': 15},
    {'hole': 8, 'par': 4, 'yards': 405, 'handicap': 7},
    {'hole': 9, 'par': 4, 'yards': 389, 'handicap': 9},
]


def asset_path(filename):
    root = Path(filename)
    assets = Path('assets') / filename
    if root.exists():
        return str(root)
    if assets.exists():
        return str(assets)
    return ''



def get_api_key():
    return os.environ.get('GOLF_API_KEY', '') or os.environ.get('GOLF_COURSE_API_KEY', '')





def button_image_src(label):
    mapping = {
        'PLAY GOLF': 'Main - Play Golf.jpg',
        'SHRINK THE GAME': 'Main - Shrink The Game.jpg',
        'HOME': 'Main - Home.jpg',
        'STATS': 'Main - Stats.jpg',
        'RECORD BOOK': 'Main - Record Book.jpg',
    }

    filename = mapping.get(str(label).upper(), '')
    if not filename:
        return ''

    if Path(filename).exists():
        return '/static/' + quote(filename)

    if (Path('assets') / filename).exists():
        return '/static/assets/' + quote(filename)

    return ''


def graphic_button(label, on_click, extra_class=''):
    classes = extra_class.strip() if extra_class else 'start-button'
    return ui.button(label, on_click=on_click).props('color=green').classes(classes)


def home_graphic_src():
    image_names = ['Main Header.jpeg', 'Main Header.jpg', 'Main Header.png']

    for filename in image_names:
        if Path(filename).exists():
            return '/static/' + quote(filename)

        if (Path('assets') / filename).exists():
            return '/static/assets/' + quote(filename)

    return ''


def video_src_for_home():
    video_names = ['GolfIntro 2.mp4', 'Main Header.jpeg']
    for filename in video_names:
        root_path = Path(filename)
        assets_path = Path('assets') / filename

        if assets_path.exists():
            return '/assets/' + quote(filename)
        if root_path.exists():
            return '/static/' + quote(filename)

    return ''


def api_search_courses(search_query):
    api_key = get_api_key()
    if not api_key:
        return []

    try:
        response = requests.get(
            f'{API_BASE_URL}/v1/search',
            headers={'Authorization': f'Key {api_key}'},
            params={'search_query': search_query},
            timeout=20,
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get('courses', []) if isinstance(data, dict) else []

    except Exception:
        return []


def api_get_course_details(course_id):
    api_key = get_api_key()
    if not api_key:
        return {}

    try:
        response = requests.get(
            f'{API_BASE_URL}/v1/courses/{course_id}',
            headers={'Authorization': f'Key {api_key}'},
            timeout=20,
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception:
        return {}


def get_course_display_name(course):
    name = course.get('course_name') or course.get('name') or course.get('club_name') or 'Unknown Course'
    city = course.get('city', '')
    state = course.get('state', '')

    location = course.get('location', {})
    if isinstance(location, dict):
        city = city or location.get('city', '')
        state = state or location.get('state', '')

    if city and state:
        return f'{name} — {city}, {state}'
    if state:
        return f'{name} — {state}'
    return name


def get_course_state(course):
    state = course.get('state', '')

    location = course.get('location', {})
    if isinstance(location, dict):
        state = state or location.get('state', '')

    return str(state).upper().strip()


def filter_courses_by_state(courses, state_abbrev):
    return [course for course in courses if get_course_state(course) == state_abbrev.upper()]


def get_course_id(course):
    return course.get('id') or course.get('course_id')


def get_tee_options(course_details):
    tee_options = []
    course_data = course_details.get('course', course_details)
    tees = course_data.get('tees', {})

    if not isinstance(tees, dict):
        return tee_options

    for gender in ['male', 'female']:
        gender_tees = tees.get(gender, [])
        if not isinstance(gender_tees, list):
            continue

        for tee in gender_tees:
            tee_name = tee.get('tee_name', 'Unnamed Tee')
            total_yards = tee.get('total_yards', '')
            rating = tee.get('course_rating', '')
            slope = tee.get('slope_rating', '')

            parts = [tee_name]

            if total_yards:
                parts.append(f'{total_yards} yds')
            if rating:
                parts.append(f'Rating {rating}')
            if slope:
                parts.append(f'Slope {slope}')

            parts.append(gender.title())

            tee_options.append({
                'label': ' • '.join(parts),
                'tee': tee,
            })

    return tee_options


def get_holes_from_tee(tee):
    clean_holes = []
    holes = tee.get('holes', [])

    if not isinstance(holes, list):
        return clean_holes

    for index, hole in enumerate(holes, start=1):
        try:
            par = int(hole.get('par', 4))
        except Exception:
            par = 4

        try:
            yards = int(hole.get('yards') or hole.get('yardage') or 0)
        except Exception:
            yards = 0

        clean_holes.append({
            'hole': index,
            'par': par,
            'yards': yards,
            'handicap': hole.get('handicap') or hole.get('hcp') or '',
        })

    return clean_holes


def init_round_entries():
    global round_entries

    round_entries = {}

    for hole in hole_data:
        round_entries[hole['hole']] = default_entry(hole)

    current_hole_index['value'] = 0


def tee_quality_options(par):
    return TEE_QUALITIES_PAR_3 if int(par) == 3 else TEE_QUALITIES_PAR_4_5


def default_tee_quality(par):
    return 'PERFECT' if int(par) == 3 else 'AVERAGE'


def default_entry(hole):
    par = int(hole['par'])
    return {
        'hole': hole['hole'],
        'par': par,
        'yards': hole['yards'],
        'handicap': hole['handicap'],
        'score': 0,
        'putts': 0,
        'tee_club': 'DRIVER',
        'tee_location': 'CENTER',
        'tee_quality': default_tee_quality(par),
        'inside_100_in_3': 'NO',
                'fairway_hit': 'NO',
                'green_hit': 'NO',
        'hazards': {item: 0 for item in HAZARDS},
        'gashes': {item: 0 for item in GASHES},
    }


def tee_color(par, location, quality):
    dark_red = '#b00000'
    bright_red = '#ff0900'
    dark_green = '#007a3d'
    medium_green = '#68c34a'
    light_green = '#94c83d'
    perfect_green = '#00ff00'
    lost = location in ['LOST LEFT', 'LOST RIGHT']
    side = location in ['LEFT', 'RIGHT']

    if int(par) == 3:
        if quality == 'TOO LONG':
            return dark_red
        if quality == 'LITTLE LONG':
            return bright_red if lost else dark_green if side else medium_green
        if quality == 'PERFECT':
            return bright_red if lost else medium_green if side else perfect_green
        if quality == 'LITTLE SHORT':
            return bright_red if lost else dark_green if side else medium_green
        if quality == 'MIS-HIT SHORT':
            return dark_red
    else:
        if quality == 'TOO LONG':
            return dark_red
        if quality == 'CRUSHED':
            return bright_red if lost else medium_green if side else perfect_green
        if quality == 'AVERAGE':
            return bright_red if lost else dark_green if side else light_green
        if quality == 'MIS-HIT SHORT':
            return dark_red

    return GREEN


hole_data = SAMPLE_HOLES.copy()
round_entries = {hole['hole']: default_entry(hole) for hole in hole_data}
round_info = {
    'date': date.today().isoformat(),
    'course': 'Sample Golf Course',
    'api_course': 'Sample Golf Course',
    'tee': 'Blue Tees',
    'holes': 9,
}
MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]
DAY_OPTIONS = list(range(1, 32))
YEAR_OPTIONS = list(range(date.today().year - 10, date.today().year + 6))

today_value = date.today()

create_course_state = {
    'course_name': '',
    'city': '',
    'state': 'Ohio',
    'country': 'United States',
    'tee_color': 'Blue',
    'slope': '',
    'rating': '',
    'holes': [],
    'status': '',
}

start_state = {
    'custom_course_label': None,
    'round_month': MONTH_NAMES[today_value.month - 1],
    'round_day': today_value.day,
    'round_year': today_value.year,
    'state_name': 'Ohio',
    'search_query': '',
    'course_matches': [],
    'course_labels': [],
    'selected_course_label': None,
    'selected_course': None,
    'tee_options': [],
    'tee_labels': [],
    'selected_tee_label': None,
    'selected_tee': None,
    'hole_options': [9],
    'selected_holes': 9,
    'status': '',
}

quick_load_state = {
    'status': '',
    'round_month': MONTH_NAMES[today_value.month - 1],
    'round_day': today_value.day,
    'round_year': today_value.year,
    'state_name': 'Ohio',
    'search_query': '',
    'course_matches': [],
    'course_labels': [],
    'selected_course_label': None,
    'selected_course': None,
    'tee_options': [],
    'tee_labels': [],
    'selected_tee_label': None,
    'selected_tee': None,
    'holes': [],
    'course_ready': False,
}

current_hole_index = {'value': 0}
current_screen = {'value': 'home'}
if not create_course_state['holes']:
    for i in range(1, 19):
        create_course_state['holes'].append({'hole': i, 'yards': '', 'par': 0, 'handicap': 0})

root_container = None

STYLE = '''
<style>
html, body, .q-page, .nicegui-content {
    background: black !important;
    color: white !important;
    font-family: Arial, sans-serif;
    margin: 0;
    overscroll-behavior: none;
}

.main-wrap {
    max-width: 760px;
    margin: auto;
    padding: 10px 10px 36px 10px;
    background: black;
}

.title {
    color: #4DDB68;
    font-size: 58px;
    font-weight: 1000;
    line-height: 1;
    margin: 12px 0 18px 0;
}

.hole-nav {
    display: grid;
    grid-template-columns: 54px 1fr 54px;
    gap: 8px;
    margin-bottom: 10px;
}

.nav-center {
    background: #1f2028;
    height: 50px;
    display:flex;
    align-items:center;
    justify-content:center;
    color:white;
    font-size: 24px;
    font-weight: 1000;
}

.nav-btn button {
    height: 50px !important;
    width: 100% !important;
    background: #4DDB68 !important;
    color: white !important;
    border-radius: 0 !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
}

.hole-card {
    background: #4DDB68;
    padding: 16px 12px 14px 12px;
    margin-bottom: 16px;
}

.hole-title {
    color:white;
    text-align:center;
    font-size: 52px;
    font-weight: 1000;
    line-height: 1;
    margin-bottom: 12px;
}

.meta-grid {
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 7px;
}

.meta-box {
    background:black;
    color:white;
    text-align:center;
    padding: 9px 3px;
    font-size: 15px;
    font-weight: 1000;
    line-height: 1.1;
}

.meta-box span {
    color:#ff3529;
    font-size: 22px;
}

.main-grid {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.stat-card {
    background:#191919;
    overflow:hidden;
}

.main-img {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
    background: #333333;
}

.fake-image {
    aspect-ratio: 1 / 1;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size: 46px;
    font-weight: 1000;
    color:white;
    text-align:center;
}

.score-bg { background:#b89c72; }
.putts-bg { background:#4f9d00; }

.big-number {
    text-align:center;
    color:white;
    font-size: 58px;
    font-weight: 1000;
    line-height:1;
    padding: 16px 0 12px 0;
}

.control-row {
    display:grid;
    grid-template-columns: 1fr 1fr;
}

.control-row button {
    border-radius:0 !important;
    height: 42px !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
}

.minus button { background:#333333 !important; color:white !important; }
.plus button { background:#4DDB68 !important; color:white !important; }

.white-line {
    border-top: 4px solid white;
    margin: 26px 0 18px 0;
}

.section-title {
    color:#4DDB68;
    text-align:center;
    font-size: 46px;
    font-weight: 1000;
    line-height:1;
    margin: 22px 0 16px 0;
}

.club-label {
    color:white;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 5px;
}

.location-title {
    color:white;
    font-size: 34px;
    font-weight: 1000;
    margin: 16px 0 12px 0;
}

.tee-caption {
    color:#aaaaaa;
    text-align:center;
    font-size: 12px;
    font-weight: 800;
    margin-bottom: 14px;
}

.tee-grid {
    display:grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
}

.tee-col-title {
    color:yellow;
    text-align:center;
    font-size: 10px;
    font-weight: 1000;
    margin-bottom: 5px;
    min-height: 20px;
    line-height:1;
}

.tee-btn button {
    width:100% !important;
    height: 38px !important;
    min-height: 38px !important;
    border-radius:0 !important;
    font-size: 8px !important;
    font-weight: 1000 !important;
    color:black !important;
    padding:0 !important;
    margin-bottom: 5px !important;
}

.tee-selected button {
    border: 3px solid white !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}

.selected-note {
    color:#4DDB68;
    text-align:center;
    font-size: 14px;
    font-weight:1000;
    margin-top: 12px;
}

.tile-grid {
    display:grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 7px;
}

.tile {
    background:#191919;
    overflow:hidden;
}

.tile-img, .tile-fallback {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
    background: #333333;
}

.tile-fallback {
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    font-size: 14px;
    font-weight:1000;
    padding: 4px;
    box-sizing:border-box;
    color:white;
}

.tile-label {
    color:white;
    text-align:center;
    font-size: 10px;
    font-weight: 1000;
    min-height: 28px;
    padding-top: 7px;
    line-height:1.05;
}

.tile-value {
    color:white;
    text-align:center;
    font-size: 36px;
    font-weight:1000;
    line-height:1;
    padding: 8px 0 10px 0;
}

.tile-controls {
    display:grid;
    grid-template-columns: 1fr 1fr;
}

.tile-controls button {
    height: 34px !important;
    border-radius:0 !important;
    font-size: 18px !important;
    padding:0 !important;
}

.scoring-question {
    color:white;
    font-size: 24px;
    font-weight:1000;
    line-height:1.1;
    margin-bottom: 12px;
}

.yes-no-grid {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.yes-no-grid button {
    height: 56px !important;
    border-radius:0 !important;
    font-size: 20px !important;
    font-weight:1000 !important;
}

.active-choice button {
    border: 3px solid white !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}


.analytics-grid {
    display:grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 18px;
}

.analytics-card {
    background:#1f2028;
    border:2px solid #333333;
    padding: 16px 8px;
    text-align:center;
}

.analytics-label {
    color:#aaaaaa;
    font-size: 12px;
    font-weight: 1000;
    margin-bottom: 8px;
    line-height:1.1;
}

.analytics-value {
    color:#4DDB68;
    font-size: 34px;
    font-weight: 1000;
    line-height: 1;
}

.analytics-sub {
    color:white;
    font-size: 12px;
    font-weight:900;
    margin-top:6px;
}

.breakdown-row {
    display:grid;
    grid-template-columns: 74px 1fr 82px;
    gap: 8px;
    align-items:center;
    background:#1f2028;
    border:2px solid #333333;
    padding: 8px;
    margin-bottom: 8px;
}

.breakdown-icon {
    width: 74px;
    height: 74px;
    object-fit:cover;
    background:#333333;
}

.breakdown-fallback {
    width:74px;
    height:74px;
    background:#333333;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    font-size:10px;
    font-weight:1000;
    padding:4px;
    box-sizing:border-box;
}

.breakdown-name {
    color:white;
    font-size: 16px;
    font-weight:1000;
    line-height:1.1;
}

.breakdown-detail {
    color:#aaaaaa;
    font-size: 12px;
    font-weight:900;
    margin-top:4px;
}

.breakdown-value {
    color:#4DDB68;
    font-size: 34px;
    font-weight:1000;
    text-align:right;
}

.par-grid {
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 14px;
}

.par-card {
    background:#1f2028;
    border:2px solid #333333;
    padding: 12px 6px;
    text-align:center;
}

.par-title {
    color:white;
    font-size: 16px;
    font-weight:1000;
    margin-bottom:8px;
}

.par-percent {
    color:#4DDB68;
    font-size: 32px;
    font-weight:1000;
    line-height:1;
}

.par-detail {
    color:#aaaaaa;
    font-size: 11px;
    font-weight:900;
    margin-top:6px;
    line-height:1.2;
}

.matrix-grid {
    display:grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
    margin-top:10px;
}

.matrix-cell {
    background:#1f2028;
    border:1px solid #333333;
    min-height:58px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:4px;
}

.matrix-label {
    color:#aaaaaa;
    font-size: 8px;
    font-weight:1000;
    line-height:1;
    margin-bottom:4px;
}

.matrix-value {
    color:#4DDB68;
    font-size: 20px;
    font-weight:1000;
    line-height:1;
}

.course-card,
.round-card,
.trend-card {
    background:#1f2028;
    border:2px solid #333333;
    padding: 14px;
    color:white;
    font-size: 16px;
    font-weight: 900;
    line-height:1.45;
    margin-bottom: 10px;
}

.trend-good { color:#4DDB68; font-weight:1000; }
.trend-bad { color:#ff3529; font-weight:1000; }
.trend-neutral { color:#aaaaaa; font-weight:1000; }



.stats-tee-layout {
    display: grid;
    grid-template-columns: 1fr 115px;
    gap: 7px;
    align-items: stretch;
}

.stats-tee-grid-left {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 4px;
}

.stats-tee-row-totals {
    display: grid;
    gap: 5px;
}

.stats-tee-row-total-spacer {
    min-height: 0px;
}

.stats-tee-row-total-box {
    background:#1f2028;
    border:1px solid #333333;
    min-height:70px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:4px;
    box-sizing:border-box;
}

.stats-tee-row-total-label {
    color:#aaaaaa;
    font-size:8px;
    font-weight:1000;
    line-height:1;
    margin-bottom:4px;
}

.stats-tee-row-total-pct {
    color:#4DDB68;
    font-size:22px;
    font-weight:1000;
    line-height:1;
}

.stats-tee-row-total-count {
    color:#aaaaaa;
    font-size:9px;
    font-weight:1000;
    margin-top:3px;
}


.stats-tee-cell {
    min-height: 70px;
    border-radius: 4px;
    margin-bottom: 5px;
    border: 1px solid rgba(0,0,0,.35);
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    color:white;
    box-sizing:border-box;
    padding: 4px 2px;
}

.stats-tee-quality {
    font-size: 8px;
    font-weight: 1000;
    line-height:1;
    color:black;
    margin-bottom: 4px;
}

.stats-tee-percent {
    font-size: 20px;
    font-weight: 1000;
    line-height:1;
    color:white;
    text-shadow: 0 1px 1px rgba(0,0,0,.6);
}

.stats-tee-count {
    font-size: 9px;
    font-weight: 1000;
    color:white;
    opacity:.9;
    margin-top:2px;
}


.stats-tee-column-total {
    background:#1f2028;
    border:1px solid #333333;
    min-height:82px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:5px;
    box-sizing:border-box;
}

.stats-tee-column-title {
    color:#aaaaaa;
    font-size:9px;
    font-weight:1000;
    line-height:1;
    margin-bottom:4px;
}

.stats-tee-column-pct {
    color:#4DDB68;
    font-size:25px;
    font-weight:1000;
    line-height:1;
}

.stats-tee-column-count {
    color:#aaaaaa;
    font-size:9px;
    font-weight:1000;
    margin-top:4px;
}

.stats-tee-row-total-column-spacer {
    min-height:82px;
}

.stats-tee-row-total-label-spacer {
    min-height:20px;
}

.stats-tee-quality {
    font-size: 10.5px !important;
    font-weight: 1000 !important;
    letter-spacing: .1px;
}

.tee-col-title {
    font-size: 11px !important;
    font-weight: 1000 !important;
}


.score-type-grid {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1fr;
    gap: 4px;
    margin-bottom: 18px;
}

.score-type-cell {
    background:#1f2028;
    border:1px solid #333333;
    min-height:58px;
    display:flex;
    flex-direction:column;
    align-items:center;
    justify-content:center;
    text-align:center;
    padding:6px 4px;
    box-sizing:border-box;
}

.score-type-header {
    background:#4DDB68;
    color:black;
    font-size:13px;
    font-weight:1000;
}

.score-type-row-label {
    color:white;
    font-size:12px;
    font-weight:1000;
    line-height:1.05;
}

.score-type-value {
    color:#4DDB68;
    font-size:28px;
    font-weight:1000;
    line-height:1;
}

.score-type-sub {
    color:#aaaaaa;
    font-size:9px;
    font-weight:900;
    margin-top:3px;
}

.summary-box {
    background:#1f2028;
    border:2px solid #333333;
    color:white;
    padding: 16px;
    font-size: 22px;
    font-weight: 1000;
    line-height:1.5;
}

@media (max-width: 700px) {
    .title { font-size: 48px; }
    .hole-title { font-size: 42px; }
    .section-title { font-size: 38px; }
    .fake-image { font-size: 39px; }
    .big-number { font-size: 52px; }
    .meta-box { font-size: 13px; }
    .meta-box span { font-size: 19px; }
    .tile-grid { gap: 5px; }
    .tile-value { font-size: 30px; }
}

.home-wrap {
    max-width: 760px;
    margin: auto;
    padding: 28px 14px;
    min-height: 90vh;
    background: black;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.home-title {
    color: #4DDB68;
    font-size: 82px;
    font-weight: 1000;
    line-height: 1;
    text-align: center;
    margin-bottom: 10px;
}

.home-subtitle {
    color: white;
    font-size: 24px;
    font-weight: 1000;
    text-align: center;
    margin-bottom: 34px;
}

.home-button button,
.start-button button,
.bottom-button button {
    width: 100% !important;
    min-height: 62px !important;
    border-radius: 0 !important;
    background: #4DDB68 !important;
    color: white !important;
    font-size: 22px !important;
    font-weight: 1000 !important;
    margin-bottom: 12px !important;
}

.home-button.secondary button,
.start-button.secondary button {
    background: #1f2028 !important;
}

.status-box {
    background:#1f2028;
    border:2px solid #333333;
    color:white;
    padding:16px;
    font-size:18px;
    font-weight:900;
    line-height:1.4;
    margin-bottom:12px;
}

.start-label {
    color: white;
    font-size: 15px;
    font-weight: 1000;
    margin-top: 18px;
    margin-bottom: 6px;
}

.bottom-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 20px;
}


/* FINAL TEE MATRIX CLEANUP */
.stats-tee-grid-left {
    display: grid !important;
    grid-template-columns: repeat(5, 1fr) !important;
    gap: 5px !important;
}

.stats-tee-row-totals {
    display: grid !important;
    gap: 5px !important;
}

.stats-tee-cell {
    min-height: 70px !important;
    border-radius: 4px !important;
    margin-bottom: 0px !important;
    box-sizing: border-box !important;
}

.stats-tee-column-total,
.stats-tee-row-total-box,
.stats-tee-row-total-spacer-box {
    background: #1f2028 !important;
    border: 1px solid #333333 !important;
}

.stats-tee-row-total-spacer-box {
    visibility: hidden !important;
}

.tee-col-title,
.stats-tee-row-total-column-spacer,
.stats-tee-row-total-label-spacer,
.stats-tee-row-total-spacer {
    display: none !important;
}

.stats-tee-quality {
    font-size: 10.5px !important;
    font-weight: 1000 !important;
    letter-spacing: .1px !important;
    color: black !important;
}

.stats-tee-column-total .stats-tee-quality,
.stats-tee-row-total-box .stats-tee-quality {
    color: #aaaaaa !important;
}

.stats-tee-percent {
    font-size: 24px !important;
    font-weight: 1000 !important;
}

.stats-tee-count {
    font-size: 9.5px !important;
    font-weight: 1000 !important;
}


/* HOME SCREEN POLISH */
.home-wrap {
    max-width: 760px !important;
    margin: auto !important;
    padding: 26px 18px 40px 18px !important;
    min-height: 92vh !important;
    background: black !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: center !important;
}

.home-video-wrap {
    width: 100%;
    margin: 28px auto 52px auto;
    display: flex;
    justify-content: center;
}

.home-video-wrap video {
    width: 420px; max-width: 100%;
    display: block;
    border: 1px solid #111111;
}

.home-fallback-logo {
    color:#4DDB68;
    font-size: 82px;
    font-weight:1000;
    text-align:center;
    margin: 50px 0 60px 0;
    line-height:1;
}

.home-menu {
    width: 100%;
    max-width: 520px;
    display: flex;
    flex-direction: column;
    gap: 28px;
    align-items: center;
}

.home-button {
    width: 100% !important;
}

.home-button button {
    width: 100% !important;
    min-height: 108px !important;
    border-radius: 0 !important;
    background: #4DDB68 !important;
    color: white !important;
    font-size: 46px !important;
    font-weight: 1000 !important;
    letter-spacing: 1px !important;
    margin-bottom: 0 !important;
    font-family: Georgia, 'Times New Roman', serif !important;
}

.home-button.secondary button {
    background: #4DDB68 !important;
}

@media (max-width: 700px) {
    .home-wrap {
        padding: 22px 16px 34px 16px !important;
    }

    .home-video-wrap {
        margin: 22px auto 46px auto;
    }

    .home-menu {
        max-width: 430px;
        gap: 24px;
    }

    .home-button button {
        min-height: 92px !important;
        font-size: 36px !important;
    }
}


/* HOME SCREEN CENTER + BUTTON POLISH V2 */
.home-wrap {
    max-width: 820px !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 34px 18px 42px 18px !important;
    min-height: 92vh !important;
    background: black !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    align-items: center !important;
    text-align: center !important;
    box-sizing: border-box !important;
}

.home-video-wrap {
    width: 100% !important;
    max-width: 720px !important;
    margin: 38px auto 58px auto !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

.home-video-wrap video {
    width: 100% !important;
    max-width: 720px !important;
    display: block !important;
    object-fit: contain !important;
    border: 1px solid #111111 !important;
}

.home-fallback-logo {
    color:#4DDB68 !important;
    font-size: 88px !important;
    font-weight:1000 !important;
    text-align:center !important;
    margin: 50px auto 60px auto !important;
    line-height:1 !important;
}

.home-menu {
    width: 100% !important;
    max-width: 560px !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 28px !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 auto !important;
}

.home-button {
    width: 100% !important;
    max-width: 560px !important;
    margin: 0 auto !important;
}

.home-button button {
    width: 100% !important;
    min-height: 112px !important;
    border-radius: 0 !important;
    background: #4DDB68 !important;
    color: white !important;
    font-size: 48px !important;
    font-weight: 1000 !important;
    letter-spacing: 1px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
    font-family: Georgia, 'Times New Roman', serif !important;
    text-transform: uppercase !important;
    line-height: 1 !important;
}

.home-button button .q-btn__content {
    width: 100% !important;
    justify-content: center !important;
    align-items: center !important;
    text-align: center !important;
}

.home-button.secondary button {
    background: #4DDB68 !important;
}

@media (max-width: 700px) {
    .home-wrap {
        padding: 26px 16px 36px 16px !important;
    }

    .home-video-wrap {
        max-width: 680px !important;
        margin: 28px auto 50px auto !important;
    }

    .home-menu {
        max-width: 520px !important;
        gap: 24px !important;
    }

    .home-button {
        max-width: 520px !important;
    }

    .home-button button {
        min-height: 96px !important;
        font-size: 38px !important;
    }
}

@media (max-width: 430px) {
    .home-button button {
        min-height: 86px !important;
        font-size: 31px !important;
    }
}


/* RECORD BOOK */
.record-hero {
    background:#1f2028;
    border:2px solid #333333;
    padding:18px;
    margin-bottom:18px;
    text-align:center;
}

.record-hero-title {
    color:#4DDB68;
    font-size:34px;
    font-weight:1000;
    line-height:1;
}

.record-hero-sub {
    color:white;
    font-size:14px;
    font-weight:900;
    margin-top:8px;
}

.record-grid {
    display:grid;
    grid-template-columns: repeat(2, 1fr);
    gap:10px;
    margin-bottom:18px;
}

.record-card {
    background:#1f2028;
    border:2px solid #333333;
    padding:14px 10px;
    text-align:center;
    min-height:112px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

.record-label {
    color:#aaaaaa;
    font-size:12px;
    font-weight:1000;
    line-height:1.1;
    margin-bottom:8px;
}

.record-value {
    color:#4DDB68;
    font-size:34px;
    font-weight:1000;
    line-height:1;
}

.record-detail {
    color:white;
    font-size:16px;
    font-weight:900;
    margin-top:8px;
    line-height:1.25;
}

.record-wide {
    background:#1f2028;
    border:2px solid #333333;
    padding:14px;
    margin-bottom:10px;
    color:white;
    font-size:15px;
    font-weight:900;
    line-height:1.35;
}

.record-wide strong {
    color:#4DDB68;
    font-size:22px;
}

.record-streak {
    background:#1f2028;
    border:2px solid #333333;
    padding:14px;
    margin-bottom:10px;
}

.record-streak-title {
    color:white;
    font-size:17px;
    font-weight:1000;
}

.record-streak-value {
    color:#4DDB68;
    font-size:34px;
    font-weight:1000;
    line-height:1;
    margin:6px 0;
}

.record-streak-detail {
    color:#aaaaaa;
    font-size:12px;
    font-weight:900;
    line-height:1.35;
}

.record-badge-row {
    display:grid;
    grid-template-columns: repeat(3, 1fr);
    gap:8px;
    margin-bottom:16px;
}

.record-badge {
    background:#4DDB68;
    color:black;
    text-align:center;
    padding:12px 6px;
    font-weight:1000;
    min-height:72px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

.record-badge-big {
    font-size:28px;
    line-height:1;
}

.record-badge-label {
    font-size:10px;
    line-height:1.1;
    margin-top:5px;
}

@media (max-width: 700px) {
    .record-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .record-value {
        font-size:28px;
    }
    .record-badge-row {
        grid-template-columns: repeat(3, 1fr);
    }
}


/* CUSTOM COURSE BUILDER */
.custom-grid {
    display:grid;
    grid-template-columns: 46px 1fr 82px 92px;
    gap:12px;
    align-items:end;
    margin-bottom:8px;
}

.custom-grid-header {
    color:#aaaaaa;
    font-size:10px;
    font-weight:1000;
    text-align:center;
}

.custom-hole-number {
    background:#4DDB68;
    color:white;
    height:56px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:20px;
    font-weight:1000;
}

.custom-section-note {
    background:#1f2028;
    border:2px solid #333333;
    color:white;
    padding:14px;
    font-size:15px;
    font-weight:900;
    line-height:1.4;
    margin-bottom:14px;
}

.custom-small-label {
    color:white;
    font-size:13px;
    font-weight:1000;
    margin-top:10px;
    margin-bottom:4px;
}

.custom-row-wrap {
    background:#111111;
    border:1px solid #222222;
    padding:8px;
    margin-bottom:7px;
}

@media (max-width: 700px) {
    .custom-grid {
        grid-template-columns: 40px 1fr 72px 78px;
        gap:5px;
    }

    .custom-hole-number {
        height:52px;
        font-size:18px;
    }

    .custom-grid-header {
        font-size:9px;
    }
}


/* GLOBAL MOBILE WIDTH SAFETY */
html, body {
    width: 100% !important;
    max-width: 100% !important;
    overflow-x: hidden !important;
}

.q-page, .nicegui-content, .q-layout, .q-page-container {
    width: 100% !important;
    max-width: 100vw !important;
    overflow-x: hidden !important;
}

.main-wrap,
.home-wrap {
    width: 100% !important;
    max-width: 100vw !important;
    box-sizing: border-box !important;
    overflow-x: hidden !important;
}

* {
    box-sizing: border-box !important;
}

img,
video {
    max-width: 100% !important;
}

.q-field,
.q-select,
.q-input,
.q-btn,
button {
    max-width: 100% !important;
}

.w-full {
    max-width: 100% !important;
}

/* Prevent wide rows from pushing the screen sideways */
.q-row,
.row {
    max-width: 100% !important;
    overflow-x: hidden !important;
}

/* Scorecard and stats grids stay inside phone width */
.main-grid,
.tile-grid,
.analytics-grid,
record-grid,
.score-type-grid,
.par-grid,
.matrix-grid,
.stats-tee-layout,
.custom-grid {
    width: 100% !important;
    max-width: 100% !important;
}

/* Tee matrix can shrink instead of overflowing */
.stats-tee-layout {
    grid-template-columns: minmax(0, 1fr) 92px !important;
    gap: 5px !important;
}

.stats-tee-grid-left {
    min-width: 0 !important;
    width: 100% !important;
}

.stats-tee-row-totals {
    min-width: 0 !important;
}

.stats-tee-cell {
    min-width: 0 !important;
}

/* Smaller phone-specific protection */
@media (max-width: 430px) {
    .main-wrap {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }

    .title {
        font-size: 42px !important;
    }

    .section-title {
        font-size: 32px !important;
    }

    .stats-tee-layout {
        grid-template-columns: minmax(0, 1fr) 74px !important;
        gap: 4px !important;
    }

    .stats-tee-grid-left {
        gap: 3px !important;
    }

    .stats-tee-cell {
        min-height: 62px !important;
        padding: 3px 1px !important;
    }

    .stats-tee-quality {
        font-size: 7.5px !important;
    }

    .stats-tee-percent {
        font-size: 18px !important;
    }

    .stats-tee-count {
        font-size: 7.5px !important;
    }

    .stats-tee-row-total-box .stats-tee-quality {
        font-size: 7px !important;
    }

    .stats-tee-row-total-box .stats-tee-percent {
        font-size: 17px !important;
    }

    .matrix-value {
        font-size: 17px !important;
    }

    .matrix-label {
        font-size: 7px !important;
    }

    .custom-grid {
        grid-template-columns: 34px minmax(0, 1fr) 58px 62px !important;
        gap: 4px !important;
    }
}


/* SCORE BY HOLE DISTANCE */
.distance-chart {
    background: #000000;
    border: 1px solid #333333;
    padding: 14px 8px 12px 8px;
    margin-bottom: 22px;
    color: #bbbbbb;
    overflow: hidden;
}

.distance-chart-title {
    display:none;
}

.distance-bars {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    gap: 6px;
    align-items: end;
    height: 250px;
    border-bottom: 4px solid #777777;
    padding: 0 4px;
}

.distance-bar-wrap {
    height: 100%;
    display: grid;
    grid-template-rows: auto 1fr;
    align-items: end;
    justify-items: center;
    overflow: hidden;
}

.distance-bar-value {
    color: #9aa7b1;
    font-size: 23px;
    font-weight: 1000;
    line-height: 1;
    margin-bottom: 7px;
    align-self: end;
}

.distance-bar-holder {
    height: 215px;
    width: 100%;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
}

.distance-bar {
    width: 100%;
    max-width: 58px;
    min-height: 0px;
    background: #9eb8d7;
    display:block;
}

.distance-labels {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    gap: 6px;
    padding: 10px 4px 0 4px;
}

.distance-label {
    color: #ffffff;
    text-align: center;
    font-size: 16px;
    font-weight: 1000;
    line-height: 1;
}

.distance-counts {
    display: grid;
    grid-template-columns: repeat(9, 1fr);
    gap: 6px;
    padding: 6px 4px 0 4px;
    margin-left: 0;
}

.distance-count {
    color: #bbbbbb;
    text-align:center;
    font-size: 10px;
    font-weight: 1000;
    line-height:1;
}

.distance-count-title {
    color:#aaaaaa;
    font-size:10px;
    font-weight:1000;
    text-align:left;
    margin-top: 8px;
    padding-left: 4px;
}

@media (max-width: 430px) {
    .distance-chart {
        padding: 12px 4px 10px 4px;
    }

    .distance-bars {
        height: 210px;
        gap: 3px;
    }

    .distance-bar-holder {
        height: 178px;
    }

    .distance-bar-value {
        font-size: 15px;
        margin-bottom: 5px;
    }

    .distance-label {
        font-size: 10px;
    }

    .distance-count {
        font-size: 8px;
    }

    .distance-count-title {
        font-size: 8px;
    }
}


/* SHRINK THE GAME */
.war-intro {
    background:#1f2028;
    border:2px solid #333333;
    color:white;
    padding:16px;
    font-size:16px;
    font-weight:900;
    line-height:1.35;
    margin-bottom:18px;
}

.war-grid {
    display:grid;
    grid-template-columns: repeat(2, 1fr);
    gap:10px;
    margin-bottom:18px;
}

.war-card {
    background:#1f2028;
    border:2px solid #333333;
    padding:16px 10px;
    text-align:center;
    min-height:132px;
    display:flex;
    flex-direction:column;
    justify-content:center;
}

.war-title {
    color:#4DDB68;
    font-size:24px;
    font-weight:1000;
    line-height:1;
    margin-bottom:6px;
}

.war-holes {
    color:white;
    font-size:13px;
    font-weight:1000;
    margin-bottom:10px;
}

.war-score {
    color:white;
    font-size:42px;
    font-weight:1000;
    line-height:1;
}

.war-detail {
    color:#aaaaaa;
    font-size:16px;
    font-weight:900;
    margin-top:8px;
    line-height:1.25;
}

.war-card-best {
    border-color:#4DDB68;
}

.war-card-worst {
    border-color:#ff3529;
}

.war-card-worst .war-title {
    color:#ff3529;
}

.war-round-card {
    background:#1f2028;
    border:2px solid #333333;
    padding:12px;
    color:white;
    font-size:14px;
    font-weight:900;
    line-height:1.35;
    margin-bottom:9px;
}

.war-round-line {
    color:#aaaaaa;
    font-size:12px;
    margin-top:4px;
}

@media (max-width: 430px) {
    .war-grid {
        grid-template-columns: repeat(2, 1fr);
        gap:8px;
    }

    .war-title {
        font-size:20px;
    }

    .war-score {
        font-size:34px;
    }

    .war-card {
        min-height:120px;
        padding:12px 6px;
    }
}


/* FORCE HOME BUTTONS GREEN */
.home-button button,
.home-button.secondary button,
.home-button .q-btn,
.home-button.secondary .q-btn {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
    color: white !important;
}

/* FRONT 9 BACK 9 SPLIT */
.split-section {
    margin-top: 20px;
    margin-bottom: 24px;
}

.split-wrap {
    display:grid;
    grid-template-columns: 1fr 1.35fr 1fr;
    gap:12px;
    align-items:center;
    margin-bottom:18px;
}

.split-card {
    border:3px solid #333333;
    background:white;
    color:#222;
    border-radius:18px;
    overflow:hidden;
    text-align:center;
    min-height:146px;
    box-shadow:0 10px 20px rgba(0,0,0,.25);
}

.split-card-front {
    border-color:#42677a;
}

.split-card-back {
    border-color:#9fbc4e;
}

.split-card-title {
    color:white;
    font-size:26px;
    font-weight:900;
    padding:12px 4px;
}

.split-front-title {
    background:#42677a;
}

.split-back-title {
    background:#9fbc4e;
}

.split-card-score {
    font-size:38px;
    font-weight:1000;
    line-height:1;
    margin-top:18px;
}

.split-card-relation {
    font-size:24px;
    font-weight:1000;
    margin-top:6px;
}

.split-front-color {
    color:#42677a;
}

.split-back-color {
    color:#9fbc4e;
}

.split-donut {
    width:230px;
    height:230px;
    border-radius:50%;
    margin:0 auto;
    display:flex;
    align-items:center;
    justify-content:center;
}

.split-donut-inner {
    width:142px;
    height:142px;
    border-radius:50%;
    background:black;
    border:4px solid #111111;
    display:flex;
    align-items:center;
    justify-content:center;
    text-align:center;
    flex-direction:column;
}

.split-donut-label {
    color:#aaaaaa;
    font-size:22px;
    font-weight:900;
}

.split-donut-score {
    color:white;
    font-size:38px;
    font-weight:1000;
    line-height:1;
    margin-top:4px;
}

.split-donut-relation {
    color:#aaaaaa;
    font-size:22px;
    font-weight:1000;
    margin-top:6px;
}

.split-caption {
    color:#aaaaaa;
    font-size:13px;
    font-weight:900;
    text-align:center;
    line-height:1.35;
    margin-top:8px;
}

@media (max-width: 700px) {
    .split-wrap {
        grid-template-columns: 1fr;
    }

    .split-donut {
        width:220px;
        height:220px;
        order:-1;
    }
}


/* COMPACT FRONT/BACK SPLIT */
.split-section {
    background:#050505 !important;
    border:2px solid #222222 !important;
    padding:14px 8px !important;
    margin-top:14px !important;
    margin-bottom:22px !important;
}

.split-wrap {
    display:grid !important;
    grid-template-columns: 1fr 1.25fr 1fr !important;
    gap:8px !important;
    align-items:center !important;
    margin-bottom:0 !important;
}

.split-card {
    border:2px solid #4DDB68 !important;
    background:#101010 !important;
    color:white !important;
    border-radius:14px !important;
    overflow:hidden !important;
    text-align:center !important;
    min-height:106px !important;
    box-shadow:none !important;
}

.split-card-front,
.split-card-back {
    border-color:#4DDB68 !important;
}

.split-card-title {
    color:black !important;
    background:#4DDB68 !important;
    font-size:18px !important;
    font-weight:1000 !important;
    padding:8px 2px !important;
}

.split-front-title,
.split-back-title {
    background:#4DDB68 !important;
}

.split-card-score {
    font-size:30px !important;
    font-weight:1000 !important;
    line-height:1 !important;
    margin-top:14px !important;
    color:white !important;
}

.split-card-relation {
    font-size:18px !important;
    font-weight:1000 !important;
    margin-top:5px !important;
    color:#4DDB68 !important;
}

.split-front-color,
.split-back-color {
    color:inherit !important;
}

.split-donut {
    width:168px !important;
    height:168px !important;
    border-radius:50% !important;
    margin:0 auto !important;
}

.split-donut-inner {
    width:104px !important;
    height:104px !important;
    border-radius:50% !important;
    background:black !important;
    border:3px solid #111111 !important;
}

.split-donut-label {
    color:#aaaaaa !important;
    font-size:16px !important;
    font-weight:900 !important;
}

.split-donut-score {
    color:white !important;
    font-size:30px !important;
    font-weight:1000 !important;
    line-height:1 !important;
    margin-top:3px !important;
}

.split-donut-relation {
    color:#4DDB68 !important;
    font-size:17px !important;
    font-weight:1000 !important;
    margin-top:4px !important;
}

.split-caption {
    display:none !important;
}

@media (max-width: 700px) {
    .split-section {
        padding:12px 5px !important;
    }

    .split-wrap {
        grid-template-columns: 1fr 1.12fr 1fr !important;
        gap:5px !important;
    }

    .split-card {
        min-height:92px !important;
        border-radius:10px !important;
    }

    .split-card-title {
        font-size:14px !important;
        padding:7px 2px !important;
    }

    .split-card-score {
        font-size:25px !important;
        margin-top:12px !important;
    }

    .split-card-relation {
        font-size:15px !important;
    }

    .split-donut {
        width:132px !important;
        height:132px !important;
    }

    .split-donut-inner {
        width:82px !important;
        height:82px !important;
    }

    .split-donut-label {
        font-size:12px !important;
    }

    .split-donut-score {
        font-size:23px !important;
    }

    .split-donut-relation {
        font-size:13px !important;
    }
}

@media (max-width: 430px) {
    .split-wrap {
        grid-template-columns: 1fr 1.05fr 1fr !important;
        gap:4px !important;
    }

    .split-card {
        min-height:82px !important;
    }

    .split-card-title {
        font-size:12px !important;
        padding:6px 1px !important;
    }

    .split-card-score {
        font-size:21px !important;
        margin-top:10px !important;
    }

    .split-card-relation {
        font-size:13px !important;
    }

    .split-donut {
        width:108px !important;
        height:108px !important;
    }

    .split-donut-inner {
        width:68px !important;
        height:68px !important;
    }

    .split-donut-label {
        font-size:10px !important;
    }

    .split-donut-score {
        font-size:19px !important;
    }

    .split-donut-relation {
        font-size:11px !important;
    }
}


/* GIR BY ROUND CHART */
.gir-round-chart {
    background:#000000;
    border:1px solid #333333;
    padding:14px 8px 12px 8px;
    margin-bottom:22px;
    color:#bbbbbb;
    overflow:hidden;
}

.gir-chart-area {
    display:grid;
    grid-template-columns: 1fr 44px;
    gap:12px;
    align-items:stretch;
}

.gir-bars {
    display:grid;
    grid-auto-flow:column;
    grid-auto-columns:minmax(42px, 1fr);
    gap:12px;
    align-items:end;
    height:240px;
    border-bottom:4px solid #777777;
    background:
        linear-gradient(to top, transparent 19%, rgba(255,255,255,.18) 20%, transparent 21%),
        linear-gradient(to top, transparent 39%, rgba(255,255,255,.18) 40%, transparent 41%),
        linear-gradient(to top, transparent 59%, rgba(255,255,255,.18) 60%, transparent 61%),
        linear-gradient(to top, transparent 79%, rgba(255,255,255,.18) 80%, transparent 81%);
    overflow-x:auto;
    padding:0 4px;
}

.gir-y-axis {
    display:grid;
    grid-template-rows: repeat(6, 1fr);
    height:240px;
    color:#aaaaaa;
    font-size:13px;
    font-weight:1000;
    text-align:right;
    align-items:center;
}

.gir-bar-wrap {
    height:100%;
    display:flex;
    flex-direction:column;
    justify-content:flex-end;
    align-items:center;
    min-width:34px;
}

.gir-bar-value {
    color:#9aa7b1;
    font-size:13px;
    font-weight:1000;
    line-height:1;
    margin-bottom:5px;
}

.gir-bar {
    width:100%;
    max-width:52px;
    min-height:4px;
    background:#9eb8d7;
    display:flex;
    align-items:flex-end;
    justify-content:center;
    padding-bottom:5px;
    box-sizing:border-box;
}

.gir-bar-score {
    color:white;
    font-size:16px;
    font-weight:1000;
    line-height:1;
    writing-mode:horizontal-tb;
}

.gir-labels {
    display:grid;
    grid-auto-flow:column;
    grid-auto-columns:minmax(42px, 1fr);
    gap:12px;
    padding:10px 50px 0 4px;
    overflow-x:auto;
}

.gir-date-label {
    color:#ffffff;
    text-align:center;
    font-size:9px;
    font-weight:1000;
    line-height:1.05;
    min-width:34px;
}

.gir-chart-note {
    color:#aaaaaa;
    font-size:10px;
    font-weight:900;
    margin-top:8px;
    text-align:center;
}

@media (max-width: 430px) {
    .gir-chart-area {
        grid-template-columns: 1fr 34px;
    }

    .gir-bars {
        height:210px;
        grid-auto-columns:minmax(30px, 1fr);
        gap:4px;
    }

    .gir-y-axis {
        height:210px;
        font-size:10px;
    }

    .gir-bar-value {
        font-size:10px;
    }

    .gir-bar-score {
        font-size:9px;
    }

    .gir-date-label {
        font-size:8px;
    }

    .gir-labels {
        grid-auto-columns:minmax(30px, 1fr);
        gap:4px;
        padding-right:40px;
    }
}


/* GIR CHART BAR SEPARATION FIX */
.gir-bars {
    display: grid !important;
    grid-auto-flow: column !important;
    grid-auto-columns: minmax(42px, 1fr) !important;
    gap: 14px !important;
    column-gap: 14px !important;
    align-items: end !important;
    padding: 0 10px !important;
}

.gir-bar-wrap {
    min-width: 42px !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

.gir-bar {
    width: 82% !important;
    max-width: 46px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

.gir-bar-score {
    font-size: 17px !important;
    font-weight: 1000 !important;
}

.gir-labels {
    display: grid !important;
    grid-auto-flow: column !important;
    grid-auto-columns: minmax(42px, 1fr) !important;
    gap: 14px !important;
    column-gap: 14px !important;
    padding-left: 10px !important;
}

@media (max-width: 430px) {
    .gir-bars {
        grid-auto-columns: minmax(34px, 1fr) !important;
        gap: 9px !important;
        column-gap: 9px !important;
        padding: 0 8px !important;
    }

    .gir-bar-wrap {
        min-width: 34px !important;
    }

    .gir-bar {
        width: 76% !important;
        max-width: 34px !important;
    }

    .gir-bar-score {
        font-size: 14px !important;
    }

    .gir-labels {
        grid-auto-columns: minmax(34px, 1fr) !important;
        gap: 9px !important;
        column-gap: 9px !important;
        padding-left: 8px !important;
    }
}


/* HOME GRAPHIC */
.home-graphic-wrap {
    width: 100% !important;
    max-width: 720px !important;
    margin: 34px auto 54px auto !important;
    display:flex !important;
    justify-content:center !important;
    align-items:center !important;
}

.home-graphic-wrap img {
    width: 100% !important;
    max-width: 720px !important;
    height:auto !important;
    object-fit:contain !important;
    display:block !important;
}


/* GRAPHIC BUTTONS */
.graphic-button {
    width: 100% !important;
    max-width: 560px !important;
    min-height: 104px !important;
    border-radius: 0 !important;
    border: none !important;
    box-shadow: none !important;
    background-size: contain !important;
    background-repeat: no-repeat !important;
    background-position: center !important;
    background-color: transparent !important;
    margin: 0 auto 12px auto !important;
    padding: 0 !important;
    display: block !important;
}

.graphic-button button,
.graphic-button .q-btn {
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
    border: none !important;
    width: 100% !important;
    min-height: 104px !important;
}

.graphic-button .q-btn__content {
    opacity: 0 !important;
}

.home-menu .graphic-button {
    max-width: 560px !important;
    min-height: 104px !important;
    margin-bottom: 16px !important;
}

@media (max-width: 700px) {
    .graphic-button,
    .graphic-button button,
    .graphic-button .q-btn {
        min-height: 86px !important;
    }

    .home-menu .graphic-button {
        min-height: 86px !important;
    }
}

@media (max-width: 430px) {
    .graphic-button,
    .graphic-button button,
    .graphic-button .q-btn {
        min-height: 68px !important;
    }

    .home-menu .graphic-button {
        min-height: 68px !important;
    }
}


/* SAFE GRAPHIC BUTTONS */
.graphic-button {
    width: 100% !important;
    max-width: 620px !important;
    height: 82px !important;
    min-height: 82px !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    background-color: transparent !important;
    margin: 0 auto 14px auto !important;
    padding: 0 !important;
    display: block !important;
}

.graphic-button .q-btn__content {
    opacity: 0 !important;
}

.home-menu .graphic-button {
    max-width: 620px !important;
}

.home-graphic-wrap {
    width: 100% !important;
    max-width: 820px !important;
    margin: 26px auto 42px auto !important;
}

.home-graphic-wrap img {
    width: 100% !important;
    max-width: 820px !important;
    height: auto !important;
    display: block !important;
    object-fit: contain !important;
}

@media (max-width: 430px) {
    .graphic-button {
        height: 56px !important;
        min-height: 56px !important;
        max-width: 96vw !important;
    }
}


/* START ROUND SCREEN CLEANUP */
.start-button button,
.start-button .q-btn,
.start-button {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    box-shadow: none !important;
}

.start-button.secondary button,
.start-button.secondary .q-btn,
.start-button.secondary {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
    color: white !important;
}

.start-home-small {
    max-width: 220px !important;
    min-height: 50px !important;
    height: 50px !important;
    margin-top: 12px !important;
}

.start-home-small button,
.start-home-small .q-btn {
    min-height: 50px !important;
    height: 50px !important;
    font-size: 22px !important;
}

.start-day-select {
    width: 118px !important;
    min-width: 118px !important;
}

.start-year-select {
    width: 154px !important;
    min-width: 154px !important;
}

.custom-section-note {
    padding: 10px 14px !important;
    min-height: 0 !important;
    margin-bottom: 12px !important;
}

.start-round-spacer {
    height: 16px !important;
}

@media (max-width: 430px) {
    .start-day-select {
        width: 92px !important;
        min-width: 92px !important;
    }

    .start-year-select {
        width: 116px !important;
        min-width: 116px !important;
    }

    .start-home-small {
        max-width: 170px !important;
        min-height: 44px !important;
        height: 44px !important;
    }

    .start-home-small button,
    .start-home-small .q-btn {
        min-height: 44px !important;
        height: 44px !important;
        font-size: 18px !important;
    }
}


/* REGULAR BUTTON RESET - NO BLUE BUTTONS */
.q-btn,
button,
.start-button,
.start-button.secondary,
.home-button,
.home-button.secondary {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 4px !important;
    font-weight: 900 !important;
}

.q-btn .q-btn__content,
button .q-btn__content {
    color: white !important;
}

.home-button,
.home-button.secondary {
    width: 100% !important;
    max-width: 560px !important;
    min-height: 82px !important;
    height: 82px !important;
    font-size: 32px !important;
    margin: 0 auto 18px auto !important;
}

.start-button,
.start-button.secondary {
    min-height: 48px !important;
    height: auto !important;
    font-size: 18px !important;
    padding: 10px 18px !important;
    margin: 8px 0 !important;
}

.start-button.dark,
.home-button.dark {
    background: #1f2028 !important;
    background-color: #1f2028 !important;
    border: 1px solid #333333 !important;
}

/* Disable any leftover graphic button styling */
.graphic-button {
    background-image: none !important;
    background-color: #4DDB68 !important;
    color: white !important;
}

.graphic-button .q-btn__content {
    opacity: 1 !important;
}

@media (max-width: 430px) {
    .home-button,
    .home-button.secondary {
        min-height: 66px !important;
        height: 66px !important;
        font-size: 24px !important;
    }

    .start-button,
    .start-button.secondary {
        font-size: 15px !important;
    }
}


/* BUTTON + CUSTOM COURSE BUILDER CLEANUP */
.q-btn,
button,
.start-button,
.start-button.secondary,
.home-button,
.home-button.secondary {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    box-shadow: none !important;
}

.q-btn.bg-primary,
.bg-primary,
.q-btn--standard {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
}

.button-row-spaced {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
    align-items: center !important;
}

.button-row-spaced .q-btn {
    margin: 0 !important;
}

.custom-grid {
    display:grid !important;
    grid-template-columns: 56px 230px 96px 116px !important;
    gap:10px !important;
    align-items:center !important;
    margin-bottom:10px !important;
}

.custom-hole-number {
    height:64px !important;
    min-height:64px !important;
    font-size:28px !important;
    font-weight:1000 !important;
}

.custom-grid .q-field,
.custom-grid .q-field__control {
    height:64px !important;
    min-height:64px !important;
}

.custom-grid .q-field__native,
.custom-grid input,
.custom-grid .q-select__dropdown-icon {
    font-size:26px !important;
    font-weight:900 !important;
    color:white !important;
}

.custom-grid-header {
    font-size:12px !important;
    font-weight:1000 !important;
}

@media (max-width: 700px) {
    .custom-grid {
        grid-template-columns: 48px minmax(120px, 1fr) 76px 88px !important;
        gap:7px !important;
    }

    .custom-hole-number {
        height:58px !important;
        min-height:58px !important;
        font-size:24px !important;
    }

    .custom-grid .q-field,
    .custom-grid .q-field__control {
        height:58px !important;
        min-height:58px !important;
    }

    .custom-grid .q-field__native,
    .custom-grid input,
    .custom-grid .q-select__dropdown-icon {
        font-size:21px !important;
    }
}

@media (max-width: 430px) {
    .custom-grid {
        grid-template-columns: 42px minmax(92px, 1fr) 66px 76px !important;
        gap:5px !important;
    }

    .custom-hole-number {
        height:54px !important;
        min-height:54px !important;
        font-size:22px !important;
    }

    .custom-grid .q-field,
    .custom-grid .q-field__control {
        height:54px !important;
        min-height:54px !important;
    }

    .custom-grid .q-field__native,
    .custom-grid input,
    .custom-grid .q-select__dropdown-icon {
        font-size:18px !important;
    }
}


/* TWO-COLUMN CUSTOM COURSE HOLE GRID */
.custom-hole-columns {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 14px !important;
    align-items: start !important;
    width: 100% !important;
}

.custom-hole-column {
    width: 100% !important;
    min-width: 0 !important;
}

.custom-hole-column-title {
    color: #4DDB68 !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    margin: 8px 0 10px 0 !important;
}

.custom-hole-columns .custom-grid {
    grid-template-columns: 42px minmax(82px, 1fr) 62px 70px !important;
    gap: 5px !important;
    margin-bottom: 8px !important;
}

.custom-hole-columns .custom-hole-number {
    height: 50px !important;
    min-height: 50px !important;
    font-size: 21px !important;
}

.custom-hole-columns .q-field,
.custom-hole-columns .q-field__control {
    height: 50px !important;
    min-height: 50px !important;
}

.custom-hole-columns .q-field__native,
.custom-hole-columns input,
.custom-hole-columns .q-select__dropdown-icon {
    font-size: 17px !important;
    font-weight: 900 !important;
}

@media (max-width: 700px) {
    .custom-hole-columns {
        grid-template-columns: 1fr 1fr !important;
        gap: 8px !important;
    }

    .custom-hole-columns .custom-grid {
        grid-template-columns: 34px minmax(62px, 1fr) 52px 58px !important;
        gap: 4px !important;
    }

    .custom-hole-columns .custom-hole-number {
        height: 46px !important;
        min-height: 46px !important;
        font-size: 18px !important;
    }

    .custom-hole-columns .q-field,
    .custom-hole-columns .q-field__control {
        height: 46px !important;
        min-height: 46px !important;
    }

    .custom-hole-columns .q-field__native,
    .custom-hole-columns input,
    .custom-hole-columns .q-select__dropdown-icon {
        font-size: 15px !important;
    }

    .custom-grid-header {
        font-size: 8px !important;
    }

    .custom-hole-column-title {
        font-size: 18px !important;
    }
}

@media (max-width: 430px) {
    .custom-hole-columns {
        gap: 6px !important;
    }

    .custom-hole-columns .custom-grid {
        grid-template-columns: 30px minmax(50px, 1fr) 46px 50px !important;
        gap: 3px !important;
    }

    .custom-hole-columns .custom-hole-number {
        height: 42px !important;
        min-height: 42px !important;
        font-size: 16px !important;
    }

    .custom-hole-columns .q-field,
    .custom-hole-columns .q-field__control {
        height: 42px !important;
        min-height: 42px !important;
    }

    .custom-hole-columns .q-field__native,
    .custom-hole-columns input,
    .custom-hole-columns .q-select__dropdown-icon {
        font-size: 13px !important;
    }
}


/* SAFE ENTRY TEE GRID CLEANUP */
.tee-entry-heading {
    color: white !important;
    font-size: 42px !important;
    font-weight: 1000 !important;
    margin: 22px 0 16px 0 !important;
    text-align: left !important;
}

.tee-grid {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 7px !important;
    width: 100% !important;
}

.tee-grid > div {
    display: grid !important;
    grid-template-rows: auto repeat(5, 1fr) !important;
    gap: 7px !important;
    min-width: 0 !important;
}

.tee-col-title {
    color: white !important;
    font-size: 13px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    margin-bottom: 2px !important;
}

.tee-btn {
    width: 100% !important;
    height: 62px !important;
    min-height: 62px !important;
    border-radius: 5px !important;
    color: white !important;
    font-size: 15px !important;
    font-weight: 1000 !important;
    line-height: 1.05 !important;
    padding: 2px !important;
    white-space: normal !important;
    text-align: center !important;
    box-shadow: none !important;
}

.tee-btn .q-btn__content {
    color: white !important;
    font-weight: 1000 !important;
    text-align: center !important;
}

.tee-selected {
    outline: 4px solid #00ff26 !important;
    outline-offset: -4px !important;
    filter: brightness(1.15) !important;
}

.location-title {
    display: none !important;
}

@media (max-width: 700px) {
    .tee-entry-heading {
        font-size: 34px !important;
    }

    .tee-grid,
    .tee-grid > div {
        gap: 5px !important;
    }

    .tee-col-title {
        font-size: 10px !important;
    }

    .tee-btn {
        height: 54px !important;
        min-height: 54px !important;
        font-size: 11px !important;
    }
}

@media (max-width: 430px) {
    .tee-entry-heading {
        font-size: 28px !important;
    }

    .tee-grid,
    .tee-grid > div {
        gap: 4px !important;
    }

    .tee-col-title {
        font-size: 8px !important;
    }

    .tee-btn {
        height: 48px !important;
        min-height: 48px !important;
        font-size: 9px !important;
    }
}


/* TEE GRID COLUMN LABELS + FIR/GIR ENTRY */
.tee-col-title {
    display: block !important;
    color: white !important;
    font-size: 13px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    margin-bottom: 6px !important;
    min-height: 18px !important;
}

.fairway-green-section {
    margin-top: 20px !important;
    margin-bottom: 18px !important;
}

.fairway-green-title {
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
    margin-bottom: 10px !important;
    text-align: left !important;
}

.fairway-green-buttons {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 10px !important;
    width: 100% !important;
}

.fairway-green-btn {
    min-height: 64px !important;
    height: 64px !important;
    border-radius: 4px !important;
    color: white !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
    border: none !important;
}

.fairway-green-btn .q-btn__content {
    color: white !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
}

.fairway-green-btn-no {
    background: #ff3529 !important;
    background-color: #ff3529 !important;
}

.fairway-green-btn-yes {
    background: #4DDB68 !important;
    background-color: #4DDB68 !important;
}

.fairway-green-btn-inactive {
    filter: brightness(.42) !important;
}

@media (max-width: 430px) {
    .tee-col-title {
        font-size: 9px !important;
    }

    .fairway-green-title {
        font-size: 24px !important;
    }

    .fairway-green-btn {
        min-height: 54px !important;
        height: 54px !important;
        font-size: 20px !important;
    }

    .fairway-green-btn .q-btn__content {
        font-size: 20px !important;
    }
}


/* FIR / GIR QUESTION MATCHES SCORING ZONE STYLE */
.tee-col-title {
    color: white !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    margin-bottom: 12px !important;
    min-height: 26px !important;
}

.fir-gir-question-wrap {
    margin-top: 28px !important;
    margin-bottom: 22px !important;
}

.fir-gir-question-title {
    color: white !important;
    font-size: 34px !important;
    font-weight: 1000 !important;
    margin-bottom: 14px !important;
    text-align: left !important;
}

.fir-gir-buttons {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 14px !important;
    width: 100% !important;
}

.fir-gir-button {
    min-height: 92px !important;
    height: 92px !important;
    border-radius: 0 !important;
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
    border: none !important;
}

.fir-gir-button .q-btn__content {
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
}

.fir-gir-yes {
    background: #4CAF50 !important;
    background-color: #4CAF50 !important;
}

.fir-gir-no {
    background: #F83A32 !important;
    background-color: #F83A32 !important;
}

.fir-gir-inactive {
    filter: brightness(.42) !important;
}

@media (max-width: 700px) {
    .tee-col-title {
        font-size: 15px !important;
    }

    .fir-gir-question-title {
        font-size: 28px !important;
    }

    .fir-gir-button {
        min-height: 76px !important;
        height: 76px !important;
        font-size: 25px !important;
    }

    .fir-gir-button .q-btn__content {
        font-size: 25px !important;
    }
}

@media (max-width: 430px) {
    .tee-col-title {
        font-size: 12px !important;
    }

    .fir-gir-question-title {
        font-size: 23px !important;
    }

    .fir-gir-button {
        min-height: 62px !important;
        height: 62px !important;
        font-size: 20px !important;
    }

    .fir-gir-button .q-btn__content {
        font-size: 20px !important;
    }
}


/* DIRECT FIR/GIR QUESTION BLOCK */
.direct-fir-gir-wrap {
    margin-top: 28px !important;
    margin-bottom: 28px !important;
}

.direct-fir-gir-title {
    color: white !important;
    font-size: 34px !important;
    font-weight: 1000 !important;
    margin-bottom: 14px !important;
    text-align: left !important;
}

.direct-fir-gir-buttons {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 14px !important;
    width: 100% !important;
}

.direct-fir-gir-btn {
    min-height: 86px !important;
    height: 86px !important;
    border-radius: 0 !important;
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
    border: none !important;
}

.direct-fir-gir-btn .q-btn__content {
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
}

.direct-fir-gir-yes {
    background: #4CAF50 !important;
    background-color: #4CAF50 !important;
}

.direct-fir-gir-no {
    background: #F83A32 !important;
    background-color: #F83A32 !important;
}

.direct-fir-gir-inactive {
    filter: brightness(.42) !important;
}

@media (max-width: 430px) {
    .direct-fir-gir-title {
        font-size: 23px !important;
    }

    .direct-fir-gir-btn {
        min-height: 62px !important;
        height: 62px !important;
        font-size: 20px !important;
    }

    .direct-fir-gir-btn .q-btn__content {
        font-size: 20px !important;
    }
}


/* FIR/GIR STYLE MATCH + TEE GRID SPACING TIGHTEN */
.tee-entry-heading {
    margin-bottom: 12px !important;
}

.tee-col-title {
    margin-bottom: 4px !important;
}

.tee-grid,
.tee-grid > div {
    gap: 5px !important;
}

.tee-btn {
    height: 56px !important;
    min-height: 56px !important;
}

.selected-note {
    margin-top: 12px !important;
    margin-bottom: 10px !important;
}

.direct-fir-gir-wrap {
    margin-top: 14px !important;
    margin-bottom: 20px !important;
}

.direct-fir-gir-title {
    color: white !important;
    font-size: 34px !important;
    font-weight: 1000 !important;
    margin-bottom: 12px !important;
    text-align: left !important;
}

.direct-fir-gir-buttons {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 14px !important;
    width: 100% !important;
}

.direct-fir-gir-btn {
    min-height: 82px !important;
    height: 82px !important;
    border-radius: 0 !important;
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
    border: none !important;
    filter: none !important;
    opacity: 1 !important;
}

.direct-fir-gir-btn .q-btn__content {
    color: white !important;
    font-size: 30px !important;
    font-weight: 1000 !important;
}

.direct-fir-gir-yes {
    background: #65AD59 !important;
    background-color: #65AD59 !important;
}

.direct-fir-gir-no {
    background: #E84C3D !important;
    background-color: #E84C3D !important;
}

.direct-fir-gir-inactive {
    filter: brightness(.78) !important;
    opacity: .88 !important;
}

@media (max-width: 700px) {
    .tee-btn {
        height: 50px !important;
        min-height: 50px !important;
    }

    .direct-fir-gir-title {
        font-size: 28px !important;
    }

    .direct-fir-gir-btn {
        min-height: 70px !important;
        height: 70px !important;
        font-size: 25px !important;
    }

    .direct-fir-gir-btn .q-btn__content {
        font-size: 25px !important;
    }
}

@media (max-width: 430px) {
    .tee-grid,
    .tee-grid > div {
        gap: 3px !important;
    }

    .tee-btn {
        height: 44px !important;
        min-height: 44px !important;
    }

    .selected-note {
        margin-top: 8px !important;
        margin-bottom: 8px !important;
    }

    .direct-fir-gir-title {
        font-size: 23px !important;
    }

    .direct-fir-gir-btn {
        min-height: 58px !important;
        height: 58px !important;
        font-size: 20px !important;
    }

    .direct-fir-gir-btn .q-btn__content {
        font-size: 20px !important;
    }
}


/* FINAL FIR/GIR STYLE FIX */
.selected-note {
    margin-top: 2px !important;
    margin-bottom: 2px !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

.direct-fir-gir-wrap {
    margin-top: 2px !important;
    padding-top: 0 !important;
    margin-bottom: 18px !important;
}

.direct-fir-gir-title {
    font-size: 30px !important;
    margin-top: 0 !important;
    margin-bottom: 10px !important;
    font-weight: 1000 !important;
    color: white !important;
}

.direct-fir-gir-buttons {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 10px !important;
    width: 100% !important;
}

.direct-fir-gir-btn {
    min-height: 58px !important;
    height: 58px !important;
    border-radius: 0 !important;
    border: none !important;
    box-shadow: none !important;
    color: white !important;
    font-weight: 1000 !important;
    font-size: 20px !important;
    text-transform: uppercase !important;
}

.direct-fir-gir-btn .q-btn__content {
    color: white !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
}

.direct-fir-gir-yes {
    background: #4CAF50 !important;
    background-color: #4CAF50 !important;
}

.direct-fir-gir-no {
    background: #F44336 !important;
    background-color: #F44336 !important;
}

.direct-fir-gir-inactive {
    opacity: .55 !important;
    filter: none !important;
}

@media (max-width: 430px) {
    .selected-note {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        font-size: 14px !important;
    }

    .direct-fir-gir-wrap {
        margin-top: 0 !important;
    }

    .direct-fir-gir-title {
        font-size: 20px !important;
        margin-bottom: 8px !important;
    }

    .direct-fir-gir-btn {
        min-height: 52px !important;
        height: 52px !important;
        font-size: 18px !important;
    }

    .direct-fir-gir-btn .q-btn__content {
        font-size: 18px !important;
    }
}


/* FINAL TEE GRID SPACING + FIR/GIR COLOR OVERRIDE */
.tee-grid > div {
    grid-template-rows: none !important;
    grid-auto-rows: auto !important;
}

.tee-grid {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

.selected-note {
    margin-top: 6px !important;
    margin-bottom: 6px !important;
    padding: 0 !important;
    line-height: 1.1 !important;
}

.direct-fir-gir-wrap {
    margin-top: 8px !important;
    margin-bottom: 18px !important;
    padding-top: 0 !important;
}

.direct-fir-gir-buttons {
    gap: 10px !important;
}

.direct-fir-gir-btn,
.direct-fir-gir-btn.q-btn,
.direct-fir-gir-btn button,
.direct-fir-gir-btn .q-btn {
    min-height: 58px !important;
    height: 58px !important;
    border-radius: 0 !important;
    border: none !important;
    box-shadow: none !important;
    color: white !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
    opacity: 1 !important;
    filter: none !important;
}

.direct-fir-gir-btn .q-btn__content {
    color: white !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
    opacity: 1 !important;
}

.direct-fir-gir-yes,
.direct-fir-gir-yes.q-btn {
    background: #4CAF50 !important;
    background-color: #4CAF50 !important;
}

.direct-fir-gir-no,
.direct-fir-gir-no.q-btn {
    background: #F44336 !important;
    background-color: #F44336 !important;
}

.direct-fir-gir-inactive {
    opacity: 1 !important;
    filter: none !important;
}

@media (max-width: 430px) {
    .selected-note {
        margin-top: 4px !important;
        margin-bottom: 4px !important;
    }

    .direct-fir-gir-wrap {
        margin-top: 6px !important;
    }

    .direct-fir-gir-btn,
    .direct-fir-gir-btn.q-btn {
        min-height: 52px !important;
        height: 52px !important;
        font-size: 18px !important;
    }

    .direct-fir-gir-btn .q-btn__content {
        font-size: 18px !important;
    }
}


/* ROUND HISTORY */
.history-card {
    background:#1f2028;
    border:2px solid #333333;
    padding:14px;
    margin-bottom:12px;
    color:white;
}

.history-title {
    color:white;
    font-size:20px;
    font-weight:1000;
    line-height:1.2;
    margin-bottom:6px;
}

.history-meta {
    color:#aaaaaa;
    font-size:13px;
    font-weight:900;
    line-height:1.35;
    margin-bottom:10px;
}

.history-score {
    color:#4DDB68;
    font-size:34px;
    font-weight:1000;
    line-height:1;
    margin-bottom:8px;
}

.history-actions {
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:10px;
    margin-bottom:16px;
}

.history-edit {
    background:#4DDB68 !important;
    background-color:#4DDB68 !important;
    color:white !important;
}

.history-delete {
    background:#F44336 !important;
    background-color:#F44336 !important;
    color:white !important;
}


/* ROUND SUMMARY CLEANUP */
.round-summary-actions {
    display:flex !important;
    flex-wrap:wrap !important;
    gap:14px !important;
    margin-top:14px !important;
    margin-bottom:24px !important;
}



/* ROUND SUMMARY BUTTON SPACING */
.round-summary-actions {
    display: flex !important;
    gap: 18px !important;
    margin-top: 18px !important;
    margin-bottom: 28px !important;
    align-items: center !important;
}

/* HIDE CUSTOM COURSES SECTION ON SUMMARY PAGE */
.custom-courses-summary-hide {
    display: none !important;
}


/* QUICK LOAD */
.quick-load-grid {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:10px;
    width:100%;
}

.quick-hole-card {
    background:#1f2028;
    border:2px solid #333333;
    padding:8px;
    color:white;
}

.quick-hole-title {
    color:#4DDB68;
    font-size:22px;
    font-weight:1000;
    margin-bottom:4px;
    line-height:1;
}

.quick-hole-sub {
    color:#bbbbbb;
    font-size:12px;
    font-weight:900;
    margin-bottom:6px;
}

.quick-mini-label {
    color:white;
    font-size:10px;
    font-weight:1000;
    margin-top:4px;
    margin-bottom:1px;
}

.quick-row {
    display:flex;
    gap:4px;
    width:100%;
}

.quick-row > div {
    flex:1;
}

.quick-load-grid .q-field__native,
.quick-load-grid .q-field__input {
    font-size:14px !important;
    min-height:34px !important;
}

.quick-load-grid .q-field {
    min-height:34px !important;
}

.quick-load-grid .q-field__control {
    min-height:34px !important;
    height:34px !important;
}

.quick-load-grid .q-field__marginal {
    height:34px !important;
}

.quick-save-button {
    width:100% !important;
    margin-top:16px !important;
    min-height:64px !important;
    font-size:24px !important;
    font-weight:1000 !important;
}

@media (max-width: 520px) {
    .quick-load-grid {
        grid-template-columns: 1fr 1fr;
        gap:7px;
    }

    .quick-hole-card {
        padding:6px;
    }

    .quick-hole-title {
        font-size:19px;
    }

    .quick-load-grid .q-field__native,
    .quick-load-grid .q-field__input {
        font-size:12px !important;
    }
}


/* QUICK LOAD TIGHT TABLE OVERRIDE */
.quick-load-grid {
    display:block !important;
    width:100% !important;
}

.quick-table-wrap {
    width:100%;
    overflow-x:auto;
    border:2px solid #333333;
    background:#111111;
}

.quick-load-table {
    width:100%;
    min-width:980px;
    border-collapse:collapse;
    color:white;
    font-size:10px;
    table-layout:fixed;
}

.quick-load-table th {
    background:#4DDB68;
    color:black;
    font-size:9px;
    font-weight:1000;
    padding:3px 2px;
    border:2px solid black;
    text-align:center;
    white-space:nowrap;
}

.quick-load-table td {
    background:#1f2028;
    border:1px solid #333333;
    padding:2px;
    text-align:center;
    vertical-align:middle;
}

.quick-hole-num {
    color:#4DDB68;
    font-size:15px;
    font-weight:1000;
}

.quick-static {
    color:#bbbbbb;
    font-size:10px;
    font-weight:900;
}

.quick-load-table .q-field,
.quick-load-table .q-field__control,
.quick-load-table .q-field__marginal {
    min-height:26px !important;
    height:26px !important;
}

.quick-load-table .q-field__native,
.quick-load-table .q-field__input {
    min-height:26px !important;
    height:26px !important;
    font-size:10px !important;
    padding:0 2px !important;
}

.quick-load-table .q-field__append {
    padding-left:0 !important;
}

.quick-load-table .q-field__control {
    padding:0 2px !important;
}

.quick-col-hole { width:42px; }
.quick-col-small { width:42px; }
.quick-col-med { width:64px; }
.quick-col-wide { width:82px; }
.quick-col-tiny { width:34px; }

@media (max-width: 520px) {
    .quick-load-table {
        min-width:1060px;
        font-size:9px;
    }
    .quick-load-table th {
        font-size:8px;
    }
}


/* QUICK LOAD STABLE WIDE GRID */
.quick-wide-wrap {
    width: 100%;
    max-width: 100%;
    overflow-x: auto;
    overflow-y: visible;
    border: 2px solid #333333;
    background: #111111;
    -webkit-overflow-scrolling: touch;
}

.quick-wide-grid {
    min-width: 1580px;
    display: grid;
    grid-template-columns:
        96px
        76px 76px 170px 150px 150px 76px 76px
        58px 58px 58px 58px 58px
        58px 58px 58px 58px 58px;
    color: white;
}

.quick-grid-cell {
    min-height: 58px;
    background: #1f2028;
    border: 1px solid #333333;
    padding: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    overflow: hidden;
}

.quick-grid-head {
    min-height: 54px;
    background: #4DDB68 !important;
    color: black;
    font-size: 11px;
    font-weight: 1000;
    line-height: 1;
}

.quick-sticky-cell {
    position: sticky;
    left: 0;
    z-index: 25;
    background: #111111 !important;
    border-right: 4px solid #4DDB68;
    box-shadow: 6px 0 10px rgba(0,0,0,.7);
}

.quick-sticky-head {
    z-index: 40;
    background: #4DDB68 !important;
    color: black;
}

.quick-hole-num {
    color: #4DDB68;
    font-size: 22px;
    font-weight: 1000;
    line-height: 1;
}

.quick-hole-meta {
    color: #dddddd;
    font-size: 11px;
    font-weight: 900;
    line-height: 1.2;
    margin-top: 3px;
}

.quick-wide-grid .q-field,
.quick-wide-grid .q-field__control,
.quick-wide-grid .q-field__marginal {
    min-height: 38px !important;
    height: 38px !important;
}

.quick-wide-grid .q-field__native,
.quick-wide-grid .q-field__input {
    min-height: 38px !important;
    height: 38px !important;
    font-size: 13px !important;
    padding: 0 4px !important;
}

.quick-wide-grid .q-field__append,
.quick-wide-grid .q-field__prepend {
    padding: 0 !important;
}

.quick-wide-grid .q-field__control {
    padding: 0 4px !important;
}

.quick-header-icon {
    width: 48px;
    height: 38px;
    object-fit: cover;
    display: block;
    margin: 0 auto;
    border-radius: 2px;
}

.quick-shot-select {
    font-size: 12px;
    font-weight: 1000;
    line-height: 1.1;
}


/* QUICK LOAD COMBINED SHOT GRID */
.quick-wide-grid {
    grid-template-columns:
        96px
        76px 76px 170px 230px 76px 76px
        58px 58px 58px 58px 58px
        58px 58px 58px 58px 58px !important;
    min-width: 1600px !important;
}

.quick-shot-combo {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    min-height: 64px;
}

.quick-shot-grid {
    display: grid;
    gap: 2px;
    flex: 0 0 auto;
}

.quick-shot-grid.par3 {
    grid-template-columns: repeat(5, 12px);
    grid-template-rows: repeat(5, 12px);
}

.quick-shot-grid.par45 {
    grid-template-columns: repeat(5, 12px);
    grid-template-rows: repeat(4, 12px);
}

.quick-shot-cell {
    width: 12px !important;
    height: 12px !important;
    min-width: 12px !important;
    min-height: 12px !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 1px solid #111 !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    opacity: .9 !important;
    appearance: none !important;
    -webkit-appearance: none !important;
}

.quick-shot-cell.selected {
    outline: 2px solid white !important;
    transform: scale(1.08);
    opacity: 1 !important;
}

.quick-shot-label {
    color: white;
    font-size: 12px;
    line-height: 1.08;
    font-weight: 1000;
    width: 95px;
    text-align: left;
    white-space: normal;
}

.quick-shot-label .loc {
    color: #4DDB68;
}

.quick-shot-label .qual {
    color: white;
}

@media (max-width: 520px) {
    .quick-shot-grid.par3 {
        grid-template-columns: repeat(5, 10px);
        grid-template-rows: repeat(5, 10px);
    }

    .quick-shot-grid.par45 {
        grid-template-columns: repeat(5, 10px);
        grid-template-rows: repeat(4, 10px);
    }

    .quick-shot-cell {
        width: 10px !important;
        height: 10px !important;
        min-width: 10px !important;
        min-height: 10px !important;
    }

    .quick-shot-label {
        font-size: 11px;
        width: 86px;
    }
}


/* QUICK LOAD SHOT GRID BUTTON COLOR FIX */
.quick-shot-cell,
.quick-shot-cell .q-btn,
.quick-shot-cell button {
    background-color: var(--shot-color) !important;
    background: var(--shot-color) !important;
    color: transparent !important;
    box-shadow: none !important;
}

.quick-shot-cell {
    width: 14px !important;
    height: 14px !important;
    min-width: 14px !important;
    min-height: 14px !important;
    max-width: 14px !important;
    max-height: 14px !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 1px solid #111 !important;
    border-radius: 0 !important;
    cursor: pointer !important;
    opacity: .95 !important;
    overflow: hidden !important;
}

.quick-shot-cell .q-btn__content {
    display: none !important;
}

.quick-shot-cell.selected {
    outline: 2px solid white !important;
    outline-offset: 1px !important;
    opacity: 1 !important;
    transform: scale(1.08);
}

.quick-shot-grid.par3 {
    grid-template-columns: repeat(5, 14px) !important;
    grid-template-rows: repeat(5, 14px) !important;
}

.quick-shot-grid.par45 {
    grid-template-columns: repeat(5, 14px) !important;
    grid-template-rows: repeat(4, 14px) !important;
}

@media (max-width: 520px) {
    .quick-shot-cell {
        width: 12px !important;
        height: 12px !important;
        min-width: 12px !important;
        min-height: 12px !important;
        max-width: 12px !important;
        max-height: 12px !important;
    }

    .quick-shot-grid.par3 {
        grid-template-columns: repeat(5, 12px) !important;
        grid-template-rows: repeat(5, 12px) !important;
    }

    .quick-shot-grid.par45 {
        grid-template-columns: repeat(5, 12px) !important;
        grid-template-rows: repeat(4, 12px) !important;
    }
}


/* QUICK LOAD SHOT LABEL / NO CLIP FIX */
.quick-wide-grid {
    grid-template-columns:
        96px
        76px 76px 170px 285px 76px 76px
        58px 58px 58px 58px 58px
        58px 58px 58px 58px 58px !important;
    min-width: 1660px !important;
}

.quick-grid-cell {
    overflow: visible !important;
}

.quick-shot-combo {
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 14px !important;
    min-height: 64px !important;
    padding-left: 8px !important;
    overflow: visible !important;
}

.quick-shot-label {
    color: white !important;
    font-size: 13px !important;
    line-height: 1.08 !important;
    font-weight: 1000 !important;
    width: 138px !important;
    min-width: 138px !important;
    max-width: none !important;
    text-align: left !important;
    white-space: normal !important;
    overflow: visible !important;
    word-break: normal !important;
}

.quick-shot-label .loc,
.quick-shot-label .qual {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
}

.quick-shot-label .loc {
    color: #4DDB68 !important;
}

.quick-shot-label .qual {
    color: white !important;
}


/* QUICK LOAD SAFE WHITE SELECTED CELL */
.quick-shot-combo {
    justify-content: center !important;
    gap: 0 !important;
}

.quick-shot-label {
    display: none !important;
}

.quick-shot-cell.selected,
.quick-shot-cell.selected .q-btn,
.quick-shot-cell.selected button {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 2px solid #ffffff !important;
    outline: 2px solid #ffffff !important;
    opacity: 1 !important;
}

.quick-shot-grid.par3 {
    grid-template-columns: repeat(5, 15px) !important;
    grid-template-rows: repeat(5, 15px) !important;
}

.quick-shot-grid.par45 {
    grid-template-columns: repeat(5, 15px) !important;
    grid-template-rows: repeat(4, 15px) !important;
}

.quick-shot-cell {
    width: 15px !important;
    height: 15px !important;
    min-width: 15px !important;
    min-height: 15px !important;
    max-width: 15px !important;
    max-height: 15px !important;
}

@media (max-width: 520px) {
    .quick-shot-grid.par3 {
        grid-template-columns: repeat(5, 13px) !important;
        grid-template-rows: repeat(5, 13px) !important;
    }

    .quick-shot-grid.par45 {
        grid-template-columns: repeat(5, 13px) !important;
        grid-template-rows: repeat(4, 13px) !important;
    }

    .quick-shot-cell {
        width: 13px !important;
        height: 13px !important;
        min-width: 13px !important;
        min-height: 13px !important;
        max-width: 13px !important;
        max-height: 13px !important;
    }
}


/* QUICK LOAD FUNCTIONAL WHITE SELECTION */
.quick-shot-label {
    display: none !important;
}

.quick-shot-cell.selected,
.quick-shot-cell.selected .q-btn,
.quick-shot-cell.selected button {
    background: #ffffff !important;
    background-color: #ffffff !important;
    border: 2px solid #ffffff !important;
    outline: 2px solid #ffffff !important;
    opacity: 1 !important;
}

.quick-shot-cell,
.quick-shot-cell .q-btn,
.quick-shot-cell button {
    cursor: pointer !important;
    pointer-events: auto !important;
}


/* STEP 81 REAL BUTTON SPACING FIX */
.home-menu {
    gap: 12px !important;
}

.home-button button {
    margin-bottom: 0 !important;
}

.quick-load-button-row {
    width: 100%;
    display: grid;
    grid-template-columns: 1fr 14px 1fr;
    align-items: stretch;
    margin-top: 8px;
}

.quick-load-button-row .start-button button {
    width: 100% !important;
    margin-bottom: 0 !important;
}


/* UNIVERSAL SIDE-BY-SIDE BUTTON SPACING */
.q-btn + .q-btn {
    margin-left: 12px !important;
}

button.q-btn + button.q-btn {
    margin-left: 12px !important;
}

.q-btn-group .q-btn + .q-btn {
    margin-left: 12px !important;
}

.row .q-btn + .q-btn,
.q-row .q-btn + .q-btn,
.flex .q-btn + .q-btn {
    margin-left: 12px !important;
}

/* Keep full-width stacked home/menu buttons from getting unintended left margin */
.home-menu .q-btn + .q-btn {
    margin-left: 0 !important;
}

/* Side-by-side action rows */
.button-row,
.bottom-row,
.quick-load-button-row,
.action-row {
    gap: 12px !important;
    column-gap: 12px !important;
}

/* Specific Quick Load search buttons */
.quick-load-search-actions {
    display: grid !important;
    grid-template-columns: 1fr 12px 1fr !important;
    width: 100% !important;
    align-items: stretch !important;
}

.quick-load-search-actions .q-btn {
    width: 100% !important;
    margin-left: 0 !important;
}


/* HOME SCREEN TIGHT BUTTON SPACING */
.home-menu {
    gap: 14px !important;
    row-gap: 14px !important;
}

.home-menu .home-button {
    margin: 0 !important;
}

.home-menu .q-btn {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}


/* QUICK LOAD STAGED FLOW */
.quick-load-actions {
    display: grid !important;
    grid-template-columns: 1fr 12px 1fr !important;
    width: 100% !important;
    align-items: stretch !important;
    margin-top: 8px !important;
}
.quick-load-actions .q-btn {
    width: 100% !important;
    margin-left: 0 !important;
}
.quick-lock-box {
    background:#1f2028;
    border:2px solid #333;
    padding:14px;
    margin:14px 0;
    color:white;
    font-size:18px;
    font-weight:900;
    line-height:1.25;
}


/* QUICK LOAD NUMERIC INPUTS */
.quick-num-input .q-field,
.quick-num-input .q-field__control,
.quick-num-input .q-field__marginal {
    min-height: 38px !important;
    height: 38px !important;
}

.quick-num-input .q-field__native,
.quick-num-input .q-field__input {
    min-height: 38px !important;
    height: 38px !important;
    font-size: 15px !important;
    font-weight: 900 !important;
    text-align: center !important;
    padding: 0 4px !important;
}


/* QUICK LOAD HTML SHOT GRID - STABLE */
.quick-shot-grid {
    display: grid !important;
    grid-template-columns: repeat(5, 24px) !important;
    gap: 5px !important;
    justify-content: center !important;
    align-content: center !important;
    margin: 0 auto !important;
}

.quick-shot-html-cell {
    width: 24px !important;
    height: 24px !important;
    border: 2px solid #111 !important;
    box-sizing: border-box !important;
    display: block !important;
}

.quick-shot-html-cell.selected {
    background: #ffffff !important;
    border: 3px solid #ffffff !important;
}


/* QUICK LOAD CLICKABLE DIV SHOT GRID */
.quick-shot-grid {
    display: grid !important;
    grid-template-columns: repeat(5, 24px) !important;
    gap: 5px !important;
    justify-content: center !important;
    align-content: center !important;
    margin: 0 auto !important;
}

.quick-shot-click-cell {
    width: 24px !important;
    height: 24px !important;
    border: 2px solid #111 !important;
    box-sizing: border-box !important;
    display: block !important;
    cursor: pointer !important;
    pointer-events: auto !important;
    touch-action: manipulation !important;
}

.quick-shot-click-cell.selected {
    background: #ffffff !important;
    border: 3px solid #ffffff !important;
}


/* QUICK LOAD BLANK NUMBERS CLEANUP */
.quick-num-input input {
    text-align: center !important;
}


/* DIGITAL SCORECARD PREVIEW - SAFE HTML VERSION */
.digital-card-wrap {
    background: #ffffff;
    color: #000000;
    width: 100%;
    max-width: 1180px;
    overflow-x: auto;
    padding: 24px;
    border-radius: 0;
    border: 3px solid #dddddd;
}

.digital-card-title {
    font-size: 58px;
    font-weight: 1000;
    line-height: 0.95;
    text-transform: uppercase;
    color: #000000;
    margin-bottom: 10px;
}

.digital-card-sub {
    font-size: 24px;
    font-weight: 1000;
    line-height: 1.25;
    text-transform: uppercase;
    color: #000000;
}

.digital-card-table {
    border-collapse: collapse;
    width: 1120px;
    table-layout: fixed;
    margin-top: 18px;
    font-family: Arial, sans-serif;
}

.digital-card-table th,
.digital-card-table td {
    border: 2px solid #999999;
    height: 44px;
    text-align: center;
    vertical-align: middle;
    font-weight: 900;
    font-size: 15px;
    color: #000000;
    background: #ffffff;
    padding: 2px;
}

.digital-card-table th {
    background: #ffffff;
    height: 50px;
    font-size: 13px;
}

.digital-card-hole {
    background: #007a3d !important;
    color: #ffffff !important;
    font-size: 30px !important;
    width: 50px !important;
}

.digital-card-meta {
    font-size: 12px !important;
    line-height: 1.05;
    width: 56px !important;
}

.digital-card-gray {
    background: #dddddd !important;
}

.digital-card-front-divider td {
    border-top: 8px solid #000000 !important;
}

.digital-card-totals td {
    border-top: 8px solid #000000 !important;
    background: #ffffff;
    font-size: 16px;
}

.digital-card-logo {
    text-align: right;
    font-size: 28px;
    font-weight: 1000;
    color: #007a3d;
    margin-top: 14px;
}


/* APP-WIDE MOBILE NAV FIXES */
html, body {
    touch-action: manipulation !important;
    -webkit-text-size-adjust: 100% !important;
}
input, select, textarea,
.q-field__native,
.q-field__input,
.q-select__input {
    font-size: 16px !important;
}
button, .q-btn {
    touch-action: manipulation !important;
}
.top-home-icon {
    position: fixed !important;
    top: 10px !important;
    right: 12px !important;
    z-index: 99999 !important;
    width: 46px !important;
    height: 46px !important;
    min-width: 46px !important;
    min-height: 46px !important;
    border-radius: 10px !important;
    background: #49d86a !important;
    color: #000000 !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.35) !important;
}
.top-home-icon .q-btn__content {
    font-size: 24px !important;
    line-height: 1 !important;
}
.bottom-hole-nav {
    margin-top: 24px !important;
    padding-top: 18px !important;
    border-top: 5px solid #ffffff !important;
}
.bottom-hole-nav-title {
    color: #4DDB68;
    font-weight: 1000;
    font-size: 28px;
    text-align: center;
    margin-bottom: 12px;
}
.hole-nav-row-bottom {
    display: grid !important;
    grid-template-columns: 1fr 12px 1fr !important;
    width: 100% !important;
    align-items: stretch !important;
}
.hole-nav-row-bottom .q-btn {
    width: 100% !important;
    margin-left: 0 !important;
}


/* PLAY GOLF TOP NAV CLEANUP */
:root {
    --mg-dark-green: #0b7f23;
    --mg-nav-gray: #1f2028;
}

.scorecard-screen-tight .title {
    display: none !important;
}

.scorecard-screen-tight {
    padding-top: 6px !important;
}

.scorecard-screen-tight .hole-nav {
    margin-top: 0 !important;
    margin-bottom: 6px !important;
    display: grid !important;
    grid-template-columns: 54px 1fr 54px !important;
    gap: 8px !important;
    width: 100% !important;
    align-items: center !important;
}

.scorecard-screen-tight .nav-btn,
.scorecard-screen-tight .nav-btn .q-btn,
.scorecard-screen-tight .nav-btn button {
    background: var(--mg-nav-gray) !important;
    color: #ffffff !important;
    border-radius: 0 !important;
    height: 52px !important;
    min-height: 52px !important;
    width: 54px !important;
    min-width: 54px !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
}

.scorecard-screen-tight .nav-center {
    background: var(--mg-nav-gray) !important;
    color: #ffffff !important;
    height: 52px !important;
    line-height: 52px !important;
    text-align: center !important;
    font-size: 28px !important;
    font-weight: 1000 !important;
    letter-spacing: .5px !important;
}

.scorecard-screen-tight .hole-card {
    background: #49d86a !important;
    padding: 7px 10px 10px 10px !important;
    margin-top: 0 !important;
    margin-bottom: 12px !important;
    border-radius: 0 !important;
}

.scorecard-screen-tight .hole-card .hole-title {
    display: none !important;
}

.scorecard-screen-tight .meta-grid {
    gap: 6px !important;
    margin-top: 0 !important;
}

.scorecard-screen-tight .meta-box {
    background: #000000 !important;
    border: 0 !important;
    min-height: 58px !important;
    padding: 7px 4px !important;
    color: #ffffff !important;
    font-size: 14px !important;
    line-height: 1.05 !important;
}

.scorecard-screen-tight .meta-box span {
    color: var(--mg-dark-green) !important;
    font-size: 24px !important;
    font-weight: 1000 !important;
    line-height: 1 !important;
}

.scorecard-screen-tight .bottom-hole-nav {
    margin-top: 22px !important;
    padding-top: 14px !important;
    border-top: 5px solid #ffffff !important;
}

.scorecard-screen-tight .bottom-hole-nav-title {
    display: none !important;
}

.scorecard-screen-tight .hole-nav-row-bottom {
    display: grid !important;
    grid-template-columns: 54px 1fr 54px !important;
    gap: 8px !important;
    width: 100% !important;
    align-items: center !important;
}

.scorecard-screen-tight .bottom-nav-center {
    background: var(--mg-nav-gray) !important;
    color: #ffffff !important;
    height: 52px !important;
    line-height: 52px !important;
    text-align: center !important;
    font-size: 28px !important;
    font-weight: 1000 !important;
}

.scorecard-screen-tight .bottom-nav-arrow,
.scorecard-screen-tight .bottom-nav-arrow .q-btn,
.scorecard-screen-tight .bottom-nav-arrow button {
    background: var(--mg-nav-gray) !important;
    color: #ffffff !important;
    border-radius: 0 !important;
    height: 52px !important;
    min-height: 52px !important;
    width: 54px !important;
    min-width: 54px !important;
    font-size: 20px !important;
    font-weight: 1000 !important;
    box-shadow: none !important;
}


/* PLAY GOLF NAV FINAL FIX */
.scorecard-screen-tight .hole-nav .q-btn,
.scorecard-screen-tight .hole-nav .q-btn.nav-btn,
.scorecard-screen-tight .hole-nav button,
.scorecard-screen-tight .nav-btn,
.scorecard-screen-tight .bottom-nav-arrow,
.scorecard-screen-tight .bottom-nav-arrow.q-btn,
.scorecard-screen-tight .bottom-nav-arrow button {
    background: #1f2028 !important;
    background-color: #1f2028 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
}

.scorecard-screen-tight .hole-nav .q-btn::before,
.scorecard-screen-tight .nav-btn::before,
.scorecard-screen-tight .bottom-nav-arrow::before {
    background: #1f2028 !important;
    opacity: 1 !important;
}

.scorecard-screen-tight .hole-card {
    display: flex !important;
    align-items: center !important;
    min-height: 76px !important;
    padding-top: 10px !important;
    padding-bottom: 10px !important;
}

.scorecard-screen-tight .meta-grid {
    width: 100% !important;
    transform: translateY(4px) !important;
}

.scorecard-screen-tight .meta-box {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
}


/* PLAY GOLF SCORE / PUTTS DIRECT ENTRY - MOBILE COMPACT */
.scorecard-screen-tight .main-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 14px !important;
    width: 100% !important;
    margin-top: 12px !important;
}

.scorecard-screen-tight .stat-card {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 0 !important;
    background: #000000 !important;
    border: 0 !important;
    padding: 0 !important;
    height: 112px !important;
    min-height: 112px !important;
    overflow: hidden !important;
}

.scorecard-screen-tight .stat-card .main-img,
.scorecard-screen-tight .stat-card .fake-image {
    width: 100% !important;
    height: 112px !important;
    object-fit: contain !important;
    object-position: center !important;
    background: #1f2028 !important;
    display: block !important;
}

.scorecard-screen-tight .score-putts-entry-box {
    background: #1f2028 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    height: 112px !important;
    min-height: 112px !important;
}

.scorecard-screen-tight .score-putts-entry-box .q-field,
.scorecard-screen-tight .score-putts-entry-box .q-field__control {
    min-height: 112px !important;
    height: 112px !important;
    background: #1f2028 !important;
    border: 0 !important;
    box-shadow: none !important;
}

.scorecard-screen-tight .score-putts-entry-box .q-field__native,
.scorecard-screen-tight .score-putts-entry-box input {
    color: #ffffff !important;
    font-size: 56px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    line-height: 1 !important;
    padding: 0 !important;
}

.scorecard-screen-tight .score-putts-entry-box .q-field__control:before,
.scorecard-screen-tight .score-putts-entry-box .q-field__control:after {
    display: none !important;
}


/* FOUR TILE SCORE / PUTTS MOBILE LAYOUT */
.scorecard-screen-tight .score-putts-four-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr 1fr 1fr !important;
    gap: 0 !important;
    width: 100% !important;
    margin-top: 12px !important;
    overflow: hidden !important;
}

.scorecard-screen-tight .score-putts-icon {
    width: 100% !important;
    height: 112px !important;
    object-fit: cover !important;
    object-position: center !important;
    display: block !important;
    background: #000000 !important;
}

.scorecard-screen-tight .score-putts-four-grid .score-putts-entry-box {
    height: 112px !important;
    min-height: 112px !important;
    background: #1f2028 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
}

.scorecard-screen-tight .score-putts-four-grid .q-field,
.scorecard-screen-tight .score-putts-four-grid .q-field__control {
    background: #1f2028 !important;
    height: 112px !important;
    min-height: 112px !important;
    border: 0 !important;
    box-shadow: none !important;
}

.scorecard-screen-tight .score-putts-four-grid input,
.scorecard-screen-tight .score-putts-four-grid .q-field__native {
    color: #ffffff !important;
    font-size: 58px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    padding: 0 !important;
}

.scorecard-screen-tight .score-putts-four-grid .q-field__control:before,
.scorecard-screen-tight .score-putts-four-grid .q-field__control:after {
    display: none !important;
}


/* SCORE / PUTTS TRUE FOUR-SQUARE MOBILE LAYOUT */
.scorecard-screen-tight .score-putts-four-grid {
    display: grid !important;
    grid-template-columns: repeat(4, 1fr) !important;
    gap: 0 !important;
    width: 100% !important;
    margin-top: 12px !important;
    overflow: hidden !important;
}

.scorecard-screen-tight .score-putts-four-grid > * {
    aspect-ratio: 1 / 1 !important;
    height: auto !important;
    min-height: 0 !important;
    max-height: none !important;
}

.scorecard-screen-tight .score-putts-icon {
    width: 100% !important;
    height: 100% !important;
    aspect-ratio: 1 / 1 !important;
    object-fit: cover !important;
    object-position: center !important;
    display: block !important;
    background: #000000 !important;
}

.scorecard-screen-tight .score-putts-four-grid .score-putts-entry-box {
    width: 100% !important;
    aspect-ratio: 1 / 1 !important;
    height: auto !important;
    min-height: 0 !important;
    background: #1f2028 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
}

.scorecard-screen-tight .score-putts-four-grid .q-field,
.scorecard-screen-tight .score-putts-four-grid .q-field__control {
    width: 100% !important;
    height: 100% !important;
    min-height: 0 !important;
    aspect-ratio: 1 / 1 !important;
    background: #1f2028 !important;
    border: 0 !important;
    box-shadow: none !important;
}

.scorecard-screen-tight .score-putts-four-grid input,
.scorecard-screen-tight .score-putts-four-grid .q-field__native {
    color: #ffffff !important;
    font-size: clamp(42px, 11vw, 68px) !important;
    font-weight: 1000 !important;
    text-align: center !important;
    padding: 0 !important;
    line-height: 1 !important;
}

.scorecard-screen-tight .score-putts-four-grid .q-field__control:before,
.scorecard-screen-tight .score-putts-four-grid .q-field__control:after {
    display: none !important;
}


/* ALWAYS START PLAY GOLF SCREEN AT TOP */
.scorecard-screen-tight {
    scroll-behavior: auto !important;
}


/* SIMPLE WHITE TRIANGLE NAV BUTTONS */
.hole-nav-arrow,
.hole-nav-arrow .q-btn__content {
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 28px !important;
    font-weight: 900 !important;
    color: white !important;
    line-height: 1 !important;
}


/* FORCE SIMPLE TRIANGLE NAV BUTTONS */
.hole-nav-arrow,
.hole-nav-arrow .q-btn__content,
.hole-nav-arrow span {
    font-family: Arial, Helvetica, sans-serif !important;
    font-size: 34px !important;
    font-weight: 900 !important;
    color: #ffffff !important;
    line-height: 1 !important;
}


/* CSS-ONLY PLAY GOLF NAV TRIANGLES - NO EMOJI CHARACTERS */
.scorecard-screen-tight .nav-btn,
.scorecard-screen-tight .bottom-nav-arrow {
    position: relative !important;
    overflow: hidden !important;
    background: #1f2028 !important;
    background-color: #1f2028 !important;
    color: transparent !important;
    font-size: 0 !important;
}

.scorecard-screen-tight .nav-btn .q-btn__content,
.scorecard-screen-tight .bottom-nav-arrow .q-btn__content {
    color: transparent !important;
    font-size: 0 !important;
}

.scorecard-screen-tight .nav-btn::after,
.scorecard-screen-tight .bottom-nav-arrow::after {
    content: "" !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    width: 0 !important;
    height: 0 !important;
}

.scorecard-screen-tight .nav-btn.nav-left::after,
.scorecard-screen-tight .bottom-nav-arrow.nav-left::after {
    border-top: 9px solid transparent !important;
    border-bottom: 9px solid transparent !important;
    border-right: 15px solid #ffffff !important;
}

.scorecard-screen-tight .nav-btn.nav-right::after,
.scorecard-screen-tight .bottom-nav-arrow.nav-right::after {
    border-top: 9px solid transparent !important;
    border-bottom: 9px solid transparent !important;
    border-left: 15px solid #ffffff !important;
}


/* PLAY GOLF LOCATION / QUALITY GRID ROW ALIGNMENT FIX */
.scorecard-screen-tight .tee-grid,
.scorecard-screen-tight .shot-grid,
.scorecard-screen-tight .location-quality-grid,
.scorecard-screen-tight .quality-grid {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    column-gap: 6px !important;
    row-gap: 8px !important;
    width: 100% !important;
    align-items: stretch !important;
}

.scorecard-screen-tight .tee-grid > *,
.scorecard-screen-tight .shot-grid > *,
.scorecard-screen-tight .location-quality-grid > *,
.scorecard-screen-tight .quality-grid > * {
    margin-left: 0 !important;
    margin-right: 0 !important;
    transform: none !important;
    left: auto !important;
    right: auto !important;
    width: 100% !important;
    min-width: 0 !important;
    box-sizing: border-box !important;
}

.scorecard-screen-tight .grid-row,
.scorecard-screen-tight .quality-row,
.scorecard-screen-tight .tee-row {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    column-gap: 6px !important;
    width: 100% !important;
    margin-left: 0 !important;
    transform: none !important;
}

.scorecard-screen-tight .grid-row > *,
.scorecard-screen-tight .quality-row > *,
.scorecard-screen-tight .tee-row > * {
    width: 100% !important;
    min-width: 0 !important;
    margin-left: 0 !important;
    transform: none !important;
}

/* Target the actual shot selection buttons regardless of their existing row wrapper */
.scorecard-screen-tight .shot-button,
.scorecard-screen-tight .tee-shot-button,
.scorecard-screen-tight .quality-button,
.scorecard-screen-tight .location-quality-button {
    width: 100% !important;
    min-width: 0 !important;
    margin-left: 0 !important;
    margin-right: 0 !important;
    transform: none !important;
    box-sizing: border-box !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: clip !important;
}


/* TRUE 5-COLUMN PLAY GOLF TEE GRID */
.tee-grid-fixed {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 6px !important;
    width: 100% !important;
    align-items: stretch !important;
    box-sizing: border-box !important;
}

.tee-grid-fixed .tee-fixed-head {
    color: #ffffff !important;
    text-align: center !important;
    font-size: 14px !important;
    font-weight: 1000 !important;
    line-height: 1.0 !important;
    min-height: 34px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
}

.tee-grid-fixed .q-btn,
.tee-grid-fixed button {
    width: 100% !important;
    min-width: 0 !important;
    max-width: none !important;
    height: 72px !important;
    min-height: 72px !important;
    margin: 0 !important;
    padding: 4px !important;
    border-radius: 8px !important;
    box-sizing: border-box !important;
    white-space: normal !important;
    text-align: center !important;
    overflow: hidden !important;
}

.tee-grid-fixed .q-btn__content {
    width: 100% !important;
    min-width: 0 !important;
    font-size: 11px !important;
    font-weight: 1000 !important;
    line-height: 1.05 !important;
    color: #ffffff !important;
    white-space: normal !important;
    text-align: center !important;
}

.tee-grid-fixed .tee-fixed-selected button,
.tee-grid-fixed .tee-fixed-selected .q-btn {
    border: 4px solid #ffffff !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}


/* FINAL TEE GRID TOP-LEFT CELL ALIGNMENT FIX */
.tee-grid-fixed {
    grid-auto-rows: auto !important;
}

.tee-grid-fixed > * {
    align-self: stretch !important;
    justify-self: stretch !important;
    box-sizing: border-box !important;
}

.tee-grid-fixed > .q-btn,
.tee-grid-fixed > button,
.tee-grid-fixed > div {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
}

.tee-grid-fixed > .q-btn:nth-child(6),
.tee-grid-fixed > button:nth-child(6) {
    transform: translateY(0px) !important;
    margin-top: 0 !important;
    height: 72px !important;
    min-height: 72px !important;
    max-height: 72px !important;
}

/* Make every tee button use the same internal vertical centering */
.tee-grid-fixed .q-btn {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.tee-grid-fixed .q-btn__content {
    height: 100% !important;
    min-height: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}


/* REAL HTML TEE GRID - FIXED ALIGNMENT */
.tee-grid-html {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 6px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

.tee-grid-html-head {
    color: #ffffff !important;
    text-align: center !important;
    font-size: 14px !important;
    font-weight: 1000 !important;
    line-height: 1.0 !important;
    min-height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    width: 100% !important;
}

.tee-grid-html-cell {
    height: 72px !important;
    min-height: 72px !important;
    width: 100% !important;
    min-width: 0 !important;
    border-radius: 8px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    color: #ffffff !important;
    font-size: 11px !important;
    font-weight: 1000 !important;
    line-height: 1.05 !important;
    padding: 4px !important;
    cursor: pointer !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    white-space: normal !important;
    overflow: hidden !important;
}

.tee-grid-html-cell.selected {
    border: 4px solid #ffffff !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}


/* INLINE SCORING ZONE UNDER FAIRWAY HIT */
.scoring-zone-inline-wrap {
    margin-top: 16px !important;
    margin-bottom: 22px !important;
}

.scoring-zone-inline-title {
    text-transform: uppercase !important;
}


/* CLICKABLE DIV TEE GRID - ALIGNED AND MOBILE SAFE */
.tee-grid-clickable {
    display: grid !important;
    grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    gap: 6px !important;
    width: 100% !important;
    box-sizing: border-box !important;
}

.tee-grid-clickable-head {
    color: #ffffff !important;
    text-align: center !important;
    font-size: 14px !important;
    font-weight: 1000 !important;
    line-height: 1.0 !important;
    min-height: 38px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    width: 100% !important;
}

.tee-grid-clickable-cell {
    height: 72px !important;
    min-height: 72px !important;
    width: 100% !important;
    min-width: 0 !important;
    border-radius: 8px !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    color: #ffffff !important;
    font-size: 11px !important;
    font-weight: 1000 !important;
    line-height: 1.05 !important;
    padding: 4px !important;
    cursor: pointer !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    white-space: normal !important;
    overflow: hidden !important;
    touch-action: manipulation !important;
    border: 4px solid transparent !important;
}

.tee-grid-clickable-cell.selected {
    border: 4px solid #ffffff !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}


/* DIRECT ENTRY PENALTIES / HAZARDS / GASHES */
.direct-counter-grid .direct-counter-tile {
    background: #1a1a1a !important;
    overflow: hidden !important;
}

.direct-counter-grid .tile-label,
.direct-counter-grid .tile-controls,
.direct-counter-grid .minus,
.direct-counter-grid .plus,
.direct-counter-grid .tile-value {
    display: none !important;
}

.direct-counter-img {
    width: 100% !important;
    height: 94px !important;
    object-fit: cover !important;
    object-position: center !important;
    display: block !important;
}

.direct-counter-input-wrap {
    background: #1a1a1a !important;
    height: 96px !important;
    min-height: 96px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

.direct-counter-input {
    width: 100% !important;
}

.direct-counter-input .q-field,
.direct-counter-input .q-field__control {
    width: 100% !important;
    height: 96px !important;
    min-height: 96px !important;
    background: #1a1a1a !important;
    border: 0 !important;
    box-shadow: none !important;
}

.direct-counter-input input,
.direct-counter-input .q-field__native {
    color: #ffffff !important;
    font-size: 48px !important;
    font-weight: 1000 !important;
    text-align: center !important;
    padding: 0 !important;
    line-height: 1 !important;
}

.direct-counter-input .q-field__control:before,
.direct-counter-input .q-field__control:after {
    display: none !important;
}

@media (max-width: 430px) {
    .direct-counter-img {
        height: 78px !important;
    }

    .direct-counter-input-wrap,
    .direct-counter-input .q-field,
    .direct-counter-input .q-field__control {
        height: 82px !important;
        min-height: 82px !important;
    }

    .direct-counter-input input,
    .direct-counter-input .q-field__native {
        font-size: 42px !important;
    }
}


/* SELECTED OUTLINE FOR FAIRWAY / GREEN HIT AND SCORING ZONE */
.direct-fir-gir-selected {
    border: 4px solid #ffffff !important;
    box-shadow: 0 0 0 1px #4DDB68 !important;
}

.direct-fir-gir-btn {
    box-sizing: border-box !important;
}


/* FORCE WHITE OUTLINE ON SELECTED YES / NO BUTTONS */
.direct-fir-gir-btn.direct-fir-gir-selected,
.direct-fir-gir-btn.direct-fir-gir-selected.q-btn,
.direct-fir-gir-selected,
.direct-fir-gir-selected button,
.direct-fir-gir-selected .q-btn {
    border: 5px solid #ffffff !important;
    box-shadow: inset 0 0 0 2px #ffffff, 0 0 0 1px #4DDB68 !important;
    filter: none !important;
    box-sizing: border-box !important;
}

.direct-fir-gir-btn.direct-fir-gir-inactive:not(.direct-fir-gir-selected) {
    filter: brightness(.42) !important;
    border: 5px solid transparent !important;
    box-sizing: border-box !important;
}

</style>
'''

ui.add_head_html(STYLE)


def current_entry():
    return round_entries[hole_data[current_hole_index['value']]['hole']]


def image_html(filename, label, css_class, fallback_class, fallback_bg):
    root_path = Path(filename)
    assets_path = Path('assets') / filename
    encoded_name = filename.replace(' ', '%20')

    if assets_path.exists():
        return f'<img class="{css_class}" src="/assets/{encoded_name}" alt="{label}">'

    if root_path.exists():
        return f'<img class="{css_class}" src="/static/{encoded_name}" alt="{label}">'

    return f'<div class="{fallback_class}" style="background:{fallback_bg};">{label}</div>'


def update_hole_display():
    entry = current_entry()
    hole_nav_html.set_content(f'<div class="nav-center">HOLE {entry["hole"]}</div>')

    try:
        bottom_hole_nav_html.set_content(f'<div class="bottom-nav-center">HOLE {entry["hole"]}</div>')
    except Exception:
        pass

    hole_card_html.set_content(f'''
        <div class="hole-card">
            <div class="hole-title">HOLE {entry["hole"]}</div>
            <div class="meta-grid">
                <div class="meta-box">PAR<br><span>{entry["par"]}</span></div>
                <div class="meta-box">YARDS<br><span>{entry["yards"]}</span></div>
                <div class="meta-box">HDCP<br><span>{entry["handicap"]}</span></div>
            </div>
        </div>
    ''')


def update_main_values():
    entry = current_entry()
    try:
        score_input.value = '' if entry.get('score', '') in [None, ''] else str(entry.get('score', ''))
    except Exception:
        pass
    try:
        putts_input.value = '' if entry.get('putts', '') in [None, ''] else str(entry.get('putts', ''))
    except Exception:
        pass


def update_summary():
    entries = list(round_entries.values())
    total_score = sum(e['score'] for e in entries)
    total_par = sum(e['par'] for e in entries)
    total_putts = sum(e['putts'] for e in entries)
    relation = total_score - total_par
    relation_text = 'E' if relation == 0 else f'+{relation}' if relation > 0 else str(relation)

    summary_html.set_content(f'''
        <div class="summary-box">
            DATE: {round_info['date']}<br>
            COURSE: {round_info['course']}<br>
            TEE: {round_info['tee']}<br>
            SCORE: {total_score} ({relation_text})<br>
            PAR: {total_par}<br>
            PUTTS: {total_putts}
        </div>
    ''')


def refresh_all():
    update_hole_display()
    update_main_values()
    rebuild_tee_grid()
    update_inside_buttons()
    rebuild_counter_grid(hazard_container, 'PENALTIES / HAZARDS', HAZARDS, 'hazards', PENALTY_IMAGES, '#0f8c72')
    rebuild_counter_grid(gash_container, 'GASHES', GASHES, 'gashes', GASH_IMAGES, '#ca1d1d')
    update_summary()


def change_hole(delta):
    current_hole_index['value'] = max(0, min(len(hole_data) - 1, current_hole_index['value'] + delta))
    refresh_all()
    save_app_state('scorecard')
    scroll_page_to_top()



def change_score(delta):
    entry = current_entry()
    entry['score'] = max(1, entry['score'] + delta)
    update_main_values()
    update_summary()
    save_app_state('scorecard')



def change_putts(delta):
    entry = current_entry()
    entry['putts'] = max(0, entry['putts'] + delta)
    update_main_values()
    update_summary()
    save_app_state('scorecard')



def set_score_direct(value):
    entry = current_entry()
    try:
        if value is None or str(value).strip() == '':
            entry['score'] = 0
        else:
            entry['score'] = max(0, int(value))
    except Exception:
        entry['score'] = entry.get('score', entry.get('par', 0))
    update_main_values()
    update_summary()


def set_putts_direct(value):
    entry = current_entry()
    try:
        if value is None or str(value).strip() == '':
            entry['putts'] = 0
        else:
            entry['putts'] = max(0, int(value))
    except Exception:
        entry['putts'] = 0
    update_main_values()
    update_summary()


def change_counter(group, key, delta):
    entry = current_entry()
    entry[group][key] = max(0, entry[group][key] + delta)
    if group == 'hazards':
        rebuild_counter_grid(hazard_container, 'PENALTIES / HAZARDS', HAZARDS, 'hazards', PENALTY_IMAGES, '#0f8c72')
    else:
        rebuild_counter_grid(gash_container, 'GASHES', GASHES, 'gashes', GASH_IMAGES, '#ca1d1d')
    save_app_state('scorecard')



def set_tee(location, quality):
    entry = current_entry()
    entry['tee_location'] = location
    entry['tee_quality'] = quality
    rebuild_tee_grid()
    save_app_state('scorecard')





def scoring_zone_shot_count(par):
    par = safe_int(par, 4)
    if par <= 3:
        return 1
    if par == 4:
        return 2
    return 3


def scoring_zone_question_for_entry(entry):
    shots = scoring_zone_shot_count(entry.get('par', 4))
    word = 'SHOT' if shots == 1 else 'SHOTS'
    return f'INSIDE 100 YARDS IN {shots} {word}?'
def set_inside(value):
    current_entry()['inside_100_in_3'] = value
    update_inside_buttons()
    save_app_state('scorecard')



def update_inside_buttons():
    # Scoring zone buttons are now rendered inline beneath Fairway/Green Hit.
    return


def update_club(event):
    current_entry()['tee_club'] = event.value

    save_app_state('scorecard')



def set_fairway_hit(value):
    entry = current_entry()
    entry['fairway_hit'] = value
    rebuild_tee_grid()


def set_green_hit(value):
    entry = current_entry()
    entry['green_hit'] = value
    rebuild_tee_grid()


def render_fir_gir_question(entry):
    par = safe_int(entry.get('par'), 0)

    if par == 3:
        label = 'GREEN HIT?'
        field = 'green_hit'
        setter = set_green_hit
    else:
        label = 'FAIRWAY HIT?'
        field = 'fairway_hit'
        setter = set_fairway_hit

    value = entry.get(field, 'NO') or 'NO'
    yes_class = 'fairway-green-btn fairway-green-btn-yes'
    no_class = 'fairway-green-btn fairway-green-btn-no'

    if value != 'YES':
        yes_class += ' fairway-green-btn-inactive'
    if value != 'NO':
        no_class += ' fairway-green-btn-inactive'

    ui.html('<div class="fairway-green-section">')
    ui.html('<div class="fairway-green-title">' + label + '</div>')
    with ui.element('div').classes('fairway-green-buttons'):
        ui.button('YES', on_click=lambda: setter('YES')).classes(yes_class)
        ui.button('NO', on_click=lambda: setter('NO')).classes(no_class)
    ui.html('</div>')



def set_fir_gir_value(field, value):
    entry = current_entry()
    entry[field] = value
    rebuild_tee_grid()
    save_app_state('scorecard')



def render_fir_gir_question(entry):
    par = safe_int(entry.get('par'), 0)

    if par == 3:
        title = 'GREEN HIT?'
        field = 'green_hit'
    else:
        title = 'FAIRWAY HIT?'
        field = 'fairway_hit'

    current_value = entry.get(field, 'NO') or 'NO'

    yes_class = 'fir-gir-button fir-gir-yes'
    no_class = 'fir-gir-button fir-gir-no'

    if current_value != 'YES':
        yes_class += ' fir-gir-inactive'
    if current_value != 'NO':
        no_class += ' fir-gir-inactive'

    ui.html('<div class="fir-gir-question-wrap">')
    ui.html('<div class="fir-gir-question-title">' + title + '</div>')
    with ui.element('div').classes('fir-gir-buttons'):
        ui.button('YES', on_click=lambda: set_fir_gir_value(field, 'YES')).classes(yes_class)
        ui.button('NO', on_click=lambda: set_fir_gir_value(field, 'NO')).classes(no_class)
    ui.html('</div>')



def set_direct_fir_gir(field, value):
    entry = current_entry()
    entry[field] = value
    rebuild_tee_grid()
    save_app_state('scorecard')



def render_direct_fir_gir(entry):
    par = safe_int(entry.get('par'), 0)

    if par == 3:
        title = 'GREEN HIT?'
        field = 'green_hit'
    else:
        title = 'FAIRWAY HIT?'
        field = 'fairway_hit'

    current_value = entry.get(field, 'NO') or 'NO'

    fairway_yes_selected = current_value == 'YES'
    fairway_no_selected = current_value == 'NO'

    fairway_yes_class = 'direct-fir-gir-btn direct-fir-gir-yes'
    fairway_no_class = 'direct-fir-gir-btn direct-fir-gir-no'

    if fairway_yes_selected:
        fairway_yes_class += ' direct-fir-gir-selected'
    else:
        fairway_yes_class += ' direct-fir-gir-inactive'

    if fairway_no_selected:
        fairway_no_class += ' direct-fir-gir-selected'
    else:
        fairway_no_class += ' direct-fir-gir-inactive'

    fairway_yes_style = (
        'background:#4CAF50 !important; background-color:#4CAF50 !important; color:white !important; '
        + ('border:5px solid #ffffff !important; box-shadow: inset 0 0 0 2px #ffffff !important; filter:none !important;' if fairway_yes_selected else 'border:5px solid transparent !important;')
    )
    fairway_no_style = (
        'background:#F44336 !important; background-color:#F44336 !important; color:white !important; '
        + ('border:5px solid #ffffff !important; box-shadow: inset 0 0 0 2px #ffffff !important; filter:none !important;' if fairway_no_selected else 'border:5px solid transparent !important;')
    )

    with ui.element('div').classes('direct-fir-gir-wrap'):
        ui.html('<div class="direct-fir-gir-title">' + title + '</div>')
        with ui.element('div').classes('direct-fir-gir-buttons'):
            ui.button('YES', on_click=lambda: set_direct_fir_gir(field, 'YES')).classes(fairway_yes_class).style(fairway_yes_style)
            ui.button('NO', on_click=lambda: set_direct_fir_gir(field, 'NO')).classes(fairway_no_class).style(fairway_no_style)

    zone_question = scoring_zone_question_for_entry(entry)
    zone_value = entry.get('inside_100_in_3', 'NO') or 'NO'

    zone_yes_selected = zone_value == 'YES'
    zone_no_selected = zone_value == 'NO'

    zone_yes_class = 'direct-fir-gir-btn direct-fir-gir-yes'
    zone_no_class = 'direct-fir-gir-btn direct-fir-gir-no'

    if zone_yes_selected:
        zone_yes_class += ' direct-fir-gir-selected'
    else:
        zone_yes_class += ' direct-fir-gir-inactive'

    if zone_no_selected:
        zone_no_class += ' direct-fir-gir-selected'
    else:
        zone_no_class += ' direct-fir-gir-inactive'

    zone_yes_style = (
        'background:#4CAF50 !important; background-color:#4CAF50 !important; color:white !important; '
        + ('border:5px solid #ffffff !important; box-shadow: inset 0 0 0 2px #ffffff !important; filter:none !important;' if zone_yes_selected else 'border:5px solid transparent !important;')
    )
    zone_no_style = (
        'background:#F44336 !important; background-color:#F44336 !important; color:white !important; '
        + ('border:5px solid #ffffff !important; box-shadow: inset 0 0 0 2px #ffffff !important; filter:none !important;' if zone_no_selected else 'border:5px solid transparent !important;')
    )

    with ui.element('div').classes('direct-fir-gir-wrap scoring-zone-inline-wrap'):
        ui.html('<div class="direct-fir-gir-title scoring-zone-inline-title">' + zone_question + '</div>')
        with ui.element('div').classes('direct-fir-gir-buttons'):
            ui.button('YES', on_click=lambda: set_inside('YES')).classes(zone_yes_class).style(zone_yes_style)
            ui.button('NO', on_click=lambda: set_inside('NO')).classes(zone_no_class).style(zone_no_style)




def rebuild_tee_grid():
    tee_container.clear()
    entry = current_entry()
    par = entry['par']
    qualities = tee_quality_options(par)

    if entry['tee_quality'] not in qualities:
        entry['tee_quality'] = default_tee_quality(par)

    with tee_container:
        caption = 'PAR 3 TEE SHOT GRID' if par == 3 else 'PAR 4 / PAR 5 TEE SHOT GRID'

        ui.html(f'<div class="tee-caption">{caption}</div>')
        ui.html('<div class="club-label">CLUB</div>')

        ui.select(
            CLUBS,
            value=entry['tee_club'] if entry.get('tee_club') in CLUBS else 'DRIVER',
            on_change=update_club
        ).props('outlined dark color=green').classes('w-full')

        ui.html('<div class="tee-entry-heading">LOCATION / QUALITY GRID</div>')

        locations = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']

        with ui.element('div').classes('tee-grid-clickable'):
            for location in locations:
                label = location.replace(' ', '<br>')
                ui.html(f'<div class="tee-grid-clickable-head">{label}</div>')

            for quality in qualities:
                for location in locations:
                    color = tee_color(par, location, quality)
                    selected = entry['tee_location'] == location and entry['tee_quality'] == quality
                    cls = 'tee-grid-clickable-cell selected' if selected else 'tee-grid-clickable-cell'

                    cell = ui.element('div').classes(cls).style(
                        f'background:{color} !important;'
                    )
                    cell.on('click', lambda e, loc=location, qual=quality: set_tee(loc, qual))
                    with cell:
                        ui.html(f'<div>{quality}</div>')

        ui.html(f'<div class="selected-note">SELECTED: {entry["tee_location"]} / {entry["tee_quality"]}</div>')
        render_direct_fir_gir(entry)




def set_counter_direct(group, item, value):
    entry = current_entry()
    try:
        if value is None or str(value).strip() == '':
            entry[group][item] = 0
        else:
            entry[group][item] = max(0, int(value))
    except Exception:
        entry[group][item] = 0

    update_summary()
    save_app_state('scorecard')
def rebuild_counter_grid(container, title, items, group, images, fallback_bg):
    container.clear()
    entry = current_entry()

    with container:
        ui.html('<div class="white-line"></div>')
        ui.html(f'<div class="section-title">{title}</div>')

        with ui.element('div').classes('tile-grid direct-counter-grid'):
            for item in items:
                with ui.element('div').classes('tile direct-counter-tile'):
                    ui.html(image_html(images.get(item, ''), item, 'tile-img direct-counter-img', 'tile-fallback direct-counter-img', fallback_bg))

                    with ui.element('div').classes('direct-counter-input-wrap'):
                        ui.input(
                            value=str(entry[group].get(item, 0)),
                            on_change=lambda e, k=item, g=group: set_counter_direct(g, k, e.value)
                        ).props(
                            'borderless type=number inputmode=numeric pattern=[0-9]*'
                        ).classes('direct-counter-input')




try:
    ui.add_head_html('<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">')
except Exception:
    pass


def scroll_page_to_top():
    try:
        ui.run_javascript('setTimeout(() => { window.scrollTo(0, 0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0; document.documentElement.scrollLeft = 0; document.body.scrollLeft = 0; }, 100);')
    except Exception:
        pass


def add_screen_home_icon():
    try:
        if current_screen.get('value') != 'home':
            ui.button('⌂', on_click=show_home).props('flat dense').classes('top-home-icon')
    except Exception:
        pass


def clear_root():
    root_container.clear()
    scroll_page_to_top()



def load_saved_rounds():
    data = read_storage_json('rounds.json', ROUNDS_FILE, [])
    return data if isinstance(data, list) else []

def write_saved_rounds(rounds):
    if not isinstance(rounds, list):
        rounds = []
    return write_storage_json('rounds.json', ROUNDS_FILE, rounds)

def relation_text(value):
    try:
        value = float(value)
    except Exception:
        value = 0
    if value == 0:
        return 'E'
    if value > 0:
        return '+' + (str(int(value)) if value == int(value) else str(round(value, 1)))
    return str(int(value)) if value == int(value) else str(round(value, 1))


def pct_value(numerator, denominator):
    if not denominator:
        return 0
    return round((numerator / denominator) * 100)


def pct_text(numerator, denominator):
    return str(pct_value(numerator, denominator)) + '%'


def avg_value(values, default=0):
    clean = []
    for value in values:
        if isinstance(value, (int, float)):
            clean.append(value)
    if not clean:
        return default
    return round(sum(clean) / len(clean), 1)


def sum_nested(rows, group, key):
    total = 0
    for row in rows:
        values = row.get(group, {})
        if isinstance(values, dict):
            total += int(values.get(key, 0) or 0)
    return total


def image_data_uri(filename):
    paths_to_try = [
        Path('assets') / filename,
        Path(filename),
    ]

    for path in paths_to_try:
        if path.exists():
            try:
                encoded = base64.b64encode(path.read_bytes()).decode()
                return 'data:image/png;base64,' + encoded
            except Exception:
                return ''

    return ''


def image_tag_for_stats(filename, label):
    src = image_data_uri(filename)
    if src:
        return '<img class="breakdown-icon" src="' + src + '" alt="' + label + '">'
    return '<div class="breakdown-fallback">' + label + '</div>'



def is_gir_entry(entry):
    try:
        par = int(entry.get('par', 0) or 0)
        score = int(entry.get('score', 0) or 0)
        putts = int(entry.get('putts', 0) or 0)
    except Exception:
        return False

    if par <= 0 or score <= 0:
        return False

    shots_to_green = score - putts
    gir_target = par - 2

    return shots_to_green <= gir_target


def gir_label(entry):
    return 'YES' if is_gir_entry(entry) else 'NO'


def current_round_payload():
    entries = []
    for hole_num in sorted(round_entries.keys()):
        entry = round_entries[hole_num]
        entries.append({
            'hole': int(entry.get('hole', hole_num)),
            'par': int(entry.get('par', 0) or 0),
            'yards': int(entry.get('yards', 0) or 0),
            'handicap': entry.get('handicap', ''),
            'score': int(entry.get('score', 0) or 0),
            'putts': int(entry.get('putts', 0) or 0),
            'tee_club': entry.get('tee_club', ''),
            'tee_location': entry.get('tee_location', ''),
            'tee_quality': entry.get('tee_quality', ''),
            'inside_100_in_3': entry.get('inside_100_in_3', 'NO'),
            'gir': gir_label(entry),
            'shots_to_green': int(entry.get('score', 0) or 0) - int(entry.get('putts', 0) or 0),
            'hazards': entry.get('hazards', {}),
            'gashes': entry.get('gashes', {}),
        })
    total_score = sum(entry['score'] for entry in entries)
    total_par = sum(entry['par'] for entry in entries)
    total_putts = sum(entry['putts'] for entry in entries)
    return {
        'saved_at': datetime.now().isoformat(timespec='seconds'),
        'date': round_info.get('date', date.today().isoformat()),
        'course': round_info.get('course', ''),
        'api_course': round_info.get('api_course', ''),
        'tee': round_info.get('tee', ''),
        'holes': len(entries),
        'total_score': total_score,
        'total_par': total_par,
        'relation_to_par': total_score - total_par,
        'total_putts': total_putts,
        'entries': entries,
    }


def save_current_round():
    payload = current_round_payload()
    rounds = load_saved_rounds()
    rounds.append(payload)
    return write_saved_rounds(rounds)


def flatten_rounds(rounds):
    rows = []
    for round_data in rounds:
        for entry in round_data.get('entries', []):
            row = dict(entry)
            row['round_date'] = round_data.get('date', '')
            row['course'] = round_data.get('course', '')
            row['tee'] = round_data.get('tee', '')
            rows.append(row)
    return rows


def filtered_by_par(rows, par):
    return [row for row in rows if int(row.get('par', 0) or 0) == par]


def scoring_zone_summary(rows):
    yes = sum(1 for row in rows if row.get('inside_100_in_3') == 'YES')
    total = len(rows)
    yes_scores = [int(row.get('score', 0) or 0) for row in rows if row.get('inside_100_in_3') == 'YES']
    no_scores = [int(row.get('score', 0) or 0) for row in rows if row.get('inside_100_in_3') != 'YES']
    return {'yes': yes, 'no': total - yes, 'total': total, 'pct': pct_text(yes, total), 'avg_yes': avg_value(yes_scores), 'avg_no': avg_value(no_scores)}


def render_metric_grid(metrics):
    html = '<div class="analytics-grid">'
    for label, value, sub in metrics:
        html += '<div class="analytics-card"><div class="analytics-label">' + str(label) + '</div><div class="analytics-value">' + str(value) + '</div><div class="analytics-sub">' + str(sub) + '</div></div>'
    html += '</div>'
    ui.html(html)


def render_item_breakdown(title, items, images, rows, group, rounds_count):
    ui.html('<div class="section-title">' + title + '</div>')
    totals = []
    for item in items:
        total = sum_nested(rows, group, item)
        per_round = round(total / rounds_count, 1) if rounds_count else 0
        holes_with_item = sum(1 for row in rows if isinstance(row.get(group, {}), dict) and int(row.get(group, {}).get(item, 0) or 0) > 0)
        totals.append((item, total, per_round, holes_with_item))
    totals.sort(key=lambda item: item[1], reverse=True)
    for item, total, per_round, holes_with_item in totals:
        ui.html('<div class="breakdown-row">' + image_tag_for_stats(images.get(item, ''), item) + '<div><div class="breakdown-name">' + item + '</div><div class="breakdown-detail">' + str(per_round) + ' / round • ' + str(holes_with_item) + ' affected holes</div></div><div class="breakdown-value">' + str(total) + '</div></div>')
    ui.html('<div class="section-title">' + title + ' BY PAR</div>')
    cards = '<div class="par-grid">'
    for par in [3, 4, 5]:
        par_rows = filtered_by_par(rows, par)
        total = sum(sum_nested(par_rows, group, item) for item in items)
        rate = round(total / len(par_rows), 2) if par_rows else 0
        cards += '<div class="par-card"><div class="par-title">PAR ' + str(par) + '</div><div class="par-percent">' + str(total) + '</div><div class="par-detail">' + str(rate) + ' per hole<br>' + str(len(par_rows)) + ' holes</div></div>'
    cards += '</div>'
    ui.html(cards)



def row_is_gir(row):
    if row.get('gir') in ['YES', 'NO']:
        return row.get('gir') == 'YES'
    return is_gir_entry(row)


def gir_summary(rows):
    total = len(rows)
    gir_count = sum(1 for row in rows if row_is_gir(row))
    non_gir_count = total - gir_count

    gir_scores = [int(row.get('score', 0) or 0) for row in rows if row_is_gir(row)]
    non_gir_scores = [int(row.get('score', 0) or 0) for row in rows if not row_is_gir(row)]
    gir_putts = [int(row.get('putts', 0) or 0) for row in rows if row_is_gir(row)]
    non_gir_putts = [int(row.get('putts', 0) or 0) for row in rows if not row_is_gir(row)]

    return {
        'total': total,
        'gir': gir_count,
        'non_gir': non_gir_count,
        'pct': pct_text(gir_count, total),
        'avg_score_gir': avg_value(gir_scores),
        'avg_score_non_gir': avg_value(non_gir_scores),
        'avg_putts_gir': avg_value(gir_putts),
        'avg_putts_non_gir': avg_value(non_gir_putts),
    }


def gir_by_round(rounds):
    rows = []

    for round_data in rounds:
        entries = round_data.get('entries', [])
        total = len(entries)
        gir_count = sum(1 for entry in entries if row_is_gir(entry))
        rows.append({
            'date': round_data.get('date', ''),
            'course': round_data.get('course', ''),
            'score': round_data.get('total_score', ''),
            'relation': round_data.get('relation_to_par', 0),
            'holes': total,
            'gir': gir_count,
            'pct': pct_text(gir_count, total),
        })

    return rows



def scoring_result_label(par, score):
    try:
        par = int(par)
        score = int(score)
    except Exception:
        return None

    if score <= 0 or par <= 0:
        return None

    diff = score - par

    if score == 1:
        return 'HOLE IN ONE'
    if diff == -3:
        return 'ALBATROSS'
    if diff == -2:
        return 'EAGLE'
    if diff == -1:
        return 'BIRDIE'
    if diff == 0:
        return 'PAR'
    if diff == 1:
        return 'BOGEY'
    if diff == 2:
        return 'DOUBLE BOGEY'
    if diff >= 3:
        return 'TRIPLE BOGEY'

    return None


def render_scoring_by_hole_type(rows):
    ui.html('<div class="section-title">SCORING BY HOLE TYPE</div>')

    scoring_rows = [
        'HOLE IN ONE',
        'ALBATROSS',
        'EAGLE',
        'BIRDIE',
        'PAR',
        'BOGEY',
        'DOUBLE BOGEY',
        'TRIPLE BOGEY',
    ]

    par_columns = [3, 4, 5]
    par_totals = {
        par: len([row for row in rows if int(row.get('par', 0) or 0) == par])
        for par in par_columns
    }

    counts = {
        label: {par: 0 for par in par_columns}
        for label in scoring_rows
    }

    for row in rows:
        par = int(row.get('par', 0) or 0)
        score = int(row.get('score', 0) or 0)

        if par not in par_columns:
            continue

        label = scoring_result_label(par, score)

        if label in counts:
            counts[label][par] += 1

    html = '<div class="score-type-grid">'
    html += '<div class="score-type-cell score-type-header">RESULT</div>'
    html += '<div class="score-type-cell score-type-header">PAR 3</div>'
    html += '<div class="score-type-cell score-type-header">PAR 4</div>'
    html += '<div class="score-type-cell score-type-header">PAR 5</div>'

    for label in scoring_rows:
        html += '<div class="score-type-cell"><div class="score-type-row-label">' + label + '</div></div>'

        for par in par_columns:
            count = counts[label][par]
            percent = pct_text(count, par_totals[par])
            html += (
                '<div class="score-type-cell">'
                '<div class="score-type-value">' + str(count) + '</div>'
                '<div class="score-type-sub">' + percent + '</div>'
                '</div>'
            )

    html += '</div>'
    ui.html(html)



def short_round_date_label(date_text):
    try:
        parts = str(date_text).split('-')
        if len(parts) == 3:
            return str(int(parts[1])) + '/' + str(int(parts[2]))
    except Exception:
        pass
    return str(date_text)


def render_gir_by_round_chart(rounds):
    ui.html('<div class="section-title" style="font-size:34px;">GIR BY ROUND</div>')

    round_items = []
    for round_data in sorted(rounds, key=lambda row: row.get('date', '')):
        entries = round_data.get('entries', [])
        holes = len(entries)
        gir_count = sum(1 for entry in entries if row_is_gir(entry))
        pct = pct_value(gir_count, holes)
        score = safe_int(round_data.get('total_score'), 0)
        round_items.append({
            'date': round_data.get('date', ''),
            'label': short_round_date_label(round_data.get('date', '')),
            'pct': pct,
            'score': score,
            'gir': gir_count,
            'holes': holes,
        })

    if not round_items:
        ui.html('<div class="summary-box">No GIR round data yet.</div>')
        return

    html = '<div class="gir-round-chart">'
    html += '<div class="gir-chart-area">'
    html += '<div class="gir-bars">'

    for item in round_items:
        height = max(4, round((item['pct'] / 100) * 220))
        html += (
            '<div class="gir-bar-wrap">'
            '<div class="gir-bar-value">' + str(item['pct']) + '%</div>'
            '<div class="gir-bar" style="height:' + str(height) + 'px;">'
            '<div class="gir-bar-score">' + str(item['score']) + '</div>'
            '</div>'
            '</div>'
        )

    html += '</div>'

    html += '<div class="gir-y-axis">'
    html += '<div>100%</div><div>80%</div><div>60%</div><div>40%</div><div>20%</div><div>0%</div>'
    html += '</div>'

    html += '</div>'

    html += '<div class="gir-labels">'
    for item in round_items:
        html += '<div class="gir-date-label">' + str(item['label']) + '</div>'
    html += '</div>'

    html += '<div class="gir-chart-note">Score is shown inside each bar.</div>'
    html += '</div>'

    ui.html(html)


def render_gir_stats(rows, rounds):
    ui.html('<div class="section-title">GREENS IN REGULATION</div>')

    overall = gir_summary(rows)

    ui.html(
        '<div class="summary-box">'
        + 'OVERALL GIR: ' + str(overall['gir']) + ' / ' + str(overall['total']) + ' holes (' + overall['pct'] + ')<br>'
        + 'AVG SCORE WHEN GIR: ' + str(overall['avg_score_gir']) + '<br>'
        + 'AVG SCORE WHEN MISSED GIR: ' + str(overall['avg_score_non_gir']) + '<br>'
        + 'AVG PUTTS WHEN GIR: ' + str(overall['avg_putts_gir']) + '<br>'
        + 'AVG PUTTS WHEN MISSED GIR: ' + str(overall['avg_putts_non_gir'])
        + '</div>'
    )

    cards = '<div class="par-grid">'
    for par in [3, 4, 5]:
        par_rows = filtered_by_par(rows, par)
        summary = gir_summary(par_rows)
        cards += (
            '<div class="par-card">'
            '<div class="par-title">PAR ' + str(par) + '</div>'
            '<div class="par-percent">' + summary['pct'] + '</div>'
            '<div class="par-detail">'
            + str(summary['gir']) + ' GIR / ' + str(summary['total']) + ' holes<br>'
            + 'GIR AVG: ' + str(summary['avg_score_gir']) + '<br>'
            + 'MISS AVG: ' + str(summary['avg_score_non_gir']) +
            '</div></div>'
        )
    cards += '</div>'
    ui.html(cards)

    render_gir_by_round_chart(rounds)



def distance_bucket_for_yards(yards):
    yards = safe_int(yards, 0)

    if yards <= 150:
        return '0-150'
    if yards <= 200:
        return '151-200'
    if yards <= 250:
        return '201-250'
    if yards <= 300:
        return '251-300'
    if yards <= 350:
        return '301-350'
    if yards <= 400:
        return '351-400'
    if yards <= 450:
        return '401-450'
    if yards <= 500:
        return '451-500'
    return '501+'


def render_score_by_distance(rows):
    ui.html('<div class="section-title">SCORE BY HOLE DISTANCE</div>')

    buckets = [
        ('0-150', '0-150'),
        ('151-200', '151-200'),
        ('201-250', '201-250'),
        ('251-300', '251-300'),
        ('301-350', '301-350'),
        ('351-400', '351-400'),
        ('401-450', '401-450'),
        ('451-500', '451-500'),
        ('501+', '500+'),
    ]

    bucket_scores = {bucket: [] for bucket, _ in buckets}

    for row in rows:
        yards = safe_int(row.get('yards'), 0)
        score = safe_int(row.get('score'), 0)

        if yards <= 0 or score <= 0:
            continue

        bucket = distance_bucket_for_yards(yards)
        if bucket in bucket_scores:
            bucket_scores[bucket].append(score)

    averages = {}
    max_avg = 0

    for bucket, _ in buckets:
        values = bucket_scores[bucket]
        averages[bucket] = avg_value(values) if values else None
        if averages[bucket] is not None:
            max_avg = max(max_avg, averages[bucket])

    if max_avg <= 0:
        max_avg = 1

    chart_height = 178

    html = '<div class="distance-chart">'
    html += '<div class="distance-bars">'

    for bucket, label in buckets:
        avg = averages[bucket]

        if avg is None:
            value_text = 'N/A'
            height = 0
        else:
            value_text = str(avg)
            height = max(4, round((avg / max_avg) * chart_height))

        html += (
            '<div class="distance-bar-wrap">'
            '<div class="distance-bar-value">' + value_text + '</div>'
            '<div class="distance-bar-holder">'
            '<div class="distance-bar" style="height:' + str(height) + 'px;"></div>'
            '</div>'
            '</div>'
        )

    html += '</div>'

    html += '<div class="distance-labels">'
    for bucket, label in buckets:
        html += '<div class="distance-label">' + label + '</div>'
    html += '</div>'

    html += '<div class="distance-count-title">HOLES PLAYED:</div>'
    html += '<div class="distance-counts">'
    for bucket, label in buckets:
        html += '<div class="distance-count">' + str(len(bucket_scores[bucket])) + '</div>'
    html += '</div>'

    html += '</div>'

    ui.html(html)


def render_scoring_zone(rows):
    ui.html('<div class="section-title">SCORING ZONE</div>')
    overall = scoring_zone_summary(rows)
    ui.html('<div class="summary-box">OVERALL: ' + str(overall['yes']) + ' YES / ' + str(overall['total']) + ' holes (' + overall['pct'] + ')<br>AVG SCORE WHEN YES: ' + str(overall['avg_yes']) + '<br>AVG SCORE WHEN NO: ' + str(overall['avg_no']) + '</div>')
    cards = '<div class="par-grid">'
    for par in [3, 4, 5]:
        par_rows = filtered_by_par(rows, par)
        summary = scoring_zone_summary(par_rows)
        cards += '<div class="par-card"><div class="par-title">PAR ' + str(par) + '</div><div class="par-percent">' + summary['pct'] + '</div><div class="par-detail">' + str(summary['yes']) + ' YES / ' + str(summary['total']) + ' holes<br>YES AVG: ' + str(summary['avg_yes']) + '<br>NO AVG: ' + str(summary['avg_no']) + '</div></div>'
    cards += '</div>'
    ui.html(cards)



def normalize_tee_quality_for_stats(par_group, quality):
    quality = str(quality or '').strip().upper()

    par3_options = TEE_QUALITIES_PAR_3
    par45_options = TEE_QUALITIES_PAR_4_5

    if par_group == 'PAR 3':
        if quality in par3_options:
            return quality

        # Older/sample data may include Par 4/5 labels on Par 3 holes.
        # Keep every tee shot in the grid by mapping those to the closest Par 3 bucket.
        if quality in ['CRUSHED', 'AVERAGE', 'PERFECT']:
            return 'PERFECT'
        if quality in ['LITTLE SHORT', 'MIS-HIT SHORT']:
            return quality
        if quality in ['TOO LONG', 'LITTLE LONG']:
            return quality
        return 'PERFECT'

    if quality in par45_options:
        return quality

    # Older/sample data may include Par 3 labels on Par 4/5 holes.
    if quality in ['PERFECT', 'CRUSHED']:
        return 'CRUSHED'
    if quality in ['LITTLE LONG', 'AVERAGE']:
        return 'AVERAGE'
    if quality in ['LITTLE SHORT', 'MIS-HIT SHORT']:
        return 'MIS-HIT SHORT'
    if quality == 'TOO LONG':
        return 'TOO LONG'
    return 'AVERAGE'


def tee_grid_quality_options_for_stats(par_group):
    if par_group == 'PAR 3':
        return TEE_QUALITIES_PAR_3
    return TEE_QUALITIES_PAR_4_5


def tee_grid_color_for_stats(par_group, location, quality):
    sample_par = 3 if par_group == 'PAR 3' else 4
    return tee_color(sample_par, location, quality)


def render_tee_matrix_grid(container, rows, par_group, club_filter):
    container.clear()

    if par_group == 'PAR 3':
        par_rows = [row for row in rows if int(row.get('par', 0) or 0) == 3]
    else:
        par_rows = [row for row in rows if int(row.get('par', 0) or 0) in [4, 5]]

    if club_filter != 'ALL CLUBS':
        par_rows = [row for row in par_rows if row.get('tee_club') == club_filter]

    total = len(par_rows)
    locations = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']
    qualities = tee_grid_quality_options_for_stats(par_group)

    with container:
        ui.html('<div class="tee-caption">' + par_group + ' • ' + club_filter + ' • ' + str(total) + ' tee shots</div>')

        ui.html('<div class="location-title" style="font-size:26px;margin-top:18px;">DISTANCE / QUALITY GRID</div>')

        html = '<div class="stats-tee-layout">'

        # Left side: 5 true columns. First row is the column total row.
        html += '<div class="stats-tee-grid-left">'

        for location in locations:
            loc_count = sum(1 for row in par_rows if row.get('tee_location') == location)
            html += (
                '<div class="stats-tee-cell stats-tee-column-total">'
                '<div class="stats-tee-quality">' + location + '</div>'
                '<div class="stats-tee-percent">' + pct_text(loc_count, total) + '</div>'
                '<div class="stats-tee-count">' + str(loc_count) + ' shots</div>'
                '</div>'
            )

        for quality in qualities:
            for location in locations:
                count = sum(
                    1 for row in par_rows
                    if row.get('tee_location') == location
                    and normalize_tee_quality_for_stats(par_group, row.get('tee_quality')) == quality
                )
                percent = pct_text(count, total)
                color = tee_grid_color_for_stats(par_group, location, quality)

                html += (
                    '<div class="stats-tee-cell" style="background:' + color + ';">'
                    '<div class="stats-tee-quality">' + quality + '</div>'
                    '<div class="stats-tee-percent">' + percent + '</div>'
                    '<div class="stats-tee-count">' + str(count) + '</div>'
                    '</div>'
                )

        html += '</div>'

        # Right side: spacer for the column-total row, then quality totals.
        html += '<div class="stats-tee-row-totals">'
        html += '<div class="stats-tee-cell stats-tee-row-total-spacer-box"></div>'

        for quality in qualities:
            row_count = sum(
                1 for row in par_rows
                if normalize_tee_quality_for_stats(par_group, row.get('tee_quality')) == quality
            )
            html += (
                '<div class="stats-tee-cell stats-tee-row-total-box">'
                '<div class="stats-tee-quality">' + quality + '</div>'
                '<div class="stats-tee-percent">' + pct_text(row_count, total) + '</div>'
                '<div class="stats-tee-count">' + str(row_count) + ' shots</div>'
                '</div>'
            )

        html += '</div>'
        html += '</div>'

        ui.html(html)

        grid_total = 0
        for location in locations:
            for quality in qualities:
                grid_total += sum(
                    1 for row in par_rows
                    if row.get('tee_location') == location
                    and normalize_tee_quality_for_stats(par_group, row.get('tee_quality')) == quality
                )

        ui.html(
            '<div class="selected-note">GRID TOTAL: '
            + str(grid_total)
            + ' / '
            + str(total)
            + ' TEE SHOTS</div>'
        )

def render_tee_matrix(rows):
    ui.html('<div class="section-title">TEE SHOT MATRIX</div>')

    clubs_seen = sorted({row.get('tee_club', '') for row in rows if row.get('tee_club', '')})
    club_options = ['ALL CLUBS'] + clubs_seen

    par3_state = {'club': 'ALL CLUBS'}
    par45_state = {'club': 'ALL CLUBS'}

    ui.html('<div class="section-title" style="font-size:34px;">PAR 3 TEE SHOTS</div>')
    par3_container = ui.element('div')

    def on_par3_club_change(event):
        par3_state['club'] = event.value
        render_tee_matrix_grid(par3_container, rows, 'PAR 3', par3_state['club'])

    ui.html('<div class="start-label">CLUB FILTER</div>')
    ui.select(
        club_options,
        value='ALL CLUBS',
        on_change=on_par3_club_change,
    ).props('outlined dark color=green').classes('w-full')

    render_tee_matrix_grid(par3_container, rows, 'PAR 3', 'ALL CLUBS')

    ui.html('<div class="white-line"></div>')
    ui.html('<div class="section-title" style="font-size:34px;">PAR 4 / PAR 5 TEE SHOTS</div>')
    par45_container = ui.element('div')

    def on_par45_club_change(event):
        par45_state['club'] = event.value
        render_tee_matrix_grid(par45_container, rows, 'PAR 4 / PAR 5', par45_state['club'])

    ui.html('<div class="start-label">CLUB FILTER</div>')
    ui.select(
        club_options,
        value='ALL CLUBS',
        on_change=on_par45_club_change,
    ).props('outlined dark color=green').classes('w-full')

    render_tee_matrix_grid(par45_container, rows, 'PAR 4 / PAR 5', 'ALL CLUBS')


def render_course_performance(rounds):
    ui.html('<div class="section-title">COURSE PERFORMANCE</div>')
    course_map = {}
    for round_data in rounds:
        course = round_data.get('course', 'Unknown Course')
        course_map.setdefault(course, []).append(round_data)
    course_rows = []
    for course, course_rounds in course_map.items():
        scores = [int(r.get('total_score', 0) or 0) for r in course_rounds]
        rels = [int(r.get('relation_to_par', 0) or 0) for r in course_rounds]
        putts = [int(r.get('total_putts', 0) or 0) for r in course_rounds]
        course_rows.append((course, len(course_rounds), avg_value(scores), avg_value(rels), avg_value(putts), min(scores), max(scores)))
    course_rows.sort(key=lambda item: item[3])
    for course, count, avg_score, avg_rel, avg_putts, best, worst in course_rows:
        ui.html('<div class="course-card">' + course + '<br>ROUNDS: ' + str(count) + ' • AVG: ' + str(avg_score) + ' (' + relation_text(avg_rel) + ')<br>BEST: ' + str(best) + ' • WORST: ' + str(worst) + ' • PUTTS AVG: ' + str(avg_putts) + '</div>')


def render_recent_trends(rounds):
    ui.html('<div class="section-title">TRENDING</div>')
    sorted_rounds = sorted(rounds, key=lambda item: item.get('date', ''))
    recent5 = sorted_rounds[-5:]
    previous5 = sorted_rounds[-10:-5]
    if len(recent5) < 2:
        ui.html('<div class="summary-box">Need more saved rounds for trend analysis.</div>')
        return
    recent_avg = avg_value([int(r.get('relation_to_par', 0) or 0) for r in recent5])
    previous_avg = avg_value([int(r.get('relation_to_par', 0) or 0) for r in previous5]) if previous5 else recent_avg
    change = round(recent_avg - previous_avg, 1)
    trend_class = 'trend-good' if change < 0 else 'trend-bad' if change > 0 else 'trend-neutral'
    trend_word = 'IMPROVING' if change < 0 else 'GETTING HIGHER' if change > 0 else 'STEADY'
    recent_putts = avg_value([int(r.get('total_putts', 0) or 0) for r in recent5])
    recent_penalties = []
    for r in recent5:
        penalty_total = 0
        for entry in r.get('entries', []):
            penalty_total += sum(int(v or 0) for v in entry.get('hazards', {}).values())
        recent_penalties.append(penalty_total)
    ui.html('<div class="trend-card">LAST 5 AVG TO PAR: ' + relation_text(recent_avg) + '<br>PRIOR 5 AVG TO PAR: ' + relation_text(previous_avg) + '<br>TREND: <span class="' + trend_class + '">' + trend_word + ' (' + relation_text(change) + ')</span><br>LAST 5 PUTTS AVG: ' + str(recent_putts) + '<br>LAST 5 PENALTY AVG: ' + str(avg_value(recent_penalties)) + '</div>')


def show_finish_screen():
    current_screen['value'] = 'finish'
    clear_root()
    save_app_state('finish')
    payload = current_round_payload()
    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">ROUND SUMMARY</div>')
            ui.html('<div class="summary-box">DATE: ' + str(payload['date']) + '<br>COURSE: ' + str(payload['course']) + '<br>TEE: ' + str(payload['tee']) + '<br>SCORE: ' + str(payload['total_score']) + ' (' + relation_text(payload['relation_to_par']) + ')<br>PAR: ' + str(payload['total_par']) + '<br>PUTTS: ' + str(payload['total_putts']) + '</div>')
            with ui.row().style('gap:18px; margin-top:14px; margin-bottom:30px; flex-wrap:wrap;'):
                ui.button('SAVE ROUND', on_click=save_and_show_stats).props('color=green').classes('start-button')
                ui.button('EDIT ROUND', on_click=show_scorecard).props('color=green').classes('start-button secondary')

            graphic_button('HOME', show_home, 'start-button secondary')


def save_and_show_stats():
    if save_current_round():
        ui.notify('Round saved.')
        save_app_state('stats')
        show_stats()
    else:
        ui.notify('Round could not be saved.')


def show_stats():
    current_screen['value'] = 'stats'
    clear_root()
    save_app_state('stats')
    rounds = load_saved_rounds()
    rows = flatten_rounds(rounds)
    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">STATS</div>')
            if not rounds or not rows:
                ui.html('<div class="summary-box">No saved rounds yet.</div>')
                graphic_button('PLAY GOLF', show_start_round, 'start-button')
                graphic_button('HOME', show_home, 'start-button secondary')
                return
            total_rounds = len(rounds)
            total_holes = len(rows)
            total_score = sum(int(row.get('score', 0) or 0) for row in rows)
            total_par = sum(int(row.get('par', 0) or 0) for row in rows)
            total_putts = sum(int(row.get('putts', 0) or 0) for row in rows)
            total_relation = total_score - total_par
            avg_score_18 = round((total_score / total_holes) * 18, 1) if total_holes else 0
            avg_to_par_18 = round((total_relation / total_holes) * 18, 1) if total_holes else 0
            putts_18 = round((total_putts / total_holes) * 18, 1) if total_holes else 0
            total_penalties = sum(sum_nested(rows, 'hazards', item) for item in HAZARDS)
            total_gashes = sum(sum_nested(rows, 'gashes', item) for item in GASHES)
            scoring_zone_yes = sum(1 for row in rows if row.get('inside_100_in_3') == 'YES')
            render_metric_grid([
                ('ROUNDS', total_rounds, 'saved'),
                ('HOLES', total_holes, 'tracked'),
                ('AVG SCORE / 18', avg_score_18, 'all rounds'),
                ('AVG TO PAR / 18', relation_text(avg_to_par_18), 'scoring rate'),
                ('PUTTS / 18', putts_18, 'putting'),
                ('SCORING ZONE', pct_text(scoring_zone_yes, total_holes), 'inside 100 in 3'),
                ('GIR', pct_text(sum(1 for row in rows if row_is_gir(row)), total_holes), 'greens in regulation'),
                ('PENALTIES', total_penalties, str(round(total_penalties / total_rounds, 1)) + ' / round'),
                ('GASHES', total_gashes, str(round(total_gashes / total_rounds, 1)) + ' / round'),
            ])
            render_gir_stats(rows, rounds)
            render_scoring_by_hole_type(rows)
            render_score_by_distance(rows)
            render_scoring_zone(rows)
            render_item_breakdown('PENALTIES / HAZARDS', HAZARDS, PENALTY_IMAGES, rows, 'hazards', total_rounds)
            render_item_breakdown('GASHES', GASHES, GASH_IMAGES, rows, 'gashes', total_rounds)
            render_tee_matrix(rows)
            render_course_performance(rounds)
            render_recent_trends(rounds)
            ui.html('<div class="section-title">SAVED ROUNDS</div>')
            for round_data in sorted(rounds, key=lambda item: item.get('date', ''), reverse=True):
                ui.html('<div class="round-card">' + str(round_data.get('date', '')) + '<br>' + str(round_data.get('course', '')) + '<br>SCORE: ' + str(round_data.get('total_score', '')) + ' (' + relation_text(int(round_data.get('relation_to_par', 0))) + ') • PUTTS: ' + str(round_data.get('total_putts', '')) + '</div>')
            graphic_button('PLAY GOLF', show_start_round, 'start-button')
            graphic_button('HOME', show_home, 'start-button secondary')



def safe_int(value, default=0):
    try:
        return int(value or 0)
    except Exception:
        return default


def round_score_results(round_data):
    results = {
        'HOLE IN ONE': 0,
        'ALBATROSS': 0,
        'EAGLE': 0,
        'BIRDIE': 0,
        'PAR': 0,
        'BOGEY': 0,
        'DOUBLE BOGEY': 0,
        'TRIPLE BOGEY': 0,
    }

    for entry in round_data.get('entries', []):
        label = scoring_result_label(safe_int(entry.get('par')), safe_int(entry.get('score')))
        if label in results:
            results[label] += 1

    return results


def round_penalty_total(round_data):
    total = 0
    for entry in round_data.get('entries', []):
        values = entry.get('hazards', {})
        if isinstance(values, dict):
            total += sum(safe_int(v) for v in values.values())
    return total


def round_gash_total(round_data):
    total = 0
    for entry in round_data.get('entries', []):
        values = entry.get('gashes', {})
        if isinstance(values, dict):
            total += sum(safe_int(v) for v in values.values())
    return total


def round_three_putt_total(round_data):
    return sum(1 for entry in round_data.get('entries', []) if safe_int(entry.get('putts')) >= 3)


def round_gir_total(round_data):
    return sum(1 for entry in round_data.get('entries', []) if row_is_gir(entry))


def format_round_short(round_data):
    return str(round_data.get('date', '')) + ' • ' + str(round_data.get('course', ''))


def best_round_min(rounds, key_func):
    valid = [r for r in rounds if r.get('entries')]
    if not valid:
        return None
    return min(valid, key=key_func)


def best_round_max(rounds, key_func):
    valid = [r for r in rounds if r.get('entries')]
    if not valid:
        return None
    return max(valid, key=key_func)


def render_record_card(label, value, detail):
    ui.html(
        '<div class="record-card">'
        '<div class="record-label">' + str(label) + '</div>'
        '<div class="record-value">' + str(value) + '</div>'
        '<div class="record-detail">' + str(detail) + '</div>'
        '</div>'
    )


def render_record_wide(title, value, detail):
    ui.html(
        '<div class="record-wide">'
        + str(title) + '<br>'
        + '<strong>' + str(value) + '</strong><br>'
        + str(detail)
        + '</div>'
    )


def consecutive_round_streak(rounds, predicate):
    sorted_rounds = sorted(rounds, key=lambda r: r.get('date', ''))
    best = []
    current = []

    for round_data in sorted_rounds:
        if predicate(round_data):
            current.append(round_data)
            if len(current) > len(best):
                best = current[:]
        else:
            current = []

    return best


def consecutive_hole_streak(rounds, predicate):
    sorted_rounds = sorted(rounds, key=lambda r: r.get('date', ''))
    best = []
    current = []

    for round_data in sorted_rounds:
        entries = sorted(round_data.get('entries', []), key=lambda e: safe_int(e.get('hole')))
        for entry in entries:
            item = {'round': round_data, 'entry': entry}
            if predicate(entry):
                current.append(item)
                if len(current) > len(best):
                    best = current[:]
            else:
                current = []

    return best


def streak_rounds_detail(streak):
    if not streak:
        return 'No streak found yet.'
    first = streak[0]
    last = streak[-1]
    if len(streak) == 1:
        return 'Round: ' + format_round_short(first)
    return 'From ' + format_round_short(first) + '<br>Through ' + format_round_short(last)


def streak_holes_detail(streak):
    if not streak:
        return 'No streak found yet.'
    first = streak[0]
    last = streak[-1]
    first_round = first['round']
    last_round = last['round']
    first_hole = safe_int(first['entry'].get('hole'))
    last_hole = safe_int(last['entry'].get('hole'))
    return (
        'From ' + str(first_round.get('date', '')) + ' hole ' + str(first_hole)
        + '<br>Through ' + str(last_round.get('date', '')) + ' hole ' + str(last_hole)
    )


def render_streak(title, streak, unit, detail):
    ui.html(
        '<div class="record-streak">'
        '<div class="record-streak-title">' + str(title) + '</div>'
        '<div class="record-streak-value">' + str(len(streak)) + ' ' + unit + '</div>'
        '<div class="record-streak-detail">' + str(detail) + '</div>'
        '</div>'
    )


def show_record_book():
    current_screen['value'] = 'record_book'
    clear_root()
    save_app_state('record_book')

    rounds = load_saved_rounds()
    rows = flatten_rounds(rounds)

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">RECORD BOOK</div>')

            if not rounds or not rows:
                ui.html('<div class="summary-box">No saved rounds yet.</div>')
                graphic_button('PLAY GOLF', show_start_round, 'start-button')
                graphic_button('HOME', show_home, 'start-button secondary')
                return

            total_rounds = len(rounds)
            total_holes = len(rows)

            best_score = best_round_min(rounds, lambda r: safe_int(r.get('total_score'), 999))
            best_to_par = best_round_min(rounds, lambda r: safe_int(r.get('relation_to_par'), 999))
            best_putts = best_round_min(rounds, lambda r: safe_int(r.get('total_putts'), 999))
            best_gir = best_round_max(rounds, lambda r: round_gir_total(r))
            best_no_penalty = best_round_min(rounds, lambda r: round_penalty_total(r))
            best_no_gash = best_round_min(rounds, lambda r: round_gash_total(r))

            all_results_by_round = [(r, round_score_results(r)) for r in rounds]
            most_birdies = max(all_results_by_round, key=lambda item: item[1]['BIRDIE'])
            most_pars = max(all_results_by_round, key=lambda item: item[1]['PAR'])
            most_eagles = max(all_results_by_round, key=lambda item: item[1]['EAGLE'])
            most_bogeys = max(all_results_by_round, key=lambda item: item[1]['BOGEY'])
            most_doubles = max(all_results_by_round, key=lambda item: item[1]['DOUBLE BOGEY'])
            most_triples = max(all_results_by_round, key=lambda item: item[1]['TRIPLE BOGEY'])

            ui.html(
                '<div class="record-hero">'
                '<div class="record-hero-title">BEST OF THE BEST</div>'
                '<div class="record-hero-sub">' + str(total_rounds) + ' rounds • ' + str(total_holes) + ' holes tracked</div>'
                '</div>'
            )

            ui.html('<div class="record-badge-row">'
                    '<div class="record-badge"><div class="record-badge-big">' + str(best_score.get('total_score', '')) + '</div><div class="record-badge-label">BEST SCORE</div></div>'
                    '<div class="record-badge"><div class="record-badge-big">' + relation_text(best_to_par.get('relation_to_par', 0)) + '</div><div class="record-badge-label">BEST TO PAR</div></div>'
                    '<div class="record-badge"><div class="record-badge-big">' + str(round_gir_total(best_gir)) + '</div><div class="record-badge-label">BEST GIR ROUND</div></div>'
                    '</div>')

            ui.html('<div class="section-title">ROUND RECORDS</div>')
            ui.html('<div class="record-grid">')
            render_record_card('BEST SCORE', best_score.get('total_score', ''), format_round_short(best_score))
            render_record_card('BEST TO PAR', relation_text(best_to_par.get('relation_to_par', 0)), format_round_short(best_to_par))
            render_record_card('BEST GIR', str(round_gir_total(best_gir)) + ' / ' + str(len(best_gir.get('entries', []))), format_round_short(best_gir))
            render_record_card('LOWEST PUTTS', best_putts.get('total_putts', ''), format_round_short(best_putts))
            render_record_card('FEWEST PENALTIES', round_penalty_total(best_no_penalty), format_round_short(best_no_penalty))
            render_record_card('FEWEST GASHES', round_gash_total(best_no_gash), format_round_short(best_no_gash))
            ui.html('</div>')

            ui.html('<div class="section-title">SCORING RECORDS</div>')
            ui.html('<div class="record-grid">')
            render_record_card('MOST BIRDIES', most_birdies[1]['BIRDIE'], format_round_short(most_birdies[0]))
            render_record_card('MOST PARS', most_pars[1]['PAR'], format_round_short(most_pars[0]))
            render_record_card('MOST EAGLES', most_eagles[1]['EAGLE'], format_round_short(most_eagles[0]))
            render_record_card('MOST BOGEYS', most_bogeys[1]['BOGEY'], format_round_short(most_bogeys[0]))
            render_record_card('MOST DOUBLES', most_doubles[1]['DOUBLE BOGEY'], format_round_short(most_doubles[0]))
            render_record_card('MOST TRIPLES', most_triples[1]['TRIPLE BOGEY'], format_round_short(most_triples[0]))
            ui.html('</div>')

            ui.html('<div class="section-title">SINGLE-HOLE RECORDS</div>')
            birdies_or_better = [row for row in rows if scoring_result_label(safe_int(row.get('par')), safe_int(row.get('score'))) in ['HOLE IN ONE', 'ALBATROSS', 'EAGLE', 'BIRDIE']]
            best_holes = sorted(rows, key=lambda row: safe_int(row.get('score')) - safe_int(row.get('par')))[:8]

            for row in best_holes:
                label = scoring_result_label(safe_int(row.get('par')), safe_int(row.get('score'))) or ''
                render_record_wide(
                    label,
                    'Hole ' + str(row.get('hole', '')) + ' • ' + str(row.get('score', '')) + ' on Par ' + str(row.get('par', '')),
                    str(row.get('round_date', '')) + ' • ' + str(row.get('course', ''))
                )

            ui.html('<div class="section-title">STREAKS</div>')

            birdie_round_streak = consecutive_round_streak(
                rounds,
                lambda r: round_score_results(r).get('BIRDIE', 0) + round_score_results(r).get('EAGLE', 0) + round_score_results(r).get('ALBATROSS', 0) + round_score_results(r).get('HOLE IN ONE', 0) > 0
            )

            no_three_putt_round_streak = consecutive_round_streak(
                rounds,
                lambda r: round_three_putt_total(r) == 0
            )

            gir_round_streak = consecutive_round_streak(
                rounds,
                lambda r: round_gir_total(r) > 0
            )

            no_penalty_round_streak = consecutive_round_streak(
                rounds,
                lambda r: round_penalty_total(r) == 0
            )

            par_or_better_round_streak = consecutive_round_streak(
                rounds,
                lambda r: safe_int(r.get('relation_to_par')) <= 0
            )

            no_three_putt_hole_streak = consecutive_hole_streak(
                rounds,
                lambda e: safe_int(e.get('putts')) < 3
            )

            par_or_better_hole_streak = consecutive_hole_streak(
                rounds,
                lambda e: safe_int(e.get('score')) <= safe_int(e.get('par'))
            )

            no_penalty_hole_streak = consecutive_hole_streak(
                rounds,
                lambda e: sum(safe_int(v) for v in e.get('hazards', {}).values()) == 0 if isinstance(e.get('hazards', {}), dict) else True
            )

            gir_hole_streak = consecutive_hole_streak(
                rounds,
                lambda e: row_is_gir(e)
            )

            render_streak('CONSECUTIVE ROUNDS WITH A BIRDIE OR BETTER', birdie_round_streak, 'rounds', streak_rounds_detail(birdie_round_streak))
            render_streak('CONSECUTIVE ROUNDS WITHOUT A THREE-PUTT', no_three_putt_round_streak, 'rounds', streak_rounds_detail(no_three_putt_round_streak))
            render_streak('CONSECUTIVE ROUNDS WITH AT LEAST ONE GIR', gir_round_streak, 'rounds', streak_rounds_detail(gir_round_streak))
            render_streak('CONSECUTIVE ROUNDS WITHOUT A PENALTY', no_penalty_round_streak, 'rounds', streak_rounds_detail(no_penalty_round_streak))
            render_streak('CONSECUTIVE ROUNDS EVEN PAR OR BETTER', par_or_better_round_streak, 'rounds', streak_rounds_detail(par_or_better_round_streak))

            render_streak('MOST HOLES IN A ROW WITHOUT A THREE-PUTT', no_three_putt_hole_streak, 'holes', streak_holes_detail(no_three_putt_hole_streak))
            render_streak('MOST HOLES IN A ROW PAR OR BETTER', par_or_better_hole_streak, 'holes', streak_holes_detail(par_or_better_hole_streak))
            render_streak('MOST HOLES IN A ROW WITHOUT A PENALTY', no_penalty_hole_streak, 'holes', streak_holes_detail(no_penalty_hole_streak))
            render_streak('MOST HOLES IN A ROW WITH GIR', gir_hole_streak, 'holes', streak_holes_detail(gir_hole_streak))

            ui.html('<div class="section-title">ROUND-BY-ROUND BESTS</div>')
            for round_data in sorted(rounds, key=lambda item: item.get('date', ''), reverse=True):
                results = round_score_results(round_data)
                render_record_wide(
                    round_data.get('date', '') + ' • ' + round_data.get('course', ''),
                    'Score ' + str(round_data.get('total_score', '')) + ' (' + relation_text(round_data.get('relation_to_par', 0)) + ')',
                    'GIR: ' + str(round_gir_total(round_data)) + ' • Birdies: ' + str(results['BIRDIE']) + ' • Pars: ' + str(results['PAR']) + ' • 3-Putts: ' + str(round_three_putt_total(round_data)) + ' • Penalties: ' + str(round_penalty_total(round_data))
                )

            graphic_button('PLAY GOLF', show_start_round, 'start-button')
            graphic_button('STATS', show_stats, 'start-button secondary')
            graphic_button('HOME', show_home, 'start-button secondary')



def war_segments():
    return [
        {'name': 'WAR 1', 'holes': [1, 2, 3], 'label': 'Holes 1-3'},
        {'name': 'WAR 2', 'holes': [4, 5, 6], 'label': 'Holes 4-6'},
        {'name': 'WAR 3', 'holes': [7, 8, 9], 'label': 'Holes 7-9'},
        {'name': 'WAR 4', 'holes': [10, 11, 12], 'label': 'Holes 10-12'},
        {'name': 'WAR 5', 'holes': [13, 14, 15], 'label': 'Holes 13-15'},
        {'name': 'WAR 6', 'holes': [16, 17, 18], 'label': 'Holes 16-18'},
    ]


def round_war_total(round_data, holes):
    total_score = 0
    total_par = 0
    count = 0

    for entry in round_data.get('entries', []):
        hole_num = safe_int(entry.get('hole'), 0)

        if hole_num in holes:
            score = safe_int(entry.get('score'), 0)
            par = safe_int(entry.get('par'), 0)

            if score > 0:
                total_score += score
                total_par += par
                count += 1

    if count == 0:
        return None

    return {
        'score': total_score,
        'par': total_par,
        'relation': total_score - total_par,
        'holes_played': count,
    }


def war_summary(rounds):
    summary = []

    for segment in war_segments():
        values = []

        for round_data in rounds:
            result = round_war_total(round_data, segment['holes'])
            if result and result['holes_played'] == len(segment['holes']):
                values.append(result)

        if values:
            avg_score = round(sum(item['score'] for item in values) / len(values), 1)
            avg_par = round(sum(item['par'] for item in values) / len(values), 1)
            avg_relation = round(sum(item['relation'] for item in values) / len(values), 1)
        else:
            avg_score = 0
            avg_par = 0
            avg_relation = 0

        summary.append({
            'name': segment['name'],
            'holes': segment['holes'],
            'label': segment['label'],
            'avg_score': avg_score,
            'avg_par': avg_par,
            'avg_relation': avg_relation,
            'round_count': len(values),
        })

    return summary



def round_side_total(round_data, start_hole, end_hole):
    score = 0
    par = 0
    count = 0

    for entry in round_data.get('entries', []):
        hole_num = safe_int(entry.get('hole'), 0)
        if start_hole <= hole_num <= end_hole:
            entry_score = safe_int(entry.get('score'), 0)
            entry_par = safe_int(entry.get('par'), 0)
            if entry_score > 0:
                score += entry_score
                par += entry_par
                count += 1

    if count == 0:
        return None

    return {'score': score, 'par': par, 'relation': score - par, 'holes': count}


def average_side(rounds, start_hole, end_hole):
    scores = []
    pars = []
    rels = []

    for round_data in rounds:
        total = round_side_total(round_data, start_hole, end_hole)
        expected_holes = end_hole - start_hole + 1
        if total and total['holes'] == expected_holes:
            scores.append(total['score'])
            pars.append(total['par'])
            rels.append(total['relation'])

    return {
        'score': avg_value(scores),
        'par': avg_value(pars),
        'relation': avg_value(rels),
        'rounds': len(scores),
    }


def render_front_back_split(rounds):
    ui.html('<div class="section-title">FRONT 9 VS BACK 9</div>')

    front = average_side(rounds, 1, 9)
    back = average_side(rounds, 10, 18)

    total_score = round(front['score'] + back['score'], 1)
    total_relation = round(front['relation'] + back['relation'], 1)

    front_share = 50
    if front['score'] + back['score'] > 0:
        front_share = round((front['score'] / (front['score'] + back['score'])) * 100)

    gradient = (
        'conic-gradient(#0B7A35 0% '
        + str(front_share)
        + '%, #4DDB68 '
        + str(front_share)
        + '% 100%)'
    )

    html = '<div class="split-section"><div class="split-wrap">'

    html += (
        '<div class="split-card split-card-front">'
        '<div class="split-card-title split-front-title">Front 9</div>'
        '<div class="split-card-score split-front-color">' + str(front['score']) + '</div>'
        '<div class="split-card-relation split-front-color">' + relation_text(front['relation']) + '</div>'
        '</div>'
    )

    html += (
        '<div>'
        '<div class="split-donut" style="background:' + gradient + ';">'
        '<div class="split-donut-inner">'
        '<div class="split-donut-label">18 Holes</div>'
        '<div class="split-donut-score">' + str(total_score) + '</div>'
        '<div class="split-donut-relation">' + relation_text(total_relation) + '</div>'
        '</div></div>'
        '<div class="split-caption">Circle split reflects average score distribution between front 9 and back 9.</div>'
        '</div>'
    )

    html += (
        '<div class="split-card split-card-back">'
        '<div class="split-card-title split-back-title">Back 9</div>'
        '<div class="split-card-score split-back-color">' + str(back['score']) + '</div>'
        '<div class="split-card-relation split-back-color">' + relation_text(back['relation']) + '</div>'
        '</div>'
    )

    html += '</div></div>'
    ui.html(html)


def show_war_scores():
    current_screen['value'] = 'war_scores'
    clear_root()
    save_app_state('war_scores')

    rounds = load_saved_rounds()

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">SHRINK THE GAME</div>')

            if not rounds:
                ui.html('<div class="summary-box">No saved rounds yet.</div>')
                graphic_button('PLAY GOLF', show_start_round, 'start-button')
                graphic_button('HOME', show_home, 'start-button secondary')
                return

            ui.html(
                '<div class="war-intro">'
                'Every 18-hole round is broken into six smaller 3-hole battles. '
                'The goal is to win the next war, forget the last bad hole, and see exactly where your round usually gets away from you.'
                '</div>'
            )

            summaries = war_summary(rounds)
            valid_summaries = [item for item in summaries if item['round_count'] > 0]

            best_name = ''
            worst_name = ''

            if valid_summaries:
                best = min(valid_summaries, key=lambda item: item['avg_relation'])
                worst = max(valid_summaries, key=lambda item: item['avg_relation'])
                best_name = best['name']
                worst_name = worst['name']

            html = '<div class="war-grid">'
            for item in summaries:
                extra_class = ''
                if item['name'] == best_name:
                    extra_class = ' war-card-best'
                if item['name'] == worst_name:
                    extra_class = ' war-card-worst'

                html += (
                    '<div class="war-card' + extra_class + '">'
                    '<div class="war-title">' + item['name'] + '</div>'
                    '<div class="war-holes">' + item['label'] + '</div>'
                    '<div class="war-score">' + str(item['avg_score']) + '</div>'
                    '<div class="war-detail">'
                    + 'AVG TO PAR: ' + relation_text(item['avg_relation']) + '<br>'
                    + 'ROUNDS: ' + str(item['round_count'])
                    + '</div>'
                    '</div>'
                )
            html += '</div>'
            ui.html(html)

            render_front_back_split(rounds)

            graphic_button('PLAY GOLF', show_start_round, 'start-button')
            graphic_button('STATS', show_stats, 'start-button secondary')
            graphic_button('HOME', show_home, 'start-button secondary')



def load_app_state():
    # app_state is intentionally local-only. It is just a convenience restore file.
    data = local_read_json(APP_STATE_FILE, {})
    return data if isinstance(data, dict) else {}

def save_app_state(screen=None):
    try:
        payload = {
            'screen': screen or current_screen.get('value', 'home'),
            'current_hole_index': current_hole_index.get('value', 0),
            'round_info': round_info,
            'hole_data': hole_data,
            'round_entries': round_entries,
            'start_state': start_state,
        }
        # IMPORTANT: app_state changes constantly during normal use.
        # Keep this local only so every button tap does not call GitHub and slow the app down.
        return local_write_json(APP_STATE_FILE, payload)
    except Exception:
        return False

def restore_app_state():
    global hole_data, round_entries

    state = load_app_state()
    if not state:
        return 'home'

    saved_holes = state.get('hole_data')
    saved_entries = state.get('round_entries')

    if isinstance(saved_holes, list) and saved_holes:
        hole_data = saved_holes

    if isinstance(saved_entries, dict) and saved_entries:
        # JSON saves dict keys as strings. Convert hole keys back to integers when possible.
        restored = {}
        for key, value in saved_entries.items():
            try:
                restored[int(key)] = value
            except Exception:
                restored[key] = value
        round_entries = restored

    saved_round_info = state.get('round_info')
    if isinstance(saved_round_info, dict):
        round_info.update(saved_round_info)

    saved_start_state = state.get('start_state')
    if isinstance(saved_start_state, dict):
        start_state.update(saved_start_state)

    try:
        idx = int(state.get('current_hole_index', 0) or 0)
        if hole_data:
            idx = max(0, min(len(hole_data) - 1, idx))
        current_hole_index['value'] = idx
    except Exception:
        current_hole_index['value'] = 0

    return state.get('screen', 'home')


def reset_app_state_to_home():
    current_screen['value'] = 'home'
    save_app_state('home')




def confirm_delete_saved_round(round_index):
    rounds = load_saved_rounds()

    if not (0 <= round_index < len(rounds)):
        ui.notify('Round not found.')
        show_round_history()
        return

    round_data = rounds[round_index]
    clear_root()

    with root_container:
        with ui.element('div').classes('main-wrap'):
            ui.html('<div class="title">DELETE ROUND?</div>')
            ui.html(
                '<div class="summary-box">'
                + str(round_data.get('date', '')) + '<br>'
                + str(round_data.get('course', '')) + '<br>'
                + 'Score: ' + str(round_data.get('total_score', '')) + ' (' + relation_text(round_data.get('relation_to_par', 0)) + ')'
                + '</div>'
            )
            ui.button('YES, DELETE THIS ROUND', on_click=lambda i=round_index: delete_saved_round(i)).props('color=red').classes('start-button')
            ui.button('CANCEL', on_click=show_round_history).props('color=green').classes('start-button secondary')


def delete_saved_round(round_index):
    rounds = load_saved_rounds()

    if 0 <= round_index < len(rounds):
        deleted = rounds.pop(round_index)
        write_saved_rounds(rounds)
        ui.notify('Deleted round: ' + str(deleted.get('date', '')))
        save_app_state('round_history')
        show_round_history()


def edit_saved_round(round_index):
    global hole_data, round_entries

    rounds = load_saved_rounds()

    if not (0 <= round_index < len(rounds)):
        ui.notify('Round not found.')
        show_round_history()
        return

    selected_round = rounds.pop(round_index)
    write_saved_rounds(rounds)

    entries = selected_round.get('entries', [])
    if not entries:
        ui.notify('This round has no editable hole data.')
        show_round_history()
        return

    hole_data = []
    round_entries = {}

    for entry in entries:
        hole_num = safe_int(entry.get('hole'), len(hole_data) + 1)
        hole_data.append({
            'hole': hole_num,
            'par': safe_int(entry.get('par'), 0),
            'yards': safe_int(entry.get('yards'), 0),
            'handicap': safe_int(entry.get('handicap'), 0),
        })
        round_entries[hole_num] = entry

    round_info.clear()
    round_info.update({
        'date': selected_round.get('date', ''),
        'course': selected_round.get('course', ''),
        'tee': selected_round.get('tee', ''),
        'holes': len(hole_data),
        'editing_existing_round': True,
    })

    current_hole_index['value'] = 0
    save_app_state('scorecard')
    ui.notify('Loaded round for editing. Save it again when finished.')
    show_scorecard()




def safe_scorecard_text(value):
    value = '' if value is None else str(value)
    return (
        value.replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )


def scorecard_cell_value(value):
    if value is None:
        return ''
    try:
        if isinstance(value, (int, float)) and value == 0:
            return ''
    except Exception:
        pass
    return str(value)


def scorecard_hazard_value(entry, *keys):
    hazards = entry.get('hazards', {}) or {}
    for key in keys:
        if key in hazards:
            return scorecard_cell_value(hazards.get(key, ''))
    return ''


def scorecard_gash_value(entry, *keys):
    gashes = entry.get('gashes', {}) or {}
    for key in keys:
        if key in gashes:
            return scorecard_cell_value(gashes.get(key, ''))
    return ''


def scorecard_yes(entry, *keys):
    for key in keys:
        val = str(entry.get(key, '')).upper()
        if val == 'YES':
            return 'Y'
    return ''


def build_digital_scorecard_html(round_data):
    course = str(round_data.get('course', round_data.get('course_name', 'COURSE NAME')) or 'COURSE NAME')
    date = str(round_data.get('date', '') or '')
    tee = str(round_data.get('tee', round_data.get('tee_name', '')) or '')
    total_par = str(round_data.get('total_par', round_data.get('par_total', '')) or '')
    total_score = str(round_data.get('total_score', '') or '')
    total_putts = str(round_data.get('total_putts', '') or '')

    entries = round_data.get('entries', round_data.get('holes', [])) or []
    entries = sorted(entries, key=lambda e: int(e.get('hole', 0) or 0))

    rows = []
    for idx, entry in enumerate(entries):
        hole = int(entry.get('hole', idx + 1) or idx + 1)
        divider_class = ' class="digital-card-front-divider"' if hole == 10 else ''

        fir = scorecard_yes(entry, 'fairway_hit')
        gir = scorecard_yes(entry, 'green_hit', 'gir')
        zone = scorecard_yes(entry, 'inside_100_in_3')

        row = (
            f'<tr{divider_class}>'
            f'<td class="digital-card-hole">{hole}</td>'
            f'<td class="digital-card-meta">PAR<br>{scorecard_cell_value(entry.get("par", ""))}<br>YDS<br>{scorecard_cell_value(entry.get("yards", ""))}<br>HAND.<br>{scorecard_cell_value(entry.get("handicap", ""))}</td>'
            f'<td>{scorecard_cell_value(entry.get("score", ""))}</td>'
            f'<td>{scorecard_cell_value(entry.get("putts", ""))}</td>'
            f'<td>{fir}</td>'
            f'<td>{gir}</td>'
            f'<td>{zone}</td>'
            f'<td>{scorecard_hazard_value(entry, "OB")}</td>'
            f'<td>{scorecard_hazard_value(entry, "GREEN BUNKER", "GREEN")}</td>'
            f'<td>{scorecard_hazard_value(entry, "FAIRWAY BUNKER", "FAIRWAY")}</td>'
            f'<td>{scorecard_hazard_value(entry, "WATER")}</td>'
            f'<td>{scorecard_hazard_value(entry, "DROP")}</td>'
            f'<td class="digital-card-gray">{scorecard_gash_value(entry, "DUFF", "DUFF / CHUNK", "DUFF CHUNK")}</td>'
            f'<td class="digital-card-gray">{scorecard_gash_value(entry, "HERO SHOT")}</td>'
            f'<td class="digital-card-gray">{scorecard_gash_value(entry, "MISREAD", "MAJOR MISREAD")}</td>'
            f'<td class="digital-card-gray">{scorecard_gash_value(entry, "UNDER CLUB")}</td>'
            f'<td class="digital-card-gray">{scorecard_gash_value(entry, "BAD TARGET")}</td>'
            f'<td class="digital-card-gray">{scorecard_cell_value(entry.get("war", ""))}</td>'
            '</tr>'
        )
        rows.append(row)

    total_row = (
        '<tr class="digital-card-totals">'
        '<td></td><td>TOTAL</td>'
        f'<td>{total_score}</td>'
        f'<td>{total_putts}</td>'
        '<td></td><td></td><td></td>'
        '<td></td><td></td><td></td><td></td><td></td>'
        '<td class="digital-card-gray"></td><td class="digital-card-gray"></td><td class="digital-card-gray"></td><td class="digital-card-gray"></td><td class="digital-card-gray"></td><td class="digital-card-gray"></td>'
        '</tr>'
    )

    return (
        '<div class="digital-card-wrap">'
        f'<div class="digital-card-title">{safe_scorecard_text(course).upper()}</div>'
        f'<div class="digital-card-sub">DATE: {safe_scorecard_text(date)}</div>'
        f'<div class="digital-card-sub">TEES - PAR - STROKE: {safe_scorecard_text(tee)}' + (f' • PAR {safe_scorecard_text(total_par)}' if total_par else '') + '</div>'
        '<div class="digital-card-sub">PLAYING PARTNERS</div>'
        '<table class="digital-card-table">'
        '<thead><tr>'
        '<th style="width:50px;"></th>'
        '<th style="width:56px;"></th>'
        '<th>SCORE</th><th>PUTTS</th><th>FIR</th><th>GIR</th><th>ZONE</th>'
        '<th>OB</th><th>GREEN</th><th>FAIRWAY</th><th>WATER</th><th>DROP</th>'
        '<th class="digital-card-gray">DUFF</th><th class="digital-card-gray">HERO</th><th class="digital-card-gray">MISREAD</th><th class="digital-card-gray">UNDER</th><th class="digital-card-gray">BAD</th><th class="digital-card-gray">WAR</th>'
        '</tr></thead>'
        '<tbody>'
        + ''.join(rows)
        + total_row
        + '</tbody></table>'
        '<div class="digital-card-logo">MARIOGOLF</div>'
        '</div>'
    )


def show_round_scorecard(round_index):
    current_screen['value'] = 'round_scorecard'
    clear_root()
    save_app_state('round_scorecard')

    rounds = load_saved_rounds()
    if round_index < 0 or round_index >= len(rounds):
        with root_container:
            with ui.element('div').classes('main-wrap'):
                add_screen_home_icon()
                ui.html('<div class="title">SCORECARD</div>')
                ui.html('<div class="summary-box">Round not found.</div>')
                ui.button('ROUND HISTORY', on_click=show_round_history).props('color=green').classes('start-button')
        return

    round_data = rounds[round_index]

    with root_container:
        with ui.element('div').classes('main-wrap'):
            ui.html('<div class="title">SCORECARD</div>')
            try:
                ui.html(build_digital_scorecard_html(round_data))
            except Exception as e:
                ui.html('<div class="summary-box">Scorecard preview failed to render.<br>Error: ' + safe_scorecard_text(e) + '</div>')

            with ui.row().classes('history-actions'):
                ui.button('ROUND HISTORY', on_click=show_round_history).props('color=green').classes('history-edit')
                ui.button('HOME', on_click=show_home).props('color=green').classes('history-edit')


def show_round_history():
    current_screen['value'] = 'round_history'
    clear_root()
    save_app_state('round_history')

    rounds = load_saved_rounds()

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">ROUND HISTORY</div>')

            if not rounds:
                ui.html('<div class="summary-box">No saved rounds yet.</div>')
                ui.button('PLAY GOLF', on_click=show_start_round).props('color=green').classes('start-button')
                return

            sorted_rounds = sorted(
                list(enumerate(rounds)),
                key=lambda pair: str(pair[1].get('date', '')),
                reverse=True,
            )

            for original_index, round_data in sorted_rounds:
                date = str(round_data.get('date', ''))
                course = str(round_data.get('course', ''))
                tee = str(round_data.get('tee', ''))
                score = str(round_data.get('total_score', ''))
                relation = relation_text(round_data.get('relation_to_par', 0))
                holes = len(round_data.get('entries', []))

                ui.html(
                    '<div class="history-card">'
                    '<div class="history-title">' + date + ' • ' + course + '</div>'
                    '<div class="history-score">' + score + ' <span style="font-size:18px;color:#aaaaaa;">' + relation + '</span></div>'
                    '<div class="history-meta">'
                    + tee + '<br>'
                    + str(holes) + ' holes logged'
                    + '</div>'
                    '</div>'
                )

                with ui.row().classes('history-actions'):
                    ui.button('SCORECARD', on_click=lambda i=original_index: show_round_scorecard(i)).props('color=green').classes('history-edit')
                    ui.button('EDIT', on_click=lambda i=original_index: edit_saved_round(i)).props('color=green').classes('history-edit')
                    ui.button('DELETE', on_click=lambda i=original_index: confirm_delete_saved_round(i)).props('color=red').classes('history-delete')

            ui.button('HOME', on_click=show_home).props('color=green').classes('start-button secondary')




def quick_selected_round_date():
    month_number = MONTH_NAMES.index(quick_load_state['round_month']) + 1
    day_number = int(quick_load_state['round_day'])
    year_number = int(quick_load_state['round_year'])

    try:
        return date(year_number, month_number, day_number)
    except ValueError:
        if month_number == 12:
            next_month = date(year_number + 1, 1, 1)
        else:
            next_month = date(year_number, month_number + 1, 1)
        return next_month - timedelta(days=1)


def quick_on_month_change(event):
    quick_load_state['round_month'] = event.value


def quick_on_day_change(event):
    quick_load_state['round_day'] = event.value


def quick_on_year_change(event):
    quick_load_state['round_year'] = event.value


def quick_on_state_change(event):
    quick_load_state['state_name'] = event.value
    quick_load_state['course_matches'] = []
    quick_load_state['course_labels'] = []
    quick_load_state['selected_course_label'] = None
    quick_load_state['tee_options'] = []
    quick_load_state['tee_labels'] = []
    quick_load_state['course_ready'] = False


def quick_on_search_change(event):
    quick_load_state['search_query'] = event.value or ''


def quick_on_course_change(event):
    quick_load_state['selected_course_label'] = event.value
    quick_load_state['tee_options'] = []
    quick_load_state['tee_labels'] = []
    quick_load_state['course_ready'] = False


def quick_on_tee_change(event):
    quick_load_state['selected_tee_label'] = event.value
    quick_load_state['holes'] = []
    quick_load_state['course_ready'] = False
    quick_load_state['entry_started'] = False


def quick_search_courses():
    query = quick_load_state['search_query'].strip()

    if not get_api_key():
        quick_load_state['status'] = 'Missing Golf API key.'
        show_quick_load()
        return

    if not query:
        quick_load_state['status'] = 'Type a course name first.'
        show_quick_load()
        return

    selected_state = US_STATES[quick_load_state['state_name']]
    matches = api_search_courses(query)

    if not matches:
        quick_load_state['status'] = 'No API course matches found.'
        quick_load_state['course_matches'] = []
        quick_load_state['course_labels'] = []
        show_quick_load()
        return

    state_matches = filter_courses_by_state(matches, selected_state)
    courses_to_show = state_matches if state_matches else matches
    labels = [get_course_display_name(course) for course in courses_to_show]

    quick_load_state['course_matches'] = courses_to_show
    quick_load_state['course_labels'] = labels
    quick_load_state['selected_course_label'] = labels[0] if labels else None
    quick_load_state['selected_course'] = courses_to_show[0] if courses_to_show else None
    quick_load_state['tee_options'] = []
    quick_load_state['tee_labels'] = []
    quick_load_state['selected_tee_label'] = None
    quick_load_state['selected_tee'] = None
    quick_load_state['course_ready'] = False

    quick_load_state['status'] = f'Found {len(labels)} match(es).'
    show_quick_load()


def quick_load_course_details():
    labels = quick_load_state['course_labels']
    selected_label = quick_load_state['selected_course_label']

    if not labels or not selected_label:
        quick_load_state['status'] = 'Search for and select a course first.'
        show_quick_load()
        return

    idx = labels.index(selected_label)
    selected_course = quick_load_state['course_matches'][idx]
    quick_load_state['selected_course'] = selected_course

    course_id = get_course_id(selected_course)

    if not course_id:
        quick_load_state['status'] = 'This API match does not include a course ID.'
        show_quick_load()
        return

    details = api_get_course_details(course_id)

    if not details:
        quick_load_state['status'] = 'Could not load course details from API.'
        show_quick_load()
        return

    tee_options = get_tee_options(details)
    tee_labels = [option['label'] for option in tee_options]

    if not tee_options:
        quick_load_state['status'] = 'Course loaded, but no tee boxes were found.'
        show_quick_load()
        return

    quick_load_state['tee_options'] = tee_options
    quick_load_state['tee_labels'] = tee_labels
    quick_load_state['selected_tee_label'] = tee_labels[0]
    quick_load_state['selected_tee'] = tee_options[0]['tee']
    quick_load_state['holes'] = []
    quick_load_state['course_ready'] = False
    quick_load_state['entry_started'] = False
    quick_load_state['status'] = f'Loaded {len(tee_options)} tee option(s). Select tee, then start Quick Load.'
    show_quick_load()


def build_quick_load_holes():
    quick_load_state['holes'] = []

    if not quick_load_state.get('tee_options') or not quick_load_state.get('selected_tee_label'):
        quick_load_state['status'] = 'No tee selected yet.'
        return

    try:
        tee_idx = quick_load_state['tee_labels'].index(quick_load_state['selected_tee_label'])
    except Exception:
        tee_idx = 0

    try:
        selected_tee = quick_load_state['tee_options'][tee_idx]['tee']
    except Exception:
        quick_load_state['status'] = 'Selected tee could not be read.'
        return

    tee_holes = get_holes_from_tee(selected_tee)

    # Defensive fallback for API tee shapes that store holes in another field.
    if not tee_holes:
        for key in ['holes', 'hole_data', 'course_holes', 'tee_holes']:
            possible = selected_tee.get(key) if isinstance(selected_tee, dict) else None
            if isinstance(possible, list) and possible:
                tee_holes = possible
                break

    if not tee_holes:
        quick_load_state['status'] = 'Selected tee loaded, but no hole-by-hole yardage was found.'
        return

    holes = []
    for idx, hole in enumerate(tee_holes[:18], start=1):
        if not isinstance(hole, dict):
            continue

        hole_num = hole.get('hole') or hole.get('number') or hole.get('hole_number') or idx
        par = hole.get('par') or hole.get('tee_par') or 4
        yards = hole.get('yards') or hole.get('yardage') or hole.get('length') or 0
        handicap = hole.get('handicap') or hole.get('hcp') or hole.get('hdcp') or idx

        try:
            par = int(par or 4)
        except Exception:
            par = 4

        try:
            yards = int(yards or 0)
        except Exception:
            yards = 0

        try:
            hole_num = int(hole_num or idx)
        except Exception:
            hole_num = idx

        holes.append({
            'hole': hole_num,
            'par': par,
            'yards': yards,
            'handicap': handicap,
            'score': par,
            'putts': 2,
            'tee_club': 'DRIVER',
            'tee_location': 'CENTER',
            'tee_quality': default_tee_quality(par),
            'inside_100_in_3': 'NO',
            'fairway_hit': 'NO',
            'green_hit': 'NO',
            'hazards': {item: 0 for item in HAZARDS},
            'gashes': {item: 0 for item in GASHES},
        })

    quick_load_state['holes'] = holes
    quick_load_state['course_ready'] = bool(holes)

    if holes:
        quick_load_state['status'] = f'Loaded {len(holes)} holes for Quick Load.'
    else:
        quick_load_state['status'] = 'Tee loaded, but holes could not be built.'




def quick_header_icon_html(filename, fallback):
    path = asset_path(filename)
    if not path:
        return fallback
    try:
        mime = mimetypes.guess_type(path)[0] or 'image/png'
        encoded = base64.b64encode(Path(path).read_bytes()).decode('ascii')
        return '<img class="quick-header-icon" src="data:' + mime + ';base64,' + encoded + '" alt="' + fallback + '">'
    except Exception:
        return fallback





def quick_mark_touched(index, field):
    try:
        quick_load_state['holes'][index].setdefault('_touched', {})[field] = True
    except Exception:
        pass


def quick_mark_nested_touched(index, bucket, key):
    try:
        quick_load_state['holes'][index].setdefault('_touched', {}).setdefault(bucket, {})[key] = True
    except Exception:
        pass


def quick_number_display(hole, field, default_blank_value):
    # If the user has typed in this field, always show the stored value.
    touched = hole.get('_touched', {}).get(field, False)
    value = hole.get(field, default_blank_value)
    if not touched:
        return ''
    try:
        return str(int(value))
    except Exception:
        return ''


def quick_nested_number_display(hole, bucket, key):
    touched = hole.get('_touched', {}).get(bucket, {}).get(key, False)
    value = hole.get(bucket, {}).get(key, 0)
    if not touched:
        return ''
    try:
        return str(int(value))
    except Exception:
        return ''


def quick_blank_number_value(value, blank_if):
    try:
        if value is None:
            return ''
        if int(value) == int(blank_if):
            return ''
        return str(int(value))
    except Exception:
        return ''


def quick_update_hole_int(index, field, value, default_value=0):
    quick_mark_touched(index, field)
    try:
        if value is None or str(value).strip() == '':
            # Store default internally, but keep touched true so the user can clear it visually.
            value = default_value
        value = int(value)
    except Exception:
        value = default_value

    try:
        quick_load_state['holes'][index][field] = value
    except Exception:
        return


def quick_update_nested_int(index, bucket, key, value):
    quick_mark_nested_touched(index, bucket, key)
    try:
        if value is None or str(value).strip() == '':
            value = 0
        value = int(value)
    except Exception:
        value = 0

    try:
        quick_load_state['holes'][index][bucket][key] = value
    except Exception:
        return


def quick_update_nested_count(index, bucket, key, value):
    try:
        value = int(value)
    except Exception:
        value = 0

    try:
        quick_load_state['holes'][index][bucket][key] = value
    except Exception:
        return


def quick_update_hole(index, field, value):
    try:
        hole = quick_load_state['holes'][index]
    except Exception:
        return

    if field in ['score', 'putts']:
        try:
            value = int(value)
        except Exception:
            value = 0

    hole[field] = value



def start_quick_entry():
    if not quick_load_state.get('tee_options') or not quick_load_state.get('selected_tee_label'):
        quick_load_state['status'] = 'Select a tee first.'
        show_quick_load()
        return

    build_quick_load_holes()

    if not quick_load_state.get('holes'):
        quick_load_state['status'] = 'No holes loaded for this tee. Try another tee.'
        show_quick_load()
        return

    quick_load_state['entry_started'] = True
    quick_load_state['course_ready'] = True
    quick_load_state['status'] = f'Ready to enter {len(quick_load_state["holes"])} holes.'
    show_quick_load()



def sanitize_quick_load_numbers():
    for hole in quick_load_state.get('holes', []):
        par = int(hole.get('par', 0) or 0)
        try:
            hole['score'] = int(hole.get('score', par) or par)
        except Exception:
            hole['score'] = par

        try:
            hole['putts'] = int(hole.get('putts', 0) or 0)
        except Exception:
            hole['putts'] = 0

        for bucket in ['hazards', 'gashes']:
            hole.setdefault(bucket, {})
            for key, value in list(hole[bucket].items()):
                try:
                    hole[bucket][key] = int(value or 0)
                except Exception:
                    hole[bucket][key] = 0

        hole.pop('_touched', None)


def save_quick_load_round():
    sanitize_quick_load_numbers()
    if not quick_load_state['holes']:
        ui.notify('Load a course first.')
        show_quick_load()
        return

    selected_course = quick_load_state.get('selected_course') or {}
    course_name = selected_course.get('course_name') or selected_course.get('name') or selected_course.get('club_name') or quick_load_state.get('selected_course_label') or 'Quick Load Round'

    entries = []
    for hole in quick_load_state['holes']:
        entry = dict(hole)
        entry['gir'] = gir_label(entry)
        entry['shots_to_green'] = int(entry.get('score', 0) or 0) - int(entry.get('putts', 0) or 0)
        entries.append(entry)

    total_score = sum(int(entry.get('score', 0) or 0) for entry in entries)
    total_par = sum(int(entry.get('par', 0) or 0) for entry in entries)
    total_putts = sum(int(entry.get('putts', 0) or 0) for entry in entries)

    payload = {
        'saved_at': datetime.now().isoformat(timespec='seconds'),
        'date': quick_selected_round_date().isoformat(),
        'course': course_name,
        'api_course': quick_load_state.get('selected_course_label') or course_name,
        'tee': quick_load_state.get('selected_tee_label') or '',
        'holes': len(entries),
        'total_score': total_score,
        'total_par': total_par,
        'relation_to_par': total_score - total_par,
        'total_putts': total_putts,
        'entries': entries,
    }

    rounds = load_saved_rounds()
    rounds.append(payload)

    if write_saved_rounds(rounds):
        ui.notify('Quick Load round saved.')
        show_round_history()
    else:
        ui.notify('Round could not be saved.')



def quick_shot_grid_color(location, quality, par):
    if par == 3:
        if quality == 'PERFECT':
            if location == 'CENTER':
                return '#67ff40'
            if location in ['LEFT', 'RIGHT']:
                return '#7fc35b'
            return '#ef3024'
        if quality in ['LITTLE LONG', 'LITTLE SHORT']:
            if location == 'CENTER':
                return '#7fc35b'
            if location in ['LEFT', 'RIGHT']:
                return '#347d42'
            return '#ef3024'
        if quality == 'TOO LONG':
            return '#a81f16'
        return '#a81f16'

    if quality == 'CRUSHED':
        if location == 'CENTER':
            return '#67ff40'
        if location in ['LEFT', 'RIGHT']:
            return '#7fc35b'
        return '#ef3024'
    if quality == 'AVERAGE':
        if location == 'CENTER':
            return '#b6e85a'
        if location in ['LEFT', 'RIGHT']:
            return '#347d42'
        return '#ef3024'
    if quality == 'TOO LONG':
        return '#a81f16'
    return '#a81f16'


def quick_select_shot(index, location, quality):
    quick_update_hole(index, 'tee_location', location)
    quick_update_hole(index, 'tee_quality', quality)
    # Redraw the Quick Load page so the white selected box moves to the tapped square.
    show_quick_load()


def render_quick_combined_shot_grid(index, hole):
    par = int(hole.get('par', 4) or 4)
    current_location = hole.get('tee_location', 'CENTER')
    current_quality = hole.get('tee_quality', default_tee_quality(par))

    locations = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']
    qualities = TEE_QUALITIES_PAR_3 if par == 3 else TEE_QUALITIES_PAR_4_5

    with ui.element('div').classes('quick-shot-combo'):
        with ui.element('div').classes('quick-shot-grid par3' if par == 3 else 'quick-shot-grid par45'):
            for quality in qualities:
                for location in locations:
                    color = quick_shot_grid_color(location, quality, par)
                    is_selected = location == current_location and quality == current_quality
                    classes = 'quick-shot-cell selected' if is_selected else 'quick-shot-cell'
                    # Use flat/unelevated and CSS variable to stop NiceGUI's blue primary color.
                    ui.button(
                        '',
                        on_click=lambda i=index, loc=location, qual=quality: quick_select_shot(i, loc, qual)
                    ).props('flat unelevated dense no-caps').classes(classes).style('--shot-color:' + color + '; background:' + color + ' !important;')



def render_quick_shot_grid_html(hole):
    par = int(hole.get('par', 4) or 4)
    current_location = hole.get('tee_location', 'CENTER')
    current_quality = hole.get('tee_quality', default_tee_quality(par))

    locations = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']
    qualities = TEE_QUALITIES_PAR_3 if par == 3 else TEE_QUALITIES_PAR_4_5

    cells = []
    for quality in qualities:
        for location in locations:
            color = quick_shot_grid_color(location, quality, par)
            selected = location == current_location and quality == current_quality
            cls = 'quick-shot-html-cell selected' if selected else 'quick-shot-html-cell'
            bg = '#ffffff' if selected else color
            cells.append(f'<div class="{cls}" style="background:{bg};"></div>')

    return '<div class="quick-shot-grid">' + ''.join(cells) + '</div>'


def quick_cell(classes=''):
    return ui.element('div').classes('quick-grid-cell ' + classes)



def render_quick_shot_grid_clickable(index, hole):
    par = int(hole.get('par', 4) or 4)
    current_location = hole.get('tee_location', 'CENTER')
    current_quality = hole.get('tee_quality', default_tee_quality(par))

    locations = ['LOST LEFT', 'LEFT', 'CENTER', 'RIGHT', 'LOST RIGHT']
    qualities = TEE_QUALITIES_PAR_3 if par == 3 else TEE_QUALITIES_PAR_4_5

    with ui.element('div').classes('quick-shot-grid'):
        for quality in qualities:
            for location in locations:
                color = quick_shot_grid_color(location, quality, par)
                selected = location == current_location and quality == current_quality
                classes = 'quick-shot-click-cell selected' if selected else 'quick-shot-click-cell'
                bg = '#ffffff' if selected else color
                ui.element('div').classes(classes).style('background:' + bg + ';').on(
                    'click',
                    lambda e=None, i=index, loc=location, qual=quality: quick_select_shot(i, loc, qual)
                )


def render_quick_hole_row(index, hole):
    par = int(hole.get('par', 0) or 0)
    score_options = list(range(1, 11))
    putt_options = list(range(0, 7))
    count_options = list(range(0, 5))

    hazards = hole.setdefault('hazards', {item: 0 for item in HAZARDS})
    gashes = hole.setdefault('gashes', {item: 0 for item in GASHES})

    with quick_cell('quick-sticky-cell'):
        ui.html(
            '<div>'
            '<div class="quick-hole-num">' + str(hole.get('hole')) + '</div>'
            '<div class="quick-hole-meta">P ' + str(par) + '<br>' + str(hole.get('yards', 0)) + ' yds<br>H ' + str(hole.get('handicap', '')) + '</div>'
            '</div>'
        )

    with quick_cell():
        ui.input(value=quick_number_display(hole, 'score', par), on_change=lambda e, i=index, p=par: quick_update_hole_int(i, 'score', e.value, p)).props('outlined dark dense color=green type=number inputmode=numeric pattern=[0-9]*').classes('w-full quick-num-input')
    with quick_cell():
        ui.input(value=quick_number_display(hole, 'putts', 0), on_change=lambda e, i=index: quick_update_hole_int(i, 'putts', e.value, 0)).props('outlined dark dense color=green type=number inputmode=numeric pattern=[0-9]*').classes('w-full quick-num-input')
    with quick_cell():
        ui.select(CLUBS, value=hole.get('tee_club', 'DRIVER'), on_change=lambda e, i=index: quick_update_hole(i, 'tee_club', e.value)).props('outlined dark dense color=green').classes('w-full')

    with quick_cell():
        render_quick_shot_grid_clickable(index, hole)

    if par == 3:
        with quick_cell():
            ui.select(['NO', 'YES'], value=hole.get('green_hit', 'NO'), on_change=lambda e, i=index: quick_update_hole(i, 'green_hit', e.value)).props('outlined dark dense color=green').classes('w-full')
    else:
        with quick_cell():
            ui.select(['NO', 'YES'], value=hole.get('fairway_hit', 'NO'), on_change=lambda e, i=index: quick_update_hole(i, 'fairway_hit', e.value)).props('outlined dark dense color=green').classes('w-full')

    with quick_cell():
        ui.select(['NO', 'YES'], value=hole.get('inside_100_in_3', 'NO'), on_change=lambda e, i=index: quick_update_hole(i, 'inside_100_in_3', e.value)).props('outlined dark dense color=green').classes('w-full')

    for hazard in HAZARDS:
        with quick_cell():
            ui.input(value=quick_nested_number_display(hole, 'hazards', hazard), on_change=lambda e, i=index, h=hazard: quick_update_nested_int(i, 'hazards', h, e.value)).props('outlined dark dense color=green type=number inputmode=numeric pattern=[0-9]*').classes('w-full quick-num-input')

    for gash in GASHES:
        with quick_cell():
            ui.input(value=quick_nested_number_display(hole, 'gashes', gash), on_change=lambda e, i=index, g=gash: quick_update_nested_int(i, 'gashes', g, e.value)).props('outlined dark dense color=green type=number inputmode=numeric pattern=[0-9]*').classes('w-full quick-num-input')


def render_quick_load_table():
    with ui.element('div').classes('quick-wide-wrap'):
        with ui.element('div').classes('quick-wide-grid'):
            ui.html('<div class="quick-grid-cell quick-grid-head quick-sticky-cell quick-sticky-head">HOLE<br><span style="font-size:9px;">PAR/YDS/HCP</span></div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(MAIN_IMAGES['SCORE'], 'SCORE') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(MAIN_IMAGES['PUTTS'], 'PUTTS') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">CLUB</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">SHOT GRID</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">F/G</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">ZONE</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(PENALTY_IMAGES['OB'], 'OB') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(PENALTY_IMAGES['GREEN BUNKER'], 'GB') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(PENALTY_IMAGES['FAIRWAY BUNKER'], 'FB') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(PENALTY_IMAGES['WATER'], 'WTR') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(PENALTY_IMAGES['DROP'], 'DRP') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(GASH_IMAGES['DUFF'], 'DUF') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(GASH_IMAGES['HERO SHOT'], 'HERO') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(GASH_IMAGES['MISREAD'], 'MIS') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(GASH_IMAGES['UNDER CLUB'], 'UND') + '</div>')
            ui.html('<div class="quick-grid-cell quick-grid-head">' + quick_header_icon_html(GASH_IMAGES['BAD TARGET'], 'BAD') + '</div>')

            for idx, hole in enumerate(quick_load_state['holes']):
                render_quick_hole_row(idx, hole)


def show_quick_load():
    current_screen['value'] = 'quick_load'
    clear_root()
    save_app_state('quick_load')

    quick_load_state.setdefault('entry_started', False)

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">QUICK LOAD</div>')

            status = quick_load_state.get('status', '')
            if status:
                ui.html(f'<div class="status-box">{status}</div>')

            ui.html('<div class="start-label">ROUND DATE</div>')
            with ui.row().classes('w-full no-wrap'):
                ui.select(MONTH_NAMES, value=quick_load_state['round_month'], on_change=quick_on_month_change).props('outlined dark color=green').classes('w-full')
                ui.select(DAY_OPTIONS, value=quick_load_state['round_day'], on_change=quick_on_day_change).props('outlined dark color=green').classes('start-day-select')
                ui.select(YEAR_OPTIONS, value=quick_load_state['round_year'], on_change=quick_on_year_change).props('outlined dark color=green').classes('start-year-select')

            # STEP 1: COURSE SEARCH / COURSE MATCHES / TEE SELECTION
            if not quick_load_state.get('entry_started'):
                ui.html('<div class="section-title" style="font-size:34px;">COURSE SEARCH</div>')

                ui.html('<div class="start-label">STATE</div>')
                ui.select(list(US_STATES.keys()), value=quick_load_state['state_name'], on_change=quick_on_state_change).props('outlined dark color=green').classes('w-full')

                ui.html('<div class="start-label">COURSE SEARCH</div>')
                ui.input(value=quick_load_state['search_query'], placeholder='Type course name...', on_change=quick_on_search_change).props('outlined dark color=green').classes('w-full')

                with ui.element('div').classes('quick-load-actions'):
                    ui.button('SEARCH COURSES', on_click=quick_search_courses).props('color=green').classes('start-button')
                    ui.html('<div></div>')
                    ui.button('HOME', on_click=show_home).props('color=green').classes('start-button')

                if quick_load_state['course_labels']:
                    ui.html('<div class="white-line"></div>')
                    ui.html('<div class="section-title" style="font-size:34px;">COURSE MATCHES</div>')

                    ui.html('<div class="start-label">COURSE MATCH</div>')
                    ui.select(quick_load_state['course_labels'], value=quick_load_state['selected_course_label'], on_change=quick_on_course_change).props('outlined dark color=green').classes('w-full')

                    if not quick_load_state.get('tee_labels'):
                        with ui.element('div').classes('quick-load-actions'):
                            ui.button('LOAD TEES', on_click=quick_load_course_details).props('color=green').classes('start-button')
                            ui.html('<div></div>')
                            ui.button('HOME', on_click=show_home).props('color=green').classes('start-button')
                    else:
                        ui.html('<div class="section-title" style="font-size:34px;">TEE</div>')
                        ui.select(quick_load_state['tee_labels'], value=quick_load_state['selected_tee_label'], on_change=quick_on_tee_change).props('outlined dark color=green').classes('w-full')

                        ui.html(
                            '<div class="quick-lock-box">'
                            'Course and tee will lock when you start Quick Load.<br>'
                            'Use this screen to select the correct tee first.'
                            '</div>'
                        )

                        with ui.element('div').classes('quick-load-actions'):
                            ui.button('START QUICK LOAD', on_click=start_quick_entry).props('color=green').classes('start-button')
                            ui.html('<div></div>')
                            ui.button('HOME', on_click=show_home).props('color=green').classes('start-button')

                return

            # STEP 2: 18-HOLE ENTRY WITH COURSE/TEE LOCKED
            selected_course = quick_load_state.get('selected_course') or {}
            course_name = selected_course.get('course_name') or selected_course.get('name') or selected_course.get('club_name') or quick_load_state.get('selected_course_label') or 'Selected Course'
            ui.html(
                '<div class="quick-lock-box">'
                f'COURSE: {course_name}<br>'
                f'TEE: {quick_load_state.get("selected_tee_label") or ""}'
                '</div>'
            )

            ui.html('<div class="white-line"></div>')
            ui.html('<div class="section-title" style="font-size:34px;">18 HOLE QUICK ENTRY</div>')

            if not quick_load_state.get('holes'):
                ui.html('<div class="summary-box">No holes loaded for this tee. Go back and select a tee again.</div>')
            else:
                render_quick_load_table()

            ui.button('SAVE QUICK ROUND', on_click=save_quick_load_round).props('color=green').classes('quick-save-button')

            with ui.element('div').classes('quick-load-actions'):
                ui.button('NEW COURSE SEARCH', on_click=lambda: (quick_load_state.update({'entry_started': False, 'course_ready': False, 'holes': [], 'tee_options': [], 'tee_labels': [], 'selected_tee_label': None}), show_quick_load())).props('color=green').classes('start-button')
                ui.html('<div></div>')
                ui.button('HOME', on_click=show_home).props('color=green').classes('start-button')


def show_settings():
    current_screen['value'] = 'settings'
    clear_root()
    save_app_state('settings')

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">SETTINGS</div>')

            ui.button('CREATE CUSTOM COURSE', on_click=show_create_course).props('color=green').classes('home-button')
            ui.button('QUICK LOAD', on_click=show_quick_load).props('color=green').classes('home-button secondary')
            ui.button('HOME', on_click=show_home).props('color=green').classes('home-button secondary')


def show_home():
    current_screen['value'] = 'home'
    clear_root()
    save_app_state('home')
    scroll_page_to_top()

    with root_container:
        with ui.element('div').classes('home-wrap'):
            graphic_src = home_graphic_src()

            if graphic_src:
                ui.html(
                    '<div class="home-graphic-wrap">'
                    '<img src="' + graphic_src + '" alt="Golf">'
                    '</div>'
                )
            else:
                video_src = video_src_for_home()

                if video_src:
                    ui.html(
                        '<div class="home-video-wrap">'
                        '<video autoplay muted loop playsinline>'
                        '<source src="' + video_src + '" type="video/mp4">'
                        '</video>'
                        '</div>'
                    )
                else:
                    ui.html('<div class="home-fallback-logo">GOLF</div>')

            with ui.element('div').classes('home-menu'):
                ui.button('PLAY GOLF', on_click=show_start_round).props('color=green').classes('home-button')
                ui.button('STATS', on_click=show_stats).props('color=green').classes('home-button secondary')
                ui.button('SHRINK THE GAME', on_click=show_war_scores).props('color=green').classes('home-button secondary')
                ui.button('RECORD BOOK', on_click=show_record_book).props('color=green').classes('home-button secondary')
                ui.button('ROUND HISTORY', on_click=show_round_history).props('color=green').classes('home-button secondary')
                ui.button('SETTINGS', on_click=show_settings).props('color=green').classes('home-button secondary')



def load_custom_courses():
    data = read_storage_json('custom_courses.json', CUSTOM_COURSES_FILE, [])
    return data if isinstance(data, list) else []

def write_custom_courses(courses):
    try:
        CUSTOM_COURSES_FILE.write_text(json.dumps(courses, indent=2))
        return True
    except Exception:
        return False


def custom_course_label(course):
    name = course.get('course_name', 'Custom Course')
    city = course.get('city', '')
    state = course.get('state', '')
    country = course.get('country', '')
    tee = course.get('tee_color', 'Tee')

    location_parts = [part for part in [city, state, country] if part]
    location = ', '.join(location_parts)

    if location:
        return name + ' — ' + location + ' • ' + tee
    return name + ' • ' + tee


def on_custom_course_change(event):
    start_state['custom_course_label'] = event.value


def start_custom_course_round():
    global hole_data

    courses = load_custom_courses()

    if not courses:
        start_state['status'] = 'No custom courses saved yet.'
        show_start_round()
        return

    labels = [custom_course_label(course) for course in courses]
    selected_label = start_state.get('custom_course_label') or labels[0]

    if selected_label == 'USE API COURSE SEARCH':
        start_state['status'] = 'Select a saved custom course first.'
        show_start_round()
        return

    if selected_label not in labels:
        selected_label = labels[0]

    selected_course = courses[labels.index(selected_label)]
    holes = selected_course.get('holes', [])

    clean_holes = []
    for index, hole in enumerate(holes, start=1):
        clean_holes.append({
            'hole': index,
            'par': safe_int(hole.get('par'), 4),
            'yards': safe_int(hole.get('yards'), 0),
            'handicap': safe_int(hole.get('handicap'), index),
        })

    if not clean_holes:
        start_state['status'] = 'That custom course does not have hole data.'
        show_start_round()
        return

    hole_data = clean_holes

    round_info['date'] = selected_round_date().isoformat()
    round_info['course'] = selected_course.get('course_name', 'Custom Course')
    round_info['api_course'] = custom_course_label(selected_course)
    round_info['tee'] = (
        str(selected_course.get('tee_color', 'Tee'))
        + ' • Slope '
        + str(selected_course.get('slope', ''))
    )
    round_info['holes'] = len(clean_holes)

    init_round_entries()
    save_app_state('scorecard')
    show_scorecard()


def create_course_update(field, event):
    create_course_state[field] = event.value


def create_course_update_hole(index, field, event):
    value = event.value
    if field in ['yards', 'par', 'handicap']:
        value = safe_int(value, 0)
    create_course_state['holes'][index][field] = value


def save_custom_course():
    name = str(create_course_state.get('course_name', '')).strip()

    if not name:
        create_course_state['status'] = 'Course name is required.'
        show_create_course()
        return

    clean_holes = []
    for i, hole in enumerate(create_course_state['holes'], start=1):
        par = safe_int(hole.get('par'), 0)
        yards = safe_int(hole.get('yards'), 0)
        handicap = safe_int(hole.get('handicap'), i)

        if par <= 0:
            par = 4
        if handicap <= 0:
            handicap = i

        clean_holes.append({
            'hole': i,
            'yards': yards,
            'par': par,
            'handicap': handicap,
        })

    course = {
        'course_name': name,
        'city': str(create_course_state.get('city', '')).strip(),
        'state': str(create_course_state.get('state', '')).strip(),
        'country': str(create_course_state.get('country', '')).strip(),
        'tee_color': str(create_course_state.get('tee_color', '')).strip(),
        'slope': str(create_course_state.get('slope', '')).strip(),
        'rating': str(create_course_state.get('rating', '')).strip(),
        'holes': clean_holes,
    }

    courses = load_custom_courses()

    # Replace matching course/tee if it already exists.
    courses = [
        item for item in courses
        if not (
            item.get('course_name') == course['course_name']
            and item.get('tee_color') == course['tee_color']
        )
    ]
    courses.append(course)

    if write_custom_courses(courses):
        create_course_state['status'] = 'Course saved.'
        start_state['custom_course_label'] = custom_course_label(course)
        show_start_round()
    else:
        create_course_state['status'] = 'Course could not be saved.'
        show_create_course()


def show_create_course():
    current_screen['value'] = 'create_course'
    clear_root()
    save_app_state('create_course')

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">CREATE COURSE</div>')

            status = create_course_state.get('status', '')
            if status:
                ui.html('<div class="status-box">' + status + '</div>')

            ui.html('<div class="custom-section-note">Use this for overseas courses, courses not found in the API, private courses, or custom tee setups. Enter one tee box at a time. You can create the same course multiple times with different tee colors.</div>')

            ui.html('<div class="start-label">COURSE NAME</div>')
            ui.input(
                value=create_course_state['course_name'],
                placeholder='Course name',
                on_change=lambda e: create_course_update('course_name', e),
            ).props('outlined dark color=green').classes('w-full')

            ui.html('<div class="start-label">CITY / STATE / COUNTRY</div>')
            ui.input(
                value=create_course_state['city'],
                placeholder='City',
                on_change=lambda e: create_course_update('city', e),
            ).props('outlined dark color=green').classes('w-full')

            with ui.row().classes('w-full no-wrap'):
                ui.input(
                    value=create_course_state['state'],
                    placeholder='State / Province',
                    on_change=lambda e: create_course_update('state', e),
                ).props('outlined dark color=green').classes('w-full')

                ui.input(
                    value=create_course_state['country'],
                    placeholder='Country',
                    on_change=lambda e: create_course_update('country', e),
                ).props('outlined dark color=green').classes('w-full')

            ui.html('<div class="start-label">TEE INFO</div>')
            with ui.row().classes('w-full no-wrap'):
                ui.input(
                    value=create_course_state['tee_color'],
                    placeholder='Tee color',
                    on_change=lambda e: create_course_update('tee_color', e),
                ).props('outlined dark color=green').classes('w-full')

                ui.input(
                    value=create_course_state['slope'],
                    placeholder='Slope',
                    on_change=lambda e: create_course_update('slope', e),
                ).props('outlined dark color=green').classes('w-28')

                ui.input(
                    value=create_course_state['rating'],
                    placeholder='Rating',
                    on_change=lambda e: create_course_update('rating', e),
                ).props('outlined dark color=green').classes('w-28')

            ui.html('<div class="section-title" style="font-size:34px;">HOLE DATA</div>')

            def render_hole_entry_row(idx, hole):
                with ui.element('div').classes('custom-grid'):
                    ui.html('<div class="custom-hole-number">' + str(idx + 1) + '</div>')
                    ui.input(
                        value=str(hole.get('yards', '')),
                        placeholder='Yds',
                        on_change=lambda e, i=idx: create_course_update_hole(i, 'yards', e),
                    ).props('outlined dark color=green type=number inputmode=numeric dense')
                    ui.select(
                        [0, 3, 4, 5],
                        value=safe_int(hole.get('par'), 0),
                        on_change=lambda e, i=idx: create_course_update_hole(i, 'par', e),
                    ).props('outlined dark color=green dense')
                    ui.select(
                        list(range(0, 19)),
                        value=safe_int(hole.get('handicap'), 0),
                        on_change=lambda e, i=idx: create_course_update_hole(i, 'handicap', e),
                    ).props('outlined dark color=green dense')

            with ui.element('div').classes('custom-hole-columns'):
                with ui.element('div').classes('custom-hole-column'):
                    ui.html('<div class="custom-hole-column-title">HOLES 1-9</div>')
                    ui.html(
                        '<div class="custom-grid">'
                        '<div class="custom-grid-header">HOLE</div>'
                        '<div class="custom-grid-header">YDS</div>'
                        '<div class="custom-grid-header">PAR</div>'
                        '<div class="custom-grid-header">HDCP</div>'
                        '</div>'
                    )
                    for idx in range(0, 9):
                        render_hole_entry_row(idx, create_course_state['holes'][idx])

                with ui.element('div').classes('custom-hole-column'):
                    ui.html('<div class="custom-hole-column-title">HOLES 10-18</div>')
                    ui.html(
                        '<div class="custom-grid">'
                        '<div class="custom-grid-header">HOLE</div>'
                        '<div class="custom-grid-header">YDS</div>'
                        '<div class="custom-grid-header">PAR</div>'
                        '<div class="custom-grid-header">HDCP</div>'
                        '</div>'
                    )
                    for idx in range(9, 18):
                        render_hole_entry_row(idx, create_course_state['holes'][idx])

            with ui.row().classes('button-row-spaced'):
                ui.button('SAVE COURSE', on_click=save_custom_course).props('color=green').classes('start-button')
                ui.button('BACK TO PLAY GOLF', on_click=show_start_round).props('color=green').classes('start-button secondary')
                ui.button('HOME', on_click=show_home).props('color=green').classes('start-button secondary')


def on_month_change(event):
    start_state['round_month'] = event.value


def on_day_change(event):
    start_state['round_day'] = int(event.value)


def on_year_change(event):
    start_state['round_year'] = int(event.value)


def selected_round_date():
    month_number = MONTH_NAMES.index(start_state['round_month']) + 1
    day_number = int(start_state['round_day'])
    year_number = int(start_state['round_year'])

    try:
        return date(year_number, month_number, day_number)
    except ValueError:
        # Handles invalid dates like February 31 by snapping to the last valid day.
        if month_number == 12:
            next_month = date(year_number + 1, 1, 1)
        else:
            next_month = date(year_number, month_number + 1, 1)
        return next_month - timedelta(days=1)


def on_state_change(event):
    start_state['state_name'] = event.value


def on_search_change(event):
    start_state['search_query'] = event.value


def on_course_change(event):
    start_state['selected_course_label'] = event.value


def on_tee_change(event):
    start_state['selected_tee_label'] = event.value


def on_holes_change(event):
    start_state['selected_holes'] = int(event.value)


def search_courses():
    query = start_state['search_query'].strip()

    if not get_api_key():
        start_state['status'] = 'Missing Golf API key. Add GOLF_API_KEY or GOLF_COURSE_API_KEY in Railway variables.'
        show_start_round()
        return

    if not query:
        start_state['status'] = 'Type a course name first.'
        show_start_round()
        return

    selected_state = US_STATES[start_state['state_name']]
    matches = api_search_courses(query)

    if not matches:
        start_state['status'] = 'No API course matches found. Try a more specific course name.'
        start_state['course_matches'] = []
        start_state['course_labels'] = []
        show_start_round()
        return

    state_matches = filter_courses_by_state(matches, selected_state)
    courses_to_show = state_matches if state_matches else matches
    labels = [get_course_display_name(course) for course in courses_to_show]

    start_state['course_matches'] = courses_to_show
    start_state['course_labels'] = labels
    start_state['selected_course_label'] = labels[0] if labels else None
    start_state['selected_course'] = courses_to_show[0] if courses_to_show else None
    start_state['tee_options'] = []
    start_state['tee_labels'] = []
    start_state['selected_tee_label'] = None
    start_state['selected_tee'] = None

    if state_matches:
        start_state['status'] = f'Found {len(labels)} match(es) in {start_state["state_name"]}.'
    else:
        start_state['status'] = f'No exact state match found. Showing all API matches for "{query}".'

    show_start_round()


def load_course_details():
    labels = start_state['course_labels']
    selected_label = start_state['selected_course_label']

    if not labels or not selected_label:
        start_state['status'] = 'Search for and select a course first.'
        show_start_round()
        return

    idx = labels.index(selected_label)
    selected_course = start_state['course_matches'][idx]
    start_state['selected_course'] = selected_course

    course_id = get_course_id(selected_course)

    if not course_id:
        start_state['status'] = 'This API match does not include a course ID.'
        show_start_round()
        return

    details = api_get_course_details(course_id)

    if not details:
        start_state['status'] = 'Could not load course details from API.'
        show_start_round()
        return

    tee_options = get_tee_options(details)
    tee_labels = [option['label'] for option in tee_options]

    if not tee_options:
        start_state['status'] = 'Course loaded, but no tee boxes were found.'
        show_start_round()
        return

    start_state['tee_options'] = tee_options
    start_state['tee_labels'] = tee_labels
    start_state['selected_tee_label'] = tee_labels[0]
    start_state['selected_tee'] = tee_options[0]['tee']

    first_holes = get_holes_from_tee(tee_options[0]['tee'])

    if len(first_holes) >= 18:
        start_state['hole_options'] = [9, 18]
        start_state['selected_holes'] = 18
    else:
        start_state['hole_options'] = [max(1, len(first_holes))]
        start_state['selected_holes'] = max(1, len(first_holes))

    start_state['status'] = f'Loaded {len(tee_options)} tee option(s).'
    show_start_round()


def start_real_round():
    global hole_data

    if not start_state['tee_options'] or not start_state['selected_tee_label']:
        start_state['status'] = 'Load a course and select a tee first.'
        show_start_round()
        return

    tee_idx = start_state['tee_labels'].index(start_state['selected_tee_label'])
    selected_tee = start_state['tee_options'][tee_idx]['tee']
    tee_holes = get_holes_from_tee(selected_tee)

    if not tee_holes:
        start_state['status'] = 'Selected tee does not include hole-by-hole data.'
        show_start_round()
        return

    holes_count = int(start_state['selected_holes'])
    hole_data = tee_holes[:holes_count]

    selected_course = start_state['selected_course'] or {}
    course_name = selected_course.get('course_name') or selected_course.get('name') or selected_course.get('club_name') or start_state['selected_course_label']

    round_info['date'] = selected_round_date().isoformat()
    round_info['course'] = course_name
    round_info['api_course'] = start_state['selected_course_label']
    round_info['tee'] = start_state['selected_tee_label']
    round_info['holes'] = holes_count

    init_round_entries()
    save_app_state('scorecard')
    show_scorecard()


def show_start_round():
    current_screen['value'] = 'start_round'
    clear_root()
    save_app_state('start_round')

    with root_container:
        with ui.element('div').classes('main-wrap'):
            add_screen_home_icon()
            ui.html('<div class="title">START ROUND</div>')

            status = start_state.get('status', '')
            if status:
                ui.html(f'<div class="status-box">{status}</div>')

            ui.html('<div class="start-label">ROUND DATE</div>')

            with ui.row().classes('w-full no-wrap'):
                ui.select(
                    MONTH_NAMES,
                    value=start_state['round_month'],
                    on_change=on_month_change,
                ).props('outlined dark color=green').classes('w-full')

                ui.select(
                    DAY_OPTIONS,
                    value=start_state['round_day'],
                    on_change=on_day_change,
                ).props('outlined dark color=green').classes('start-day-select')

                ui.select(
                    YEAR_OPTIONS,
                    value=start_state['round_year'],
                    on_change=on_year_change,
                ).props('outlined dark color=green').classes('start-year-select')

            custom_courses = load_custom_courses()
            custom_labels = [custom_course_label(course) for course in custom_courses]

            ui.html('<div class="start-label">CUSTOM COURSE</div>')

            if custom_labels:
                custom_options = ['USE API COURSE SEARCH'] + custom_labels
                selected_custom = start_state.get('custom_course_label') or 'USE API COURSE SEARCH'
                if selected_custom not in custom_options:
                    selected_custom = 'USE API COURSE SEARCH'

                ui.select(
                    custom_options,
                    value=selected_custom,
                    on_change=on_custom_course_change,
                ).props('outlined dark color=green').classes('w-full')

                if selected_custom != 'USE API COURSE SEARCH':
                    ui.button('START CUSTOM COURSE', on_click=start_custom_course_round).props('color=green').classes('start-button')
            else:
                ui.select(
                    ['NO CUSTOM COURSES SAVED'],
                    value='NO CUSTOM COURSES SAVED',
                ).props('outlined dark color=green disable').classes('w-full')

            ui.html('<div class="white-line"></div>')
            ui.html('<div class="section-title" style="font-size:34px;">API COURSE SEARCH</div>')

            ui.html('<div class="start-label">STATE</div>')
            ui.select(
                list(US_STATES.keys()),
                value=start_state['state_name'],
                on_change=on_state_change,
            ).props('outlined dark color=green').classes('w-full')

            ui.html('<div class="start-label">COURSE SEARCH</div>')
            ui.input(
                value=start_state['search_query'],
                placeholder='Type course name...',
                on_change=on_search_change,
            ).props('outlined dark color=green').classes('w-full')

            ui.button('SEARCH COURSES', on_click=search_courses).props('color=green').classes('start-button')

            if start_state['course_labels']:
                ui.html('<div class="white-line"></div>')
                ui.html('<div class="section-title" style="font-size:34px;">API COURSE MATCHES</div>')

                ui.html('<div class="start-label">COURSE MATCH</div>')
                ui.select(
                    start_state['course_labels'],
                    value=start_state['selected_course_label'],
                    on_change=on_course_change,
                ).props('outlined dark color=green').classes('w-full')

                ui.button('LOAD TEES', on_click=load_course_details).props('color=green').classes('start-button')

            if start_state['tee_labels']:
                ui.html('<div class="start-label">TEE</div>')
                ui.select(
                    start_state['tee_labels'],
                    value=start_state['selected_tee_label'],
                    on_change=on_tee_change,
                ).props('outlined dark color=green').classes('w-full')

                ui.html('<div class="start-label">HOLES</div>')
                ui.select(
                    start_state['hole_options'],
                    value=start_state['selected_holes'],
                    on_change=on_holes_change,
                ).props('outlined dark color=green').classes('w-full')

                ui.button('START ROUND', on_click=start_real_round).props('color=green').classes('start-button')

            ui.button('HOME', on_click=show_home).props('color=green').classes('start-button secondary start-home-small')

def show_scorecard():
    current_screen['value'] = 'scorecard'
    clear_root()
    save_app_state('scorecard')

    with root_container:
        with ui.element('div').classes('main-wrap scorecard-screen-tight'):
            ui.run_javascript('setTimeout(() => { window.scrollTo(0,0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0; document.documentElement.scrollLeft = 0; document.body.scrollLeft = 0; }, 50); setTimeout(() => { window.scrollTo(0,0); document.documentElement.scrollTop = 0; document.body.scrollTop = 0; document.documentElement.scrollLeft = 0; document.body.scrollLeft = 0; }, 250);')

            with ui.element('div').classes('hole-nav'):
                ui.button('', on_click=lambda: change_hole(-1)).props('flat color=dark').classes('nav-btn nav-left')
                global hole_nav_html
                hole_nav_html = ui.html('')
                ui.button('', on_click=lambda: change_hole(1)).props('flat color=dark').classes('nav-btn nav-right')

            global hole_card_html
            hole_card_html = ui.html('')

            with ui.element('div').classes('main-grid score-putts-four-grid'):

                ui.html(image_html(
                    MAIN_IMAGES['SCORE'],
                    'SCORE',
                    'main-img score-putts-icon',
                    'fake-image score-bg score-putts-icon',
                    '#b89c72'
                ))

                with ui.element('div').classes('score-putts-entry-box'):
                    global score_input
                    score_input = ui.input(
                        value='',
                        on_change=lambda e: set_score_direct(e.value)
                    ).props(
                        'borderless type=number inputmode=numeric pattern=[0-9]*'
                    ).classes('w-full')

                ui.html(image_html(
                    MAIN_IMAGES['PUTTS'],
                    'PUTTS',
                    'main-img score-putts-icon',
                    'fake-image putts-bg score-putts-icon',
                    '#4f9d00'
                ))

                with ui.element('div').classes('score-putts-entry-box'):
                    global putts_input
                    putts_input = ui.input(
                        value='',
                        on_change=lambda e: set_putts_direct(e.value)
                    ).props(
                        'borderless type=number inputmode=numeric pattern=[0-9]*'
                    ).classes('w-full')

            ui.html('<div class="white-line"></div>')
            ui.html('<div class="section-title">TEE SHOT</div>')
            global tee_container
            tee_container = ui.element('div')

            global hazard_container
            hazard_container = ui.element('div')

            global gash_container
            gash_container = ui.element('div')

            with ui.element('div').classes('bottom-hole-nav'):
                with ui.element('div').classes('hole-nav-row-bottom'):
                    ui.button('', on_click=lambda: change_hole(-1)).props('flat color=dark').classes('bottom-nav-arrow nav-left')
                    global bottom_hole_nav_html
                    bottom_hole_nav_html = ui.html('')
                    ui.button('', on_click=lambda: change_hole(1)).props('flat color=dark').classes('bottom-nav-arrow nav-right')

            ui.html('<div class="white-line"></div>')
            ui.html('<div class="section-title">ROUND SUMMARY</div>')
            global summary_html
            summary_html = ui.html('')

            with ui.element('div').classes('bottom-row'):
                ui.button('SETUP', on_click=show_start_round).props('color=green').classes('bottom-button')
                ui.button('FINISH', on_click=show_finish_screen).props('color=green').classes('bottom-button')

            refresh_all()


init_round_entries()
last_screen = restore_app_state()
root_container = ui.element('div')

if last_screen == 'scorecard' and round_entries:
    show_scorecard()
elif last_screen == 'start_round':
    show_start_round()
elif last_screen == 'stats':
    show_stats()
elif last_screen == 'record_book':
    show_record_book()
elif last_screen == 'round_history':
    show_round_history()
elif last_screen == 'settings':
    show_settings()
elif last_screen == 'quick_load':
    show_quick_load()
elif last_screen == 'war_scores':
    show_war_scores()
elif last_screen == 'create_course':
    show_create_course()
elif last_screen == 'finish' and round_entries:
    show_finish_screen()
else:
    show_home()

ui.run(host='0.0.0.0', port=8080)

all_rounds = []
