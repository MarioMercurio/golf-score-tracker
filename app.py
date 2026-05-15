import base64
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

# =========================================================
# API FUNCTIONS
# =========================================================

@st.cache_data
def api_search_courses(search_query):

    api_key = st.secrets.get("GOLF_API_KEY", "")

    if not api_key:
        return []

    headers = {
        "Authorization": f"Key {api_key}"
    }

    params = {
        "search_query": search_query
    }

    try:

        response = requests.get(
            f"{API_BASE_URL}/v1/search",
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return []

        return response.json().get("courses", [])

    except Exception:
        return []

# =========================================================
# COURSE DETAILS
# =========================================================

@st.cache_data
def api_get_course_details(course_id):

    api_key = st.secrets.get("GOLF_API_KEY", "")

    if not api_key:
        return {}

    headers = {
        "Authorization": f"Key {api_key}"
    }

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

# =========================================================
# DISPLAY NAME
# =========================================================

def get_course_display_name(course):

    club = course.get("club_name", "")
    course_name = course.get("course_name", "")
    city = course.get("city", "")
    state = course.get("state", "")

    main_name = course_name or club or "Unknown Course"

    if city and state:
        return f"{main_name} — {city}, {state}"

    if state:
        return f"{main_name} — {state}"

    return main_name

# =========================================================
# TEE OPTIONS
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

            label = f"{tee_name} • {total_yards} YDS • {gender.title()}"

            tee_options.append({
                "label": label,
                "tee": tee
            })

    return tee_options

# =========================================================
# HOLES
# =========================================================

def get_holes_from_tee(tee):

    holes = tee.get("holes", [])

    clean_holes = []

    for index, hole in enumerate(holes, start=1):

        clean_holes.append({
            "hole": index,
            "par": int(hole.get("par", 4)),
            "yards": int(hole.get("yards", 0)),
            "handicap": hole.get("handicap", "")
        })

    return clean_holes

# =========================================================
# VIDEO
# =========================================================

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
    padding-top: 0.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 1100px;
}

/* =====================================================
VIDEO
===================================================== */

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

/* =====================================================
TITLES
===================================================== */

.start-title {
    text-align: center;
    color: #5BE06C;
    font-size: 72px;
    font-weight: 900;
    line-height: 0.95;
    margin-top: 10px;
    margin-bottom: 45px;
}

/* =====================================================
LABELS
===================================================== */

label {
    color: white !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

/* =====================================================
API NOTE
===================================================== */

.api-note {
    color: #B8B8B8;
    text-align: center;
    font-size: 18px;
    margin-top: 25px;
    margin-bottom: 25px;
    line-height: 1.5;
}

/* =====================================================
SELECT BOXES
===================================================== */

.stSelectbox div[data-baseweb="select"] > div {
    background-color: #242533 !important;
    color: white !important;
    font-size: 28px !important;
    min-height: 74px !important;
    border-radius: 14px !important;

    display: flex !important;
    align-items: center !important;
}

/* dropdown text */
.stSelectbox span {
    display: flex !important;
    align-items: center !important;
}

/* =====================================================
TEXT INPUT
===================================================== */

.stTextInput input {
    background-color: #242533 !important;
    color: white !important;
    font-size: 28px !important;
    height: 74px !important;
    border-radius: 14px !important;

    padding-top: 0px !important;
    padding-bottom: 0px !important;

    line-height: 74px !important;
}

/* placeholder */
.stTextInput input::placeholder {
    font-size: 28px !important;
    opacity: 0.7 !important;
}

/* =====================================================
BUTTONS
===================================================== */

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

/* =====================================================
ALERTS
===================================================== */

div[data-testid="stAlert"] {
    font-size: 24px;
    border-radius: 16px;
}

/* =====================================================
MOBILE
===================================================== */

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
    }

    .stSelectbox span {
        font-size: 22px !important;
    }

    .stTextInput input {
        font-size: 22px !important;
        height: 66px !important;
        line-height: 66px !important;
        padding-right: 16px !important;
    }

    .stTextInput input::placeholder {
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

# =========================================================
# SESSION STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

# =========================================================
# HOME SCREEN
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

    st.markdown(
        "<div class='start-title'>START ROUND</div>",
        unsafe_allow_html=True
    )

    # =====================================================
    # DATE
    # =====================================================

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

    # =====================================================
    # STATES
    # =====================================================

    states = [
        "Alabama",
        "Alaska",
        "Arizona",
        "Arkansas",
        "California",
        "Colorado",
        "Connecticut",
        "Delaware",
        "Florida",
        "Georgia",
        "Hawaii",
        "Idaho",
        "Illinois",
        "Indiana",
        "Iowa",
        "Kansas",
        "Kentucky",
        "Louisiana",
        "Maine",
        "Maryland",
        "Massachusetts",
        "Michigan",
        "Minnesota",
        "Mississippi",
        "Missouri",
        "Montana",
        "Nebraska",
        "Nevada",
        "New Hampshire",
        "New Jersey",
        "New Mexico",
        "New York",
        "North Carolina",
        "North Dakota",
        "Ohio",
        "Oklahoma",
        "Oregon",
        "Pennsylvania",
        "Rhode Island",
        "South Carolina",
        "South Dakota",
        "Tennessee",
        "Texas",
        "Utah",
        "Vermont",
        "Virginia",
        "Washington",
        "West Virginia",
        "Wisconsin",
        "Wyoming"
    ]

    selected_state = st.selectbox(
        "STATE",
        states,
        index=16
    )

    # =====================================================
    # COURSE SEARCH
    # =====================================================

    search_course = st.text_input(
        "COURSE SEARCH",
        placeholder="Type course name..."
    )

    st.markdown(
        """
        <div class='api-note'>
        Course search, tee boxes and hole yardages are powered only by the Golf Course API.
        </div>
        """,
        unsafe_allow_html=True
    )

    if search_course.strip() == "":
        st.stop()

    api_matches = api_search_courses(search_course)

    filtered_matches = []

    for course in api_matches:

        course_state = course.get("state", "")

        if course_state == selected_state:
            filtered_matches.append(course)

    if not filtered_matches:
        st.warning("No matching courses found.")
        st.stop()

    match_labels = [
        get_course_display_name(course)
        for course in filtered_matches
    ]

    selected_course_label = st.selectbox(
        "SELECT COURSE",
        match_labels
    )

    selected_course_index = match_labels.index(selected_course_label)

    selected_course = filtered_matches[selected_course_index]

    course_id = selected_course.get("id")

    course_details = api_get_course_details(course_id)

    tee_options = get_tee_options(course_details)

    tee_labels = [
        option["label"]
        for option in tee_options
    ]

    selected_tee_label = st.selectbox(
        "TEE",
        tee_labels
    )

    selected_tee_index = tee_labels.index(selected_tee_label)

    selected_tee = tee_options[selected_tee_index]["tee"]

    tee_holes = get_holes_from_tee(selected_tee)

    st.success("Course loaded successfully.")

    # =====================================================
    # START ROUND BUTTON
    # =====================================================

    if st.button("START ROUND"):

        st.session_state.round_date = round_date
        st.session_state.course = selected_course_label
        st.session_state.tee = selected_tee_label
        st.session_state.hole_data = tee_holes

        st.session_state.screen = "scorecard"

        st.rerun()