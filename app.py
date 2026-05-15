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

# =========================================================
# PAGE STYLING
# =========================================================

st.markdown("""
<style>

#MainMenu, footer, header {
    visibility: hidden;
}

html, body, [class*="css"] {
    font-family: Arial, Helvetica, sans-serif;
}

.stApp {
    background-color: black;
}

.block-container {
    padding-top: 1rem;
    max-width: 1100px;
}

/* =========================
VIDEO
========================= */

.video-wrap {
    width: 100%;
    margin: 20px auto 50px auto;
    display: flex;
    justify-content: center;
}

.video-wrap video {
    width: 100%;
    max-width: 760px;
    border: 2px solid #111111;
}

/* =========================
TITLES
========================= */

.start-title {
    text-align: center;
    color: #59E36A;
    font-size: 84px;
    font-weight: 900;
    margin-bottom: 40px;
    line-height: 0.95;
}

.section-title {
    text-align: center;
    color: #59E36A;
    font-size: 64px;
    font-weight: 900;
    margin-top: 50px;
    margin-bottom: 25px;
    line-height: 1;
}

/* =========================
BUTTONS
========================= */

.stButton > button {
    background-color: #59E36A !important;
    color: white !important;
    border: none !important;
    border-radius: 0px !important;
    height: 80px !important;
    font-size: 28px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

/* =========================
LABELS
========================= */

label {
    color: white !important;
    font-size: 20px !important;
    font-weight: 700 !important;
}

/* =========================
ALL INPUT FONT SIZES
========================= */

.stSelectbox div[data-baseweb="select"] > div {
    font-size: 26px !important;
    min-height: 68px !important;
}

.stTextInput input {
    font-size: 26px !important;
    min-height: 68px !important;
}

.stDateInput input {
    font-size: 26px !important;
    min-height: 68px !important;
}

/* =========================
DATE DISPLAY
========================= */

.pretty-date {
    text-align: center;
    color: white;
    font-size: 34px;
    font-weight: 700;
    margin-top: -10px;
    margin-bottom: 35px;
}

/* =========================
INFO TEXT
========================= */

.api-note {
    color: #BDBDBD;
    text-align: center;
    font-size: 20px;
    line-height: 1.5;
    margin-top: 20px;
    margin-bottom: 30px;
}

/* =========================
MOBILE
========================= */

@media (max-width: 768px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .start-title {
        font-size: 62px;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 42px;
    }

    .pretty-date {
        font-size: 24px;
        margin-bottom: 20px;
    }

    label {
        font-size: 16px !important;
    }

    .stSelectbox div[data-baseweb="select"] > div {
        font-size: 22px !important;
        min-height: 60px !important;
    }

    .stTextInput input {
        font-size: 22px !important;
        min-height: 60px !important;
    }

    .stDateInput input {
        font-size: 22px !important;
        min-height: 60px !important;
    }

    .api-note {
        font-size: 16px;
    }

    .stButton > button {
        height: 68px !important;
        font-size: 22px !important;
    }
}

</style>
""", unsafe_allow_html=True)

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
# API
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
# SESSION STATE
# =========================================================

if "screen" not in st.session_state:
    st.session_state.screen = "home"

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

    round_date = st.date_input(
        "DATE",
        value=date.today()
    )

    formatted_date = round_date.strftime("%A, %B %d, %Y")

    st.markdown(
        f"<div class='pretty-date'>{formatted_date}</div>",
        unsafe_allow_html=True
    )

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
        index=17
    )

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
        st.info("Type a course name to search.")
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

    selected_course = st.selectbox(
        "SELECT COURSE",
        match_labels
    )

    st.success("Course loaded successfully.")