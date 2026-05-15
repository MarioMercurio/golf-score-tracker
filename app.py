import base64
from datetime import date
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

US_STATES = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}

# =========================================================
# API FUNCTIONS
# =========================================================

def get_api_key():
    return (
        st.secrets.get("GOLF_API_KEY", "")
        or st.secrets.get("GOLF_COURSE_API_KEY", "")
    )


@st.cache_data(show_spinner=False)
def api_search_courses(search_query):
    api_key = get_api_key()

    if not api_key:
        return []

    headers = {"Authorization": f"Key {api_key}"}
    params = {"search_query": search_query}

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/search",
            headers=headers,
            params=params,
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

    headers = {"Authorization": f"Key {api_key}"}

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/courses/{course_id}",
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception:
        return {}


def get_course_display_name(course):
    club = course.get("club_name", "")
    course_name = course.get("course_name", "")
    name = course.get("name", "")
    city = course.get("city", "")
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        city = city or location.get("city", "")
        state = state or location.get("state", "")

    main_name = course_name or name or club or "Unknown Course"

    if city and state:
        return f"{main_name} — {city}, {state}"
    if state:
        return f"{main_name} — {state}"
    return main_name


def get_course_state(course):
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        state = state or location.get("state", "")

    return str(state).upper().strip()


def filter_courses_by_state(courses, state_abbrev):
    filtered = []

    for course in courses:
        course_state = get_course_state(course)

        if course_state == state_abbrev.upper():
            filtered.append(course)

    return filtered


def get_course_id(course):
    return course.get("id") or course.get("course_id")


def get_tee_options(course_details):
    tee_options = []

    course_data = course_details.get("course", course_details)
    tees = course_data.get("tees", {})

    if isinstance(tees, dict):
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
                    label_parts.append(f"{total_yards} yds")
                if rating:
                    label_parts.append(f"Rating {rating}")
                if slope:
                    label_parts.append(f"Slope {slope}")

                label_parts.append(gender.title())
                label = " • ".join(label_parts)

                tee_options.append({
                    "label": label,
                    "tee": tee,
                    "gender": gender
                })

    elif isinstance(tees, list):
        for tee in tees:
            tee_name = tee.get("tee_name") or tee.get("name") or tee.get("color") or "Unnamed Tee"
            total_yards = tee.get("total_yards") or tee.get("yards") or tee.get("yardage") or ""
            rating = tee.get("course_rating") or tee.get("rating") or ""
            slope = tee.get("slope_rating") or tee.get("slope") or ""

            label_parts = [tee_name]

            if total_yards:
                label_parts.append(f"{total_yards} yds")
            if rating:
                label_parts.append(f"Rating {rating}")
            if slope:
                label_parts.append(f"Slope {slope}")

            label = " • ".join(label_parts)

            tee_options.append({
                "label": label,
                "tee": tee,
                "gender": ""
            })

    return tee_options


def get_holes_from_tee(tee):
    holes = tee.get("holes", [])
    clean_holes = []

    if not isinstance(holes, list):
        return clean_holes

    for index, hole in enumerate(holes, start=1):
        par = hole.get("par", 4)
        yards = hole.get("yards") or hole.get("yardage") or 0
        handicap = hole.get("handicap") or hole.get("hcp") or ""

        try:
            par = int(par)
        except Exception:
            par = 4

        try:
            yards = int(yards)
        except Exception:
            yards = 0

        clean_holes.append({
            "hole": index,
            "par": par,
            "yards": yards,
            "handicap": handicap
        })

    return clean_holes


# =========================================================
# STYLE
# =========================================================

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
    max-width: 950px;
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

.stButton > button {
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    border-radius: 0px !important;
    height: 90px !important;
    font-size: 34px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

.hole-title {
    color: white;
    font-size: 28px;
    font-weight: 900;
    margin-top: 26px;
}

.tee-title {
    text-align: center;
    color: white;
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 35px;
}

label {
    color: white !important;
    font-weight: 700 !important;
}

.api-note {
    color: #AAAAAA;
    text-align: center;
    font-size: 16px;
    margin-bottom: 20px;
}

div[data-baseweb="select"] > div {
    background-color: #111111;
    color: white;
}

input {
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


def autoplay_video(video_path):
    path = Path(video_path)

    if not path.exists():
        return

    video_bytes = path.read_bytes()
    encoded = base64.b64encode(video_bytes).decode()

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
# APP STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"


# =========================================================
# HOME
# =========================================================

if st.session_state.screen == "home":
    autoplay_video(VIDEO_FILE)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("PLAY GOLF"):
            st.session_state.screen = "start_round"
            st.rerun()


# =========================================================
# START ROUND
# =========================================================

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
        "<div class='api-note'>Course search, tee boxes and hole yardages are now powered only by the Golf Course API.</div>",
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

    if state_matches:
        courses_to_show = state_matches
    else:
        st.warning(f"No exact matches found in {selected_state_name}. Showing all API matches.")
        courses_to_show = api_matches

    api_match_labels = [get_course_display_name(course) for course in courses_to_show]

    selected_match_label = st.selectbox("COURSE", api_match_labels)

    selected_match_index = api_match_labels.index(selected_match_label)
    selected_match = courses_to_show[selected_match_index]

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
        st.warning("Course loaded, but no tee boxes were found in the API detail response.")
        st.stop()

    tee_labels = [option["label"] for option in tee_options]
    selected_tee_label = st.selectbox("TEE", tee_labels)

    selected_tee_index = tee_labels.index(selected_tee_label)
    selected_tee = tee_options[selected_tee_index]["tee"]

    tee_holes = get_holes_from_tee(selected_tee)

    if not tee_holes:
        st.warning("Tee selected, but no hole-by-hole yardage data was found.")
        st.stop()

    max_holes = len(tee_holes)

    if max_holes >= 18:
        holes = st.selectbox("HOLES", [9, 18], index=1)
    else:
        holes = st.selectbox("HOLES", [max_holes], index=0)

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

        st.session_state.screen = "scorecard"
        st.rerun()


# =========================================================
# SCORECARD
# =========================================================

elif st.session_state.screen == "scorecard":
    course = st.session_state.course
    tee = st.session_state.tee
    hole_data = st.session_state.hole_data

    st.markdown(f"<div class='start-title'>{course}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='tee-title'>TEE: {tee}</div>", unsafe_allow_html=True)

    total_score = 0
    total_par = 0

    for hole_info in hole_data:
        hole = hole_info["hole"]
        par = hole_info["par"]
        yards = hole_info["yards"]

        total_par += par

        st.markdown(
            f"<div class='hole-title'>HOLE {hole} • PAR {par} • {yards} YDS</div>",
            unsafe_allow_html=True
        )

        score = st.number_input(
            f"Score Hole {hole}",
            min_value=1,
            max_value=20,
            value=par,
            step=1,
            key=f"hole_{hole}"
        )

        total_score += score

    relation = total_score - total_par
    relation_text = "E" if relation == 0 else f"+{relation}" if relation > 0 else str(relation)

    st.markdown(
        f"""
        <div style='text-align:center; color:white; font-size:40px; font-weight:900; margin:40px 0;'>
            TOTAL: {total_score} ({relation_text})
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("BACK"):
            st.session_state.screen = "start_round"
            st.rerun()

    with col2:
        if st.button("FINISH ROUND"):
            st.session_state.screen = "home"
            st.rerun()
