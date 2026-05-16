import base64
import json
from datetime import date, timedelta
from pathlib import Path

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
    "", "golf", "club", "country club", "course", "links", "national",
    "municipal", "park", "valley", "lake", "lakes", "hills", "ridge",
    "river", "creek", "woods", "meadows", "pointe", "point", "legacy",
    "green", "greens", "oak", "oaks", "pine", "pines", "blue", "red",
    "a", "e", "i", "o", "u", "r", "s", "t", "n", "l", "m", "c"
]


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


def get_course_display_name(course):
    name = get_course_name(course)
    city = get_course_city(course)
    state = get_course_state(course)

    if city and state:
        return f"{name} — {city}, {state}"

    if state:
        return f"{name} — {state}"

    return name


def normalize_course(course):
    return {
        "id": get_course_id(course),
        "name": get_course_name(course),
        "city": get_course_city(course),
        "state": get_course_state(course),
        "raw": course
    }


def load_course_index():
    path = Path(COURSE_INDEX_FILE)

    if not path.exists():
        return []

    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def save_course_index(index):
    path = Path(COURSE_INDEX_FILE)
    path.write_text(json.dumps(index, indent=2))


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
            course_state = get_course_state(course)

            if course_state == state_abbrev:
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


def course_label_from_index(course):
    name = course.get("name", "Unknown Course")
    city = course.get("city", "")
    state = course.get("state", "")

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
        gender_tees = tees.get(gender, [])

        if not isinstance(gender_tees, list):
            continue

        for tee in gender_tees:
            tee_name = tee.get("tee_name", "Unnamed Tee")
            total_yards = tee.get("total_yards", "")
            rating = tee.get("course_rating", "")
            slope = tee.get("slope_rating", "")

            parts = [tee_name]

            if total_yards:
                parts.append(f"{total_yards} YDS")
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
    padding-top: 0.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1100px;
}

.video-wrap {
    width: 100%;
    margin-top: 10px;
    margin-bottom: 40px;
    display: flex;
    justify-content: center;
}

.video-wrap video {
    width: 100%;
    max-width: 700px;
}

.start-title {
    text-align: center;
    color: #5BE06C;
    font-size: 72px;
    font-weight: 900;
    line-height: 0.95;
    margin-top: 10px;
    margin-bottom: 45px;
}

label {
    color: white !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

.api-note {
    color: #B8B8B8;
    text-align: center;
    font-size: 18px;
    margin-top: 25px;
    margin-bottom: 25px;
    line-height: 1.5;
}

.stSelectbox div[data-baseweb="select"] > div {
    background-color: #242533 !important;
    color: white !important;
    font-size: 28px !important;
    min-height: 74px !important;
    border-radius: 14px !important;
    display: flex !important;
    align-items: center !important;
}

.stSelectbox span {
    display: flex !important;
    align-items: center !important;
    font-size: 28px !important;
}

.stButton > button {
    background-color: #5BE06C !important;
    color: black !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 28px !important;
    font-weight: 900 !important;
    height: 72px !important;
    width: 100% !important;
}

div[data-testid="stAlert"] {
    font-size: 24px;
    border-radius: 16px;
}

@media (max-width: 768px) {

    .block-container {
        padding-left: 14px;
        padding-right: 14px;
        padding-top: 0px;
    }

    .start-title {
        font-size: 58px;
        margin-bottom: 28px;
    }

    label {
        font-size: 16px !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        font-size: 22px !important;
        min-height: 66px !important;
        height: 66px !important;
    }

    .stSelectbox span {
        font-size: 22px !important;
    }

    .api-note {
        font-size: 15px;
        margin-top: 18px;
        margin-bottom: 18px;
    }

    .stButton > button {
        font-size: 22px !important;
        height: 64px !important;
    }
}

</style>
""", unsafe_allow_html=True)


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

    st.markdown(
        "<div class='start-title'>START ROUND</div>",
        unsafe_allow_html=True
    )

    today = date.today()

    upcoming_dates = [
        today + timedelta(days=i)
        for i in range(0, 365)
    ]

    formatted_dates = [
        d.strftime("%A, %B %d, %Y")
        for d in upcoming_dates
    ]

    selected_date_label = st.selectbox(
        "DATE",
        formatted_dates,
        index=0
    )

    selected_date_index = formatted_dates.index(selected_date_label)
    round_date = upcoming_dates[selected_date_index]

    state_names = list(US_STATES.keys())

    selected_state = st.selectbox(
        "STATE",
        state_names,
        index=state_names.index("Kentucky")
    )

    selected_state_abbrev = US_STATES[selected_state]

    st.markdown(
        """
        <div class='api-note'>
        Courses are saved into a local course index, then filtered by state.
        </div>
        """,
        unsafe_allow_html=True
    )

    existing_state_courses = get_indexed_courses_for_state(selected_state_abbrev)

    if st.button("UPDATE COURSE INDEX"):
        with st.spinner("Searching API and updating local course index..."):
            discovered = discover_courses_for_state(selected_state, selected_state_abbrev)
            current_index = load_course_index()
            updated_index = merge_courses(current_index, [c["raw"] for c in discovered])
            save_course_index(updated_index)

        st.success(f"Course index updated. Found {len(discovered)} courses for {selected_state}.")
        st.rerun()

    state_courses = get_indexed_courses_for_state(selected_state_abbrev)

    if not state_courses:
        st.warning("No courses saved for this state yet. Tap UPDATE COURSE INDEX.")
        st.stop()

    course_options = {
        course_label_from_index(course): course
        for course in state_courses
    }

    selected_course_label = st.selectbox(
        "COURSE",
        list(course_options.keys())
    )

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

    tee_labels = [
        option["label"]
        for option in tee_options
    ]

    selected_tee_label = st.selectbox(
        "TEE",
        tee_labels
    )

    selected_tee = tee_options[tee_labels.index(selected_tee_label)]["tee"]
    tee_holes = get_holes_from_tee(selected_tee)

    if not tee_holes:
        st.warning("Tee selected, but no hole-by-hole yardage data was found.")
        st.stop()

    st.success("Course loaded successfully.")

    if st.button("START ROUND"):
        st.session_state.round_date = round_date
        st.session_state.course = selected_course_label
        st.session_state.tee = selected_tee_label
        st.session_state.hole_data = tee_holes
        st.session_state.screen = "scorecard"
        st.rerun()