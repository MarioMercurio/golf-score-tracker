import base64
import json
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import quote, unquote

import requests
import streamlit as st

st.set_page_config(page_title="GOLF", page_icon="⛳", layout="wide", initial_sidebar_state="collapsed")

VIDEO_FILE = "GolfIntro.mp4"
API_BASE_URL = "https://api.golfcourseapi.com"
COURSE_INDEX_FILE = "course_index.json"

MAIN_IMAGES = {
    "SCORE": "Main - Score.png",
    "PUTTS": "Main - Putts.png",
}

PENALTY_IMAGES = {
    "OB": "Penalty - OB.png",
    "GREEN BUNKER": "Penalty - Green Bunker .png",
    "FAIRWAY BUNKER": "Penalty - Fairway Bunker.png",
    "WATER": "Penalty - Water.png",
    "DROP": "Penalty - Drop.png",
}

GASH_IMAGES = {
    "DUFF": "Gash - Duff Chunk.png",
    "HERO SHOT": "Gash - Hero Shot.png",
    "MISREAD": "Gash - Misread.png",
    "UNDER CLUB": "Gash - Under Club.png",
    "BAD TARGET AREA": "Gash - Bad Target.png",
}

US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

COURSE_SWEEP_TERMS = [
    "", "golf", "club", "country club", "course", "links", "national",
    "municipal", "park", "valley", "lake", "lakes", "hills", "ridge",
    "river", "creek", "woods", "meadows", "pointe", "point", "legacy",
    "green", "greens", "oak", "oaks", "pine", "pines", "blue", "red",
    "a", "e", "i", "o", "u", "r", "s", "t", "n", "l", "m", "c"
]

CLUBS = ["DR", "3W", "5W", "HYB", "4I", "5I", "6I", "7I", "8I", "9I", "PW", "GW", "SW", "LW"]

TEE_LOCATIONS = ["LOST LEFT", "LEFT", "CENTER", "RIGHT", "LOST RIGHT"]

TEE_QUALITIES_PAR_3 = [
    "TOO LONG",
    "LITTLE LONG",
    "PERFECT",
    "LITTLE SHORT",
    "MIS-HIT SHORT"
]

TEE_QUALITIES_PAR_4_5 = [
    "TOO LONG",
    "CRUSHED",
    "AVERAGE",
    "MIS-HIT SHORT"
]

HAZARDS = ["OB", "GREEN BUNKER", "FAIRWAY BUNKER", "WATER", "DROP"]
GASHES = ["DUFF", "HERO SHOT", "MISREAD", "UNDER CLUB", "BAD TARGET AREA"]


def get_api_key():
    return st.secrets.get("GOLF_API_KEY", "") or st.secrets.get("GOLF_COURSE_API_KEY", "")


def local_image_base64(filename):
    path = Path(filename)

    if not path.exists():
        path = Path("assets") / filename

    if not path.exists():
        return ""

    return base64.b64encode(path.read_bytes()).decode()


@st.cache_data(show_spinner=False)
def api_search_courses(search_query):
    api_key = get_api_key()

    if not api_key:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/search",
            headers={"Authorization": f"Key {api_key}"},
            params={"search_query": search_query},
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()

        if isinstance(data, dict):
            return data.get("courses", []) or data.get("data", []) or []

        if isinstance(data, list):
            return data

        return []

    except Exception:
        return []


@st.cache_data(show_spinner=False)
def api_get_course_details(course_id):
    api_key = get_api_key()

    if not api_key:
        return {}

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/courses/{course_id}",
            headers={"Authorization": f"Key {api_key}"},
            timeout=20
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception:
        return {}


def get_course_id(course):
    return course.get("id") or course.get("course_id")


def get_course_name(course):
    return (
        course.get("course_name")
        or course.get("name")
        or course.get("club_name")
        or "Unknown Course"
    )


def get_course_city(course):
    city = course.get("city", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        city = city or location.get("city", "")

    return str(city).strip()


def get_course_state(course):
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        state = state or location.get("state", "")

    return str(state).upper().strip()


def normalize_course(course):
    return {
        "id": get_course_id(course),
        "name": get_course_name(course),
        "city": get_course_city(course),
        "state": get_course_state(course),
        "raw": course
    }


def course_label_from_index(course):
    name = course.get("name", "Unknown Course")
    city = course.get("city", "")
    state = course.get("state", "")

    if city and state:
        return f"{name} — {city}, {state}"

    if state:
        return f"{name} — {state}"

    return name


def load_course_index():
    path = Path(COURSE_INDEX_FILE)

    if not path.exists():
        return []

    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def save_course_index(index):
    Path(COURSE_INDEX_FILE).write_text(json.dumps(index, indent=2))


def merge_courses(existing_index, new_courses):
    merged = {}

    for course in existing_index:
        course_id = course.get("id")
        if course_id:
            merged[str(course_id)] = course

    for course in new_courses:
        normalized = normalize_course(course)
        course_id = normalized.get("id")

        if course_id:
            merged[str(course_id)] = normalized

    return list(merged.values())


@st.cache_data(show_spinner=False)
def discover_courses_for_state(state_name, state_abbrev):
    discovered = []

    search_terms = [state_name, state_abbrev] + COURSE_SWEEP_TERMS

    for term in search_terms:
        results = api_search_courses(term)

        for course in results:
            if get_course_state(course) == state_abbrev:
                discovered.append(course)

    normalized = {}

    for course in discovered:
        course_id = get_course_id(course)

        if course_id:
            normalized[str(course_id)] = normalize_course(course)

    return sorted(
        list(normalized.values()),
        key=lambda c: (c.get("name", "").lower(), c.get("city", "").lower())
    )


def get_indexed_courses_for_state(state_abbrev):
    index = load_course_index()

    return sorted(
        [c for c in index if c.get("state") == state_abbrev],
        key=lambda c: (c.get("name", "").lower(), c.get("city", "").lower())
    )


def get_course_display_name(course):
    name = get_course_name(course)
    city = get_course_city(course)
    state = get_course_state(course)

    if city and state:
        return f"{name} — {city}, {state}"
    if state:
        return f"{name} — {state}"
    return name


def get_tee_options(course_details):
    tee_options = []
    course_data = course_details.get("course", course_details)
    tees = course_data.get("tees", {})

    if not isinstance(tees, dict):
        return tee_options

    for gender in ["male", "female"]:
        for tee in tees.get(gender, []):
            tee_name = tee.get("tee_name", "Unnamed Tee")
            total_yards = tee.get("total_yards", "")
            rating = tee.get("course_rating", "")
            slope = tee.get("slope_rating", "")

            parts = [tee_name]

            if total_yards:
                parts.append(f"{total_yards} yds")
            if rating:
                parts.append(f"Rating {rating}")
            if slope:
                parts.append(f"Slope {slope}")

            parts.append(gender.title())

            tee_options.append({
                "label": " • ".join(parts),
                "tee": tee
            })

    return tee_options


def get_holes_from_tee(tee):
    clean_holes = []

    for index, hole in enumerate(tee.get("holes", []), start=1):
        try:
            par = int(hole.get("par", 4))
        except Exception:
            par = 4

        try:
            yards = int(hole.get("yards") or hole.get("yardage") or 0)
        except Exception:
            yards = 0

        clean_holes.append({
            "hole": index,
            "par": par,
            "yards": yards,
            "handicap": hole.get("handicap") or hole.get("hcp") or ""
        })

    return clean_holes


def get_tee_quality_options(par):
    if int(par) == 3:
        return TEE_QUALITIES_PAR_3
    return TEE_QUALITIES_PAR_4_5


def get_default_tee_quality(par):
    if int(par) == 3:
        return "PERFECT"
    return "AVERAGE"


def default_hole_entry(hole_info):
    par = hole_info["par"]

    return {
        "hole": hole_info["hole"],
        "par": par,
        "yards": hole_info["yards"],
        "handicap": hole_info["handicap"],
        "score": par,
        "putts": 2,
        "tee_club": "DR",
        "tee_location": "CENTER",
        "tee_quality": get_default_tee_quality(par),
        "inside_100_in_3": "NO",
        "hazards": {hazard: 0 for hazard in HAZARDS},
        "gashes": {gash: 0 for gash in GASHES},
    }


def init_round_entries():
    st.session_state.round_entries = {}

    for hole_info in st.session_state.hole_data:
        hole_num = hole_info["hole"]
        st.session_state.round_entries[hole_num] = default_hole_entry(hole_info)

    st.session_state.current_hole_index = 0


def set_value(hole_num, field, value):
    st.session_state.round_entries[hole_num][field] = value


def set_nested_value(hole_num, group, key, value):
    st.session_state.round_entries[hole_num][group][key] = value


def tee_cell_color(par, location, quality):
    dark_red = "#b00000"
    bright_red = "#ff0900"
    dark_green = "#007a3d"
    medium_green = "#68c34a"
    light_green = "#94c83d"
    perfect_green = "#00ff00"

    lost = location in ["LOST LEFT", "LOST RIGHT"]
    side = location in ["LEFT", "RIGHT"]
    center = location == "CENTER"

    if int(par) == 3:
        if quality == "TOO LONG":
            return dark_red
        if quality == "LITTLE LONG":
            return bright_red if lost else dark_green if side else medium_green
        if quality == "PERFECT":
            return bright_red if lost else medium_green if side else perfect_green
        if quality == "LITTLE SHORT":
            return bright_red if lost else dark_green if side else medium_green
        if quality == "MIS-HIT SHORT":
            return dark_red

    else:
        if quality == "TOO LONG":
            return dark_red
        if quality == "CRUSHED":
            return bright_red if lost else medium_green if side else perfect_green
        if quality == "AVERAGE":
            return bright_red if lost else dark_green if side else light_green
        if quality == "MIS-HIT SHORT":
            return dark_red

    return "#4DDB68"


st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background-color: black;
}

.block-container {
    padding-top: 1rem;
    max-width: 1100px;
}

.video-wrap {
    width: 100%;
    margin: 25px auto 70px auto;
    display: flex;
    justify-content: center;
}

.video-wrap video {
    width: 100%;
    max-width: 760px;
    border: 2px solid #111111;
}

.start-title {
    text-align: center;
    color: #4DDB68;
    font-size: 72px;
    font-weight: 900;
    margin-bottom: 40px;
}

.compact-hole-card {
    background: #4DDB68;
    margin-top: 14px;
    margin-bottom: 18px;
    padding: 18px 18px 16px 18px;
}

.compact-hole-title {
    color: white;
    font-size: 56px;
    font-weight: 1000;
    text-align: center;
    line-height: 1;
    margin-bottom: 14px;
}

.compact-hole-meta {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.compact-hole-meta-box {
    background: black;
    color: white;
    text-align: center;
    padding: 10px 4px;
    font-size: 20px;
    font-weight: 1000;
}

.compact-hole-meta-box span {
    color: #ff3529;
}

.hole-nav-row {
    display: grid;
    grid-template-columns: 70px 1fr 70px;
    gap: 10px;
    margin-top: 8px;
    margin-bottom: 10px;
}

.hole-nav-btn {
    background: #4DDB68;
    color: white !important;
    text-decoration: none !important;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 58px;
    font-size: 30px;
    font-weight: 1000;
}

.hole-nav-current {
    background: #1f2028;
    color: white;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 26px;
    font-weight: 1000;
}

.big-label {
    color: white;
    font-size: 44px;
    font-weight: 1000;
    margin-top: 14px;
    margin-bottom: 4px;
}

.section-title {
    color: #4DDB68;
    font-size: 58px;
    font-weight: 1000;
    text-align: center;
    margin-top: 26px;
    margin-bottom: 18px;
}

.white-line {
    border-top: 5px solid white;
    margin: 30px 0 22px 0;
}

.api-note {
    color: #AAAAAA;
    text-align: center;
    font-size: 16px;
    margin-bottom: 20px;
}

.summary-box {
    color: white;
    border: 2px solid #333;
    padding: 20px;
    font-size: 22px;
    font-weight: 800;
}

label {
    color: white !important;
    font-weight: 800 !important;
    font-size: 18px !important;
}

input {
    color: white !important;
}

.stButton > button {
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    border-radius: 0px !important;
    min-height: 68px !important;
    font-size: 22px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

div[data-baseweb="select"] > div {
    min-height: 58px !important;
    font-size: 22px !important;
}

.tee-grid-caption {
    color: #AAAAAA;
    text-align: center;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 16px;
}

.tee-selected-note {
    color: #4DDB68;
    text-align: center;
    font-size: 18px;
    font-weight: 1000;
    margin-top: 18px;
    margin-bottom: 8px;
}

.tee-html-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    width: 100%;
    margin-top: 8px;
}

.tee-col-title {
    color: yellow;
    text-align: center;
    font-size: 22px;
    font-weight: 1000;
    margin-bottom: 8px;
}

.tee-tile {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 58px;
    margin-bottom: 8px;
    text-decoration: none !important;
    color: black !important;
    font-size: 24px;
    font-weight: 1000;
    line-height: 1;
    text-align: center;
    border: 3px solid transparent;
    box-sizing: border-box;
}

.tee-tile.selected {
    border: 4px solid white;
    box-shadow: 0 0 0 2px #4DDB68;
}

.tile-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 18px;
    width: 100%;
    margin-top: 20px;
}

.main-tile-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 22px;
    width: 100%;
    margin-top: 24px;
    margin-bottom: 10px;
}

.stat-card {
    background: #191919;
}

.stat-img {
    width: 100%;
    aspect-ratio: 1 / 1;
    object-fit: cover;
    display: block;
}

.stat-value {
    color: white;
    text-align: center;
    font-size: 82px;
    font-weight: 1000;
    line-height: 1;
    padding: 28px 0 18px 0;
}

.stat-controls {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0;
}

.stat-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    background: #4DDB68;
    color: white !important;
    text-decoration: none !important;
    height: 48px;
    font-size: 34px;
    font-weight: 1000;
}

.stat-btn.minus {
    background: #333333;
}

@media (max-width: 768px) {
    .block-container {
        padding-left: .45rem;
        padding-right: .45rem;
        padding-top: .35rem;
        max-width: 100%;
    }

    .start-title {
        font-size: 46px;
        margin-bottom: 24px;
    }

    .hole-nav-row {
        grid-template-columns: 46px 1fr 46px;
        gap: 6px;
        margin-top: 0px;
        margin-bottom: 8px;
    }

    .hole-nav-btn {
        height: 42px;
        font-size: 20px;
    }

    .hole-nav-current {
        height: 42px;
        font-size: 20px;
    }

    .compact-hole-card {
        margin-top: 8px;
        margin-bottom: 12px;
        padding: 13px 10px 10px 10px;
    }

    .compact-hole-title {
        font-size: 42px;
        margin-bottom: 10px;
    }

    .compact-hole-meta {
        gap: 5px;
    }

    .compact-hole-meta-box {
        padding: 7px 2px;
        font-size: 13px;
        line-height: 1.05;
    }

    .big-label {
        font-size: 38px;
        margin-top: 12px;
    }

    .section-title {
        font-size: 42px;
        line-height: 1;
        margin-top: 20px;
        margin-bottom: 16px;
    }

    .white-line {
        margin: 24px 0 18px 0;
        border-top: 4px solid white;
    }

    .stButton > button {
        min-height: 48px !important;
        font-size: 16px !important;
    }

    .tee-html-grid {
        gap: 4px;
    }

    .tee-col-title {
        font-size: 9.5px;
        line-height: 1;
        margin-bottom: 4px;
        min-height: 18px;
    }

    .tee-tile {
        height: 38px;
        margin-bottom: 4px;
        font-size: 8.7px;
        border: 1px solid transparent;
        padding: 0 1px;
        letter-spacing: -0.2px;
    }

    .tee-tile.selected {
        border: 2px solid white;
        box-shadow: 0 0 0 1px #4DDB68;
    }

    .tee-selected-note {
        font-size: 13px;
        margin-top: 10px;
    }

    .tee-grid-caption {
        font-size: 12px;
        margin-bottom: 10px;
    }

    .tile-grid {
        gap: 5px;
        margin-top: 12px;
    }

    .main-tile-grid {
        gap: 10px;
        margin-top: 14px;
        margin-bottom: 6px;
    }

    .stat-value {
        font-size: 34px;
        padding: 14px 0 10px 0;
    }

    .stat-btn {
        height: 32px;
        font-size: 22px;
    }

    div[data-baseweb="select"] > div {
        min-height: 52px !important;
        font-size: 20px !important;
    }
}
</style>
""", unsafe_allow_html=True)


def autoplay_video(video_path):
    path = Path(video_path)

    if not path.exists():
        return

    encoded = base64.b64encode(path.read_bytes()).decode()

    st.markdown(
        f"""
        <div class="video-wrap">
            <video autoplay muted loop playsinline>
                <source src="data:video/mp4;base64,{encoded}" type="video/mp4">
            </video>
        </div>
        """,
        unsafe_allow_html=True
    )


def process_query_params(hole_num):
    if "hole_nav" in st.query_params:
        raw = st.query_params.get("hole_nav", "")

        try:
            decoded = unquote(raw)
            hole_data = st.session_state.hole_data
            current_index = st.session_state.current_hole_index

            if decoded == "prev":
                st.session_state.current_hole_index = max(0, current_index - 1)
            elif decoded == "next":
                st.session_state.current_hole_index = min(len(hole_data) - 1, current_index + 1)

            st.query_params.clear()
            st.rerun()

        except Exception:
            st.query_params.clear()

    if "tee_choice" in st.query_params:
        raw = st.query_params.get("tee_choice", "")

        try:
            decoded = unquote(raw)
            selected_hole, location, quality = decoded.split("||")
            selected_hole = int(selected_hole)

            if selected_hole == hole_num:
                set_value(hole_num, "tee_location", location)
                set_value(hole_num, "tee_quality", quality)

            st.query_params.clear()
            st.rerun()

        except Exception:
            st.query_params.clear()

    if "stat_change" in st.query_params:
        raw = st.query_params.get("stat_change", "")

        try:
            decoded = unquote(raw)
            selected_hole, group, key, direction = decoded.split("||")
            selected_hole = int(selected_hole)

            if selected_hole == hole_num:
                if group == "main":
                    if key == "SCORE":
                        current = int(st.session_state.round_entries[hole_num]["score"])
                        current = current + 1 if direction == "plus" else max(1, current - 1)
                        set_value(hole_num, "score", current)

                    elif key == "PUTTS":
                        current = int(st.session_state.round_entries[hole_num]["putts"])
                        current = current + 1 if direction == "plus" else max(0, current - 1)
                        set_value(hole_num, "putts", current)

                else:
                    current = int(st.session_state.round_entries[hole_num][group][key])
                    current = current + 1 if direction == "plus" else max(0, current - 1)
                    set_nested_value(hole_num, group, key, current)

            st.query_params.clear()
            st.rerun()

        except Exception:
            st.query_params.clear()


def render_compact_hole_header(hole_num, entry):
    prev_payload = quote("prev")
    next_payload = quote("next")

    st.markdown(
        f"""
        <div class="hole-nav-row">
            <a class="hole-nav-btn" href="?hole_nav={prev_payload}">◀</a>
            <div class="hole-nav-current">HOLE {hole_num}</div>
            <a class="hole-nav-btn" href="?hole_nav={next_payload}">▶</a>
        </div>

        <div class="compact-hole-card">
            <div class="compact-hole-title">HOLE {hole_num}</div>
            <div class="compact-hole-meta">
                <div class="compact-hole-meta-box">PAR<br><span>{entry['par']}</span></div>
                <div class="compact-hole-meta-box">YARDS<br><span>{entry['yards']}</span></div>
                <div class="compact-hole-meta-box">HDCP<br><span>{entry['handicap']}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_tee_shot_grid(hole_num, entry):
    par = int(entry["par"])
    quality_options = get_tee_quality_options(par)

    if entry["tee_quality"] not in quality_options:
        entry["tee_quality"] = get_default_tee_quality(par)

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>TEE SHOT</div>", unsafe_allow_html=True)

    grid_type = "PAR 3 TEE SHOT GRID" if par == 3 else "PAR 4 / PAR 5 TEE SHOT GRID"
    st.markdown(f"<div class='tee-grid-caption'>{grid_type}</div>", unsafe_allow_html=True)

    selected_club = st.selectbox(
        "CLUB",
        CLUBS,
        index=CLUBS.index(entry["tee_club"]) if entry["tee_club"] in CLUBS else 0,
        key=f"club_{hole_num}"
    )
    set_value(hole_num, "tee_club", selected_club)

    st.markdown("<div class='big-label' style='font-size:34px;'>LOCATION:</div>", unsafe_allow_html=True)

    html_parts = ["<div class='tee-html-grid'>"]

    for location in TEE_LOCATIONS:
        html_parts.append("<div>")
        html_parts.append(f"<div class='tee-col-title'>{location}</div>")

        for quality in quality_options:
            selected_class = "selected" if entry["tee_location"] == location and entry["tee_quality"] == quality else ""
            color = tee_cell_color(par, location, quality)
            payload = quote(f"{hole_num}||{location}||{quality}")

            html_parts.append(
                f"<a class='tee-tile {selected_class}' style='background:{color};' href='?tee_choice={payload}'>{quality}</a>"
            )

        html_parts.append("</div>")

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)

    st.markdown(
        f"<div class='tee-selected-note'>SELECTED: {entry['tee_location']} / {entry['tee_quality']}</div>",
        unsafe_allow_html=True
    )


def render_main_stat_tiles(hole_num, entry):
    html_parts = ["<div class='main-tile-grid'>"]

    for stat_name in ["SCORE", "PUTTS"]:
        image_file = MAIN_IMAGES.get(stat_name, "")
        image_b64 = local_image_base64(image_file)

        value = int(entry["score"]) if stat_name == "SCORE" else int(entry["putts"])

        minus_payload = quote(f"{hole_num}||main||{stat_name}||minus")
        plus_payload = quote(f"{hole_num}||main||{stat_name}||plus")

        img_html = (
            f"<img class='stat-img' src='data:image/png;base64,{image_b64}'>"
            if image_b64 else
            f"<div class='stat-img' style='background:#333;color:white;display:flex;align-items:center;justify-content:center;font-weight:900;'>{stat_name}</div>"
        )

        html_parts.append(
            f"<div class='stat-card'>"
            f"{img_html}"
            f"<div class='stat-value'>{value}</div>"
            f"<div class='stat-controls'>"
            f"<a class='stat-btn minus' href='?stat_change={minus_payload}'>−</a>"
            f"<a class='stat-btn' href='?stat_change={plus_payload}'>+</a>"
            f"</div>"
            f"</div>"
        )

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_image_stat_grid(title, items, images, group, hole_num, entry):
    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)

    html_parts = ["<div class='tile-grid'>"]

    for item in items:
        image_file = images.get(item, "")
        image_b64 = local_image_base64(image_file)

        minus_payload = quote(f"{hole_num}||{group}||{item}||minus")
        plus_payload = quote(f"{hole_num}||{group}||{item}||plus")
        value = int(entry[group][item])

        img_html = (
            f"<img class='stat-img' src='data:image/png;base64,{image_b64}'>"
            if image_b64 else
            f"<div class='stat-img' style='background:#333;color:white;display:flex;align-items:center;justify-content:center;font-weight:900;'>{item}</div>"
        )

        html_parts.append(
            f"<div class='stat-card'>"
            f"{img_html}"
            f"<div class='stat-value'>{value}</div>"
            f"<div class='stat-controls'>"
            f"<a class='stat-btn minus' href='?stat_change={minus_payload}'>−</a>"
            f"<a class='stat-btn' href='?stat_change={plus_payload}'>+</a>"
            f"</div>"
            f"</div>"
        )

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)


if "screen" not in st.session_state:
    st.session_state.screen = "home"


if st.session_state.screen == "home":
    autoplay_video(VIDEO_FILE)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("PLAY GOLF"):
            st.session_state.screen = "start_round"
            st.rerun()


elif st.session_state.screen == "start_round":
    st.markdown("<div class='start-title'>START ROUND</div>", unsafe_allow_html=True)

    today = date.today()
    upcoming_dates = [today + timedelta(days=i) for i in range(365)]
    formatted_dates = [d.strftime("%A, %B %d, %Y") for d in upcoming_dates]

    selected_date_label = st.selectbox("DATE", formatted_dates, index=0)
    round_date = upcoming_dates[formatted_dates.index(selected_date_label)]

    state_names = list(US_STATES.keys())

    selected_state_name = st.selectbox(
        "STATE",
        state_names,
        index=state_names.index("Kentucky")
    )

    selected_state_abbrev = US_STATES[selected_state_name]

    st.markdown(
        "<div class='api-note'>Courses are saved into a local course index, then filtered by state.</div>",
        unsafe_allow_html=True
    )

    if st.button("UPDATE COURSE INDEX"):
        with st.spinner("Searching API and updating local course index..."):
            discovered = discover_courses_for_state(selected_state_name, selected_state_abbrev)
            current_index = load_course_index()
            updated_index = merge_courses(current_index, [c["raw"] for c in discovered])
            save_course_index(updated_index)

        st.success(f"Course index updated. Found {len(discovered)} courses for {selected_state_name}.")
        st.rerun()

    state_courses = get_indexed_courses_for_state(selected_state_abbrev)

    if not state_courses:
        st.warning("No courses saved for this state yet. Tap UPDATE COURSE INDEX.")
        st.stop()

    course_options = {
        course_label_from_index(course): course
        for course in state_courses
    }

    selected_course_label = st.selectbox("COURSE", list(course_options.keys()))
    selected_course = course_options[selected_course_label]
    course_id = selected_course.get("id")

    if not course_id:
        st.warning("This course does not include a usable course ID.")
        st.stop()

    with st.spinner("Loading tees..."):
        course_details = api_get_course_details(course_id)

    if not course_details:
        st.warning("Could not load course details from the Golf Course API.")
        st.stop()

    tee_options = get_tee_options(course_details)

    if not tee_options:
        st.warning("Course loaded, but no tee boxes were found.")
        st.stop()

    tee_labels = [option["label"] for option in tee_options]
    selected_tee_label = st.selectbox("TEE", tee_labels)

    selected_tee = tee_options[tee_labels.index(selected_tee_label)]["tee"]
    tee_holes = get_holes_from_tee(selected_tee)

    if not tee_holes:
        st.warning("Tee selected, but no hole-by-hole yardage data was found.")
        st.stop()

    max_holes = len(tee_holes)

    if max_holes >= 18:
        holes = st.selectbox("HOLES", [9, 18], index=1)
    else:
        holes = st.selectbox("HOLES", [max_holes])

    st.success("Course loaded successfully.")

    if st.button("START ROUND"):
        st.session_state.course = selected_course_label
        st.session_state.api_course = selected_course_label
        st.session_state.tee = selected_tee_label
        st.session_state.holes = holes
        st.session_state.hole_data = tee_holes[:holes]
        st.session_state.round_date = round_date

        init_round_entries()

        st.session_state.screen = "scorecard"
        st.rerun()


elif st.session_state.screen == "scorecard":
    if "round_entries" not in st.session_state:
        init_round_entries()

    hole_data = st.session_state.hole_data
    current_index = st.session_state.current_hole_index
    hole_info = hole_data[current_index]
    hole_num = hole_info["hole"]
    entry = st.session_state.round_entries[hole_num]

    process_query_params(hole_num)

    render_compact_hole_header(hole_num, entry)

    render_main_stat_tiles(hole_num, entry)

    render_tee_shot_grid(hole_num, entry)

    render_image_stat_grid(
        title="PENALTIES / HAZARDS",
        items=HAZARDS,
        images=PENALTY_IMAGES,
        group="hazards",
        hole_num=hole_num,
        entry=entry
    )

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>SCORING ZONE</div>", unsafe_allow_html=True)

    st.markdown(
        "<div class='big-label' style='font-size:30px;'>INSIDE 100 YARDS IN 3 SHOTS?</div>",
        unsafe_allow_html=True
    )

    inside_answer = st.radio(
        "INSIDE 100",
        ["YES", "NO"],
        index=0 if entry["inside_100_in_3"] == "YES" else 1,
        horizontal=True,
        key=f"inside_100_{hole_num}",
        label_visibility="collapsed"
    )

    set_value(hole_num, "inside_100_in_3", inside_answer)

    render_image_stat_grid(
        title="GASHES",
        items=GASHES,
        images=GASH_IMAGES,
        group="gashes",
        hole_num=hole_num,
        entry=entry
    )

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

    bottom1, bottom2 = st.columns(2)

    with bottom1:
        if st.button("SETUP"):
            st.session_state.screen = "start_round"
            st.rerun()

    with bottom2:
        if st.button("FINISH"):
            st.session_state.screen = "round_summary"
            st.rerun()


elif st.session_state.screen == "round_summary":
    st.markdown("<div class='start-title'>ROUND SUMMARY</div>", unsafe_allow_html=True)

    entries = st.session_state.round_entries

    total_score = sum(value["score"] for value in entries.values())
    total_par = sum(value["par"] for value in entries.values())
    total_putts = sum(value["putts"] for value in entries.values())

    relation = total_score - total_par
    relation_text = "E" if relation == 0 else f"+{relation}" if relation > 0 else str(relation)

    st.markdown(
        f"""
        <div class='summary-box'>
        COURSE: {st.session_state.course}<br>
        TEE: {st.session_state.tee}<br>
        SCORE: {total_score} ({relation_text})<br>
        PUTTS: {total_putts}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(entries)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("EDIT ROUND"):
            st.session_state.screen = "scorecard"
            st.rerun()

    with col2:
        if st.button("HOME"):
            st.session_state.screen = "home"
            st.rerun()