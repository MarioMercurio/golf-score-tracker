import base64
import json
from datetime import date, timedelta
from pathlib import Path

import requests
import streamlit as st

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# CONSTANTS
# =========================================================

VIDEO_FILE = "GolfIntro.mp4"
API_BASE_URL = "https://api.golfcourseapi.com"
COURSE_INDEX_FILE = "course_index.json"

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
    "", "golf", "club", "country club", "course", "links",
    "national", "municipal", "park", "valley", "lake",
    "ridge", "river", "creek", "woods", "meadows",
    "pointe", "point", "green", "oak", "pine"
]

# =========================================================
# API
# =========================================================

def get_api_key():
    return st.secrets.get("GOLF_API_KEY", "")


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
            return data.get("courses", [])

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

# =========================================================
# COURSE HELPERS
# =========================================================

def get_course_id(course):
    return course.get("id")


def get_course_name(course):
    return (
        course.get("course_name")
        or course.get("club_name")
        or "Unknown Course"
    )


def get_course_city(course):
    return str(course.get("city", "")).strip()


def get_course_state(course):
    return str(course.get("state", "")).upper().strip()


def normalize_course(course):

    return {
        "id": get_course_id(course),
        "name": get_course_name(course),
        "city": get_course_city(course),
        "state": get_course_state(course),
        "raw": course
    }


def course_label(course):

    name = course.get("name", "")
    city = course.get("city", "")
    state = course.get("state", "")

    if city and state:
        return f"{name} — {city}, {state}"

    return name

# =========================================================
# COURSE INDEX
# =========================================================

def load_course_index():

    path = Path(COURSE_INDEX_FILE)

    if not path.exists():
        return []

    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def save_course_index(index):

    Path(COURSE_INDEX_FILE).write_text(
        json.dumps(index, indent=2)
    )


def merge_courses(existing_index, new_courses):

    merged = {}

    for course in existing_index:
        merged[str(course["id"])] = course

    for course in new_courses:

        normalized = normalize_course(course)

        if normalized["id"]:
            merged[str(normalized["id"])] = normalized

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

    deduped = {}

    for course in discovered:

        course_id = get_course_id(course)

        if course_id:
            deduped[str(course_id)] = normalize_course(course)

    return sorted(
        list(deduped.values()),
        key=lambda c: c["name"].lower()
    )


def get_courses_for_state(state_abbrev):

    index = load_course_index()

    return sorted(
        [c for c in index if c["state"] == state_abbrev],
        key=lambda c: c["name"].lower()
    )

# =========================================================
# TEE BOXES
# =========================================================

def get_tee_options(course_details):

    tee_options = []

    course_data = course_details.get("course", {})
    tees = course_data.get("tees", {})

    if not isinstance(tees, dict):
        return tee_options

    for gender in ["male", "female"]:

        gender_tees = tees.get(gender, [])

        if not isinstance(gender_tees, list):
            continue

        for tee in gender_tees:

            tee_name = tee.get("tee_name", "Unnamed Tee")
            total_yards = tee.get("total_yards", "")
            rating = tee.get("course_rating", "")
            slope = tee.get("slope_rating", "")

            label_parts = [tee_name]

            if total_yards:
                label_parts.append(f"{total_yards} YDS")

            if rating:
                label_parts.append(f"RATING {rating}")

            if slope:
                label_parts.append(f"SLOPE {slope}")

            label = " • ".join(label_parts)

            tee_options.append({
                "label": label,
                "tee": tee
            })

    return tee_options


def get_holes_from_tee(tee):

    clean_holes = []

    for index, hole in enumerate(tee.get("holes", []), start=1):

        clean_holes.append({
            "hole": index,
            "par": int(hole.get("par", 4)),
            "yards": int(hole.get("yards", 0))
        })

    return clean_holes

# =========================================================
# VIDEO
# =========================================================

def autoplay_video(video_path):

    path = Path(video_path)

    if not path.exists():
        return

    encoded = base64.b64encode(
        path.read_bytes()
    ).decode()

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

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

#MainMenu,
footer,
header {
    visibility: hidden;
}

html,
body,
[data-testid="stAppViewContainer"] {
    background: black;
}

.stApp {
    background-color: black;
}

.block-container {
    max-width: 900px;
    padding-top: 0.5rem;
}

/* VIDEO */

.video-wrap {
    width: 100%;
    display: flex;
    justify-content: center;
    margin-bottom: 40px;
}

.video-wrap video {
    width: 100%;
    max-width: 720px;
}

/* TITLES */

.start-title {
    text-align: center;
    color: #5BE06C;
    font-size: 64px;
    font-weight: 900;
    margin-bottom: 30px;
}

/* INPUTS */

label {
    color: white !important;
    font-size: 20px !important;
    font-weight: 700 !important;
}

.stSelectbox div[data-baseweb="select"] > div {
    background: #242533 !important;
    color: white !important;
    min-height: 72px !important;
    border-radius: 14px !important;
    font-size: 26px !important;
    display: flex !important;
    align-items: center !important;
}

.stSelectbox span {
    font-size: 26px !important;
}

.stButton > button {
    background-color: #5BE06C !important;
    color: black !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 24px !important;
    font-weight: 900 !important;
    height: 68px !important;
    width: 100% !important;
}

/* SCORECARD */

.hole-banner {
    background: #181818;
    border: 2px solid #333333;
    padding: 18px;
    margin-bottom: 25px;
}

.hole-number {
    color: #5BE06C;
    font-size: 42px;
    font-weight: 900;
}

.hole-info {
    color: white;
    font-size: 22px;
    font-weight: 700;
}

.section-title {
    color: white;
    font-size: 26px;
    font-weight: 900;
    margin-top: 35px;
    margin-bottom: 18px;
}

.icon-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
}

.icon-button {
    background: #222222;
    border: 2px solid #333333;
    border-radius: 14px;
    padding: 14px;
    text-align: center;
    color: white;
    font-weight: 700;
    min-height: 110px;
}

/* MOBILE */

@media (max-width: 768px) {

    .start-title {
        font-size: 52px;
    }

    .hole-number {
        font-size: 34px;
    }

    .hole-info {
        font-size: 18px;
    }

    .section-title {
        font-size: 22px;
    }

    .icon-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .stSelectbox div[data-baseweb="select"] > div {
        font-size: 22px !important;
        min-height: 64px !important;
    }

    .stSelectbox span {
        font-size: 22px !important;
    }

    .stButton > button {
        font-size: 20px !important;
        height: 62px !important;
    }
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# SESSION STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

if "current_hole" not in st.session_state:
    st.session_state.current_hole = 1

# =========================================================
# HOME
# =========================================================

if st.session_state.screen == "home":

    autoplay_video(VIDEO_FILE)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        if st.button("PLAY GOLF"):

            st.session_state.screen = "start_round"
            st.rerun()

# =========================================================
# START ROUND
# =========================================================

elif st.session_state.screen == "start_round":

    st.markdown(
        "<div class='start-title'>START ROUND</div>",
        unsafe_allow_html=True
    )

    today = date.today()

    upcoming_dates = [
        today + timedelta(days=i)
        for i in range(365)
    ]

    formatted_dates = [
        d.strftime("%A, %B %d, %Y")
        for d in upcoming_dates
    ]

    selected_date = st.selectbox(
        "DATE",
        formatted_dates
    )

    state_names = list(US_STATES.keys())

    selected_state = st.selectbox(
        "STATE",
        state_names,
        index=state_names.index("Kentucky")
    )

    selected_state_abbrev = US_STATES[selected_state]

    if st.button("UPDATE COURSE INDEX"):

        with st.spinner("Updating course index..."):

            discovered = discover_courses_for_state(
                selected_state,
                selected_state_abbrev
            )

            current_index = load_course_index()

            updated_index = merge_courses(
                current_index,
                [c["raw"] for c in discovered]
            )

            save_course_index(updated_index)

        st.success(f"Loaded {len(discovered)} courses.")
        st.rerun()

    state_courses = get_courses_for_state(
        selected_state_abbrev
    )

    if not state_courses:

        st.warning(
            "No courses loaded for this state yet."
        )

        st.stop()

    course_labels = [
        course_label(c)
        for c in state_courses
    ]

    selected_course_label = st.selectbox(
        "COURSE",
        course_labels
    )

    selected_course = state_courses[
        course_labels.index(selected_course_label)
    ]

    course_id = selected_course["id"]

    course_details = api_get_course_details(course_id)

    tee_options = get_tee_options(course_details)

    tee_labels = [
        t["label"]
        for t in tee_options
    ]

    selected_tee_label = st.selectbox(
        "TEE",
        tee_labels
    )

    selected_tee = tee_options[
        tee_labels.index(selected_tee_label)
    ]["tee"]

    hole_data = get_holes_from_tee(selected_tee)

    if st.button("START ROUND"):

        st.session_state.course = selected_course_label
        st.session_state.tee = selected_tee_label
        st.session_state.hole_data = hole_data

        st.session_state.screen = "scorecard"

        st.rerun()

# =========================================================
# SCORECARD
# =========================================================

elif st.session_state.screen == "scorecard":

    hole_data = st.session_state.hole_data
    current_hole = st.session_state.current_hole

    hole = hole_data[current_hole - 1]

    st.markdown(
        f"""
        <div class='hole-banner'>
            <div class='hole-number'>
                HOLE {hole['hole']}
            </div>
            <div class='hole-info'>
                PAR {hole['par']} • {hole['yards']} YDS
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # =====================================================
    # TEE SHOT
    # =====================================================

    st.markdown(
        "<div class='section-title'>TEE SHOT</div>",
        unsafe_allow_html=True
    )

    if hole["par"] == 3:

        st.markdown(
            """
            <div class='icon-grid'>
                <div class='icon-button'>CENTER</div>
                <div class='icon-button'>LEFT</div>
                <div class='icon-button'>RIGHT</div>
                <div class='icon-button'>SHORT</div>
                <div class='icon-button'>LONG</div>
                <div class='icon-button'>GREEN</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            """
            <div class='icon-grid'>
                <div class='icon-button'>FAIRWAY</div>
                <div class='icon-button'>LEFT</div>
                <div class='icon-button'>RIGHT</div>
                <div class='icon-button'>ROUGH</div>
                <div class='icon-button'>BUNKER</div>
                <div class='icon-button'>WATER</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =====================================================
    # PENALTIES
    # =====================================================

    st.markdown(
        "<div class='section-title'>PENALTIES</div>",
        unsafe_allow_html=True
    )

    penalty_cols = st.columns(5)

    penalty_labels = [
        ("🚫", "OB"),
        ("🌊", "WATER"),
        ("🌲", "TREE"),
        ("⛳", "UNPLAYABLE"),
        ("❌", "OTHER")
    ]

    for col, (emoji, label) in zip(penalty_cols, penalty_labels):

        with col:

            st.button(
                f"{emoji}\n{label}",
                key=f"penalty_{label}_{current_hole}"
            )

    # =====================================================
    # GASHES
    # =====================================================

    st.markdown(
        "<div class='section-title'>GASHES</div>",
        unsafe_allow_html=True
    )

    gash_cols = st.columns(5)

    gash_labels = [
        ("💣", "BOMB"),
        ("🎯", "PIN"),
        ("🔥", "HOT"),
        ("⚡", "PURE"),
        ("🪄", "MAGIC")
    ]

    for col, (emoji, label) in zip(gash_cols, gash_labels):

        with col:

            st.button(
                f"{emoji}\n{label}",
                key=f"gash_{label}_{current_hole}"
            )

    # =====================================================
    # PUTTS
    # =====================================================

    st.markdown(
        "<div class='section-title'>PUTTS</div>",
        unsafe_allow_html=True
    )

    putt_cols = st.columns(6)

    for i in range(6):

        with putt_cols[i]:

            st.button(
                str(i),
                key=f"putts_{i}_{current_hole}"
            )

    # =====================================================
    # SCORE
    # =====================================================

    st.markdown(
        "<div class='section-title'>SCORE</div>",
        unsafe_allow_html=True
    )

    score_cols = st.columns(8)

    for i in range(1, 9):

        with score_cols[i - 1]:

            st.button(
                str(i),
                key=f"score_{i}_{current_hole}"
            )

    # =====================================================
    # NAVIGATION
    # =====================================================

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        if current_hole > 1:

            if st.button("PREVIOUS HOLE"):

                st.session_state.current_hole -= 1
                st.rerun()

    with col2:

        if current_hole < len(hole_data):

            if st.button("NEXT HOLE"):

                st.session_state.current_hole += 1
                st.rerun()

        else:

            if st.button("FINISH ROUND"):

                st.session_state.screen = "home"
                st.session_state.current_hole = 1

                st.rerun()