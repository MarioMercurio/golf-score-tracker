import base64
from datetime import date
from pathlib import Path
from urllib.parse import quote, unquote

import requests
import streamlit as st

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"
API_BASE_URL = "https://api.golfcourseapi.com"

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
        return data.get("courses", []) if isinstance(data, dict) else []

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


def get_course_display_name(course):
    name = course.get("course_name") or course.get("name") or course.get("club_name") or "Unknown Course"
    city = course.get("city", "")
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        city = city or location.get("city", "")
        state = state or location.get("state", "")

    if city and state:
        return f"{name} — {city}, {state}"
    if state:
        return f"{name} — {state}"
    return name


def get_course_state(course):
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        state = state or location.get("state", "")

    return str(state).upper().strip()


def filter_courses_by_state(courses, state_abbrev):
    return [course for course in courses if get_course_state(course) == state_abbrev.upper()]


def get_course_id(course):
    return course.get("id") or course.get("course_id")


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
            if lost:
                return bright_red
            if side:
                return dark_green
            if center:
                return medium_green
        if quality == "PERFECT":
            if lost:
                return bright_red
            if side:
                return medium_green
            if center:
                return perfect_green
        if quality == "LITTLE SHORT":
            if lost:
                return bright_red
            if side:
                return dark_green
            if center:
                return medium_green
        if quality == "MIS-HIT SHORT":
            return dark_red

    else:
        if quality == "TOO LONG":
            return dark_red
        if quality == "CRUSHED":
            if lost:
                return bright_red
            if side:
                return medium_green
            if center:
                return perfect_green
        if quality == "AVERAGE":
            if lost:
                return bright_red
            if side:
                return dark_green
            if center:
                return light_green
        if quality == "MIS-HIT SHORT":
            return dark_red

    return "#4DDB68"


st.markdown("""
<style>
#MainMenu, footer, header {
    visibility: hidden;
}

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

.hole-header {
    background: #4DDB68;
    color: white;
    font-size: 58px;
    font-weight: 1000;
    text-align: center;
    padding: 18px;
    margin-bottom: 18px;
}

.hole-meta {
    color: white;
    font-size: 28px;
    font-weight: 900;
    line-height: 1.5;
    margin-bottom: 25px;
}

.hole-meta span {
    color: #ff3529;
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

.small-note {
    color: red;
    text-align: center;
    font-size: 14px;
    font-weight: 900;
    margin-top: -8px;
    margin-bottom: 12px;
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

div[data-testid="stNumberInput"] button {
    background-color: #2b2c34 !important;
    color: white !important;
    border-radius: 0px !important;
}

div[data-testid="stNumberInput"] input {
    font-size: 30px !important;
    font-weight: 800 !important;
    min-height: 64px !important;
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

@media (max-width: 768px) {
    .block-container {
        padding-left: .4rem;
        padding-right: .4rem;
        padding-top: .5rem;
        max-width: 100%;
    }

    .start-title {
        font-size: 46px;
        margin-bottom: 24px;
    }

    .hole-header {
        font-size: 42px;
        padding: 14px 8px;
        margin-bottom: 16px;
    }

    .hole-meta {
        font-size: 28px;
        margin-bottom: 16px;
    }

    .big-label {
        font-size: 38px;
        margin-top: 12px;
    }

    .section-title {
        font-size: 44px;
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

    div[data-testid="stNumberInput"] input {
        min-height: 54px !important;
        font-size: 24px !important;
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


def process_tee_query_param(hole_num):
    if "tee_choice" not in st.query_params:
        return

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

            tile = (
                f"<a class='tee-tile {selected_class}' "
                f"style='background:{color};' "
                f"href='?tee_choice={payload}'>"
                f"{quality}</a>"
            )

            html_parts.append(tile)

        html_parts.append("</div>")

    html_parts.append("</div>")

    st.markdown("".join(html_parts), unsafe_allow_html=True)

    st.markdown(
        f"<div class='tee-selected-note'>SELECTED: {entry['tee_location']} / {entry['tee_quality']}</div>",
        unsafe_allow_html=True
    )


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

    round_date = st.date_input("DATE", value=date.today())

    selected_state_name = st.selectbox(
        "STATE",
        list(US_STATES.keys()),
        index=list(US_STATES.keys()).index("Kentucky")
    )

    selected_state = US_STATES[selected_state_name]

    search_query = st.text_input(
        "COURSE SEARCH",
        value="",
        placeholder="Type course name..."
    )

    st.markdown(
        "<div class='api-note'>Course search, tee boxes and hole yardages are powered only by the Golf Course API.</div>",
        unsafe_allow_html=True
    )

    if not get_api_key():
        st.error("Missing Golf API key. Add GOLF_API_KEY to Streamlit secrets.")
        st.stop()

    if not search_query.strip():
        st.info("Type a course name to search.")
        st.stop()

    api_matches = api_search_courses(search_query.strip())

    if not api_matches:
        st.warning("No API course matches found. Try a more specific course name.")
        st.stop()

    state_matches = filter_courses_by_state(api_matches, selected_state)
    courses_to_show = state_matches if state_matches else api_matches

    if not state_matches:
        st.warning(f"No exact matches found in {selected_state_name}. Showing all API matches.")

    api_match_labels = [get_course_display_name(course) for course in courses_to_show]
    selected_match_label = st.selectbox("COURSE", api_match_labels)

    selected_match = courses_to_show[api_match_labels.index(selected_match_label)]
    course_id = get_course_id(selected_match)

    if not course_id:
        st.warning("This API match does not include a course ID.")
        st.stop()

    course_details = api_get_course_details(course_id)

    if not course_details:
        st.warning("Could not load course details from API.")
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

    if st.button("START ROUND"):
        clean_course_name = (
            selected_match.get("course_name")
            or selected_match.get("name")
            or selected_match.get("club_name")
            or selected_match_label
        )

        st.session_state.course = clean_course_name
        st.session_state.api_course = selected_match_label
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

    process_tee_query_param(hole_num)

    nav_left, nav_mid, nav_right = st.columns([1, 1.2, 1])

    with nav_left:
        if st.button("◀") and current_index > 0:
            st.session_state.current_hole_index -= 1
            st.rerun()

    with nav_mid:
        selected_hole = st.selectbox(
            "HOLE",
            [hole["hole"] for hole in hole_data],
            index=current_index,
            label_visibility="collapsed"
        )

        new_index = [hole["hole"] for hole in hole_data].index(selected_hole)

        if new_index != current_index:
            st.session_state.current_hole_index = new_index
            st.rerun()

    with nav_right:
        if st.button("▶") and current_index < len(hole_data) - 1:
            st.session_state.current_hole_index += 1
            st.rerun()

    st.markdown(f"<div class='hole-header'>HOLE {hole_num}</div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class='hole-meta'>
        PAR: <span>{entry['par']}</span><br>
        YARDS: <span>{entry['yards']}</span><br>
        HANDICAP: <span>{entry['handicap']}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='big-label'>SCORE:</div>", unsafe_allow_html=True)

    score = st.number_input(
        "Score",
        min_value=1,
        max_value=20,
        value=int(entry["score"]),
        step=1,
        key=f"score_{hole_num}",
        label_visibility="collapsed"
    )

    set_value(hole_num, "score", score)

    st.markdown("<div class='big-label'>PUTTS:</div>", unsafe_allow_html=True)

    putts = st.number_input(
        "Putts",
        min_value=0,
        max_value=10,
        value=int(entry["putts"]),
        step=1,
        key=f"putts_{hole_num}",
        label_visibility="collapsed"
    )

    set_value(hole_num, "putts", putts)

    render_tee_shot_grid(hole_num, entry)

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>PENALTIES / HAZARDS</div>", unsafe_allow_html=True)

    for hazard in HAZARDS:
        st.markdown(
            f"<div class='big-label' style='font-size:26px; color:yellow; text-align:center;'>{hazard}</div>",
            unsafe_allow_html=True
        )

        value = st.number_input(
            hazard,
            min_value=0,
            max_value=10,
            value=int(entry["hazards"][hazard]),
            step=1,
            key=f"hazard_{hole_num}_{hazard}",
            label_visibility="collapsed"
        )

        set_nested_value(hole_num, "hazards", hazard, value)

        st.markdown("<div class='small-note'>DEFAULT IS 0</div>", unsafe_allow_html=True)

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

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>GASHES</div>", unsafe_allow_html=True)

    for gash in GASHES:
        st.markdown(
            f"<div class='big-label' style='font-size:26px; color:yellow; text-align:center;'>{gash}</div>",
            unsafe_allow_html=True
        )

        value = st.number_input(
            gash,
            min_value=0,
            max_value=10,
            value=int(entry["gashes"][gash]),
            step=1,
            key=f"gash_{hole_num}_{gash}",
            label_visibility="collapsed"
        )

        set_nested_value(hole_num, "gashes", gash, value)

        st.markdown("<div class='small-note'>DEFAULT IS 0</div>", unsafe_allow_html=True)

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