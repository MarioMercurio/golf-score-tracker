import base64
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"

# -----------------------------------
# STYLING
# -----------------------------------

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
    max-width: 900px;
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

.section-box {
    border: 1px solid #222;
    padding: 30px;
    border-radius: 12px;
    background-color: #050505;
}

.stButton > button {
    background-color: #4DDB68 !important;
    color: white !important;
    border: none !important;
    border-radius: 0px !important;
    height: 90px !important;
    font-size: 36px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

.hole-title {
    color: white;
    font-size: 30px;
    font-weight: 900;
    margin-top: 30px;
}

.tee-title {
    text-align: center;
    color: white;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 40px;
}

label {
    color: white !important;
    font-weight: 700 !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# VIDEO
# -----------------------------------

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

# -----------------------------------
# API FUNCTIONS
# -----------------------------------

@st.cache_data
def get_courses_by_state(state):

    url = f"https://api.opengolfapi.org/v1/courses/state/{state}"

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            return response.json()

    except:
        return []

    return []

# -----------------------------------
# SESSION STATE
# -----------------------------------

if "screen" not in st.session_state:
    st.session_state.screen = "home"

# -----------------------------------
# HOME SCREEN
# -----------------------------------

if st.session_state.screen == "home":

    autoplay_video(VIDEO_FILE)

    st.markdown(
        """
        <div style='text-align:center; margin-top:20px;'>
            <img src='https://raw.githubusercontent.com/MarioMercurio/golf-score-tracker/main/GOLFLOGO.png' width='780'>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        if st.button("PLAY GOLF"):

            st.session_state.screen = "start_round"
            st.rerun()

# -----------------------------------
# START ROUND SCREEN
# -----------------------------------

elif st.session_state.screen == "start_round":

    st.markdown(
        "<div class='start-title'>START ROUND</div>",
        unsafe_allow_html=True
    )

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    round_date = st.date_input(
        "DATE",
        value=date.today()
    )

    # -----------------------------------
    # STATE
    # -----------------------------------

    states = [
        "AL","AK","AZ","AR","CA","CO","CT","DE",
        "FL","GA","HI","ID","IL","IN","IA","KS",
        "KY","LA","ME","MD","MA","MI","MN","MS",
        "MO","MT","NE","NV","NH","NJ","NM","NY",
        "NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV",
        "WI","WY"
    ]

    selected_state = st.selectbox(
        "STATE",
        states,
        index=18
    )

    # -----------------------------------
    # LOAD COURSES
    # -----------------------------------

    courses = get_courses_by_state(selected_state)

    course_names = []

    for course in courses:

        if "name" in course:
            course_names.append(course["name"])

    course_names = sorted(list(set(course_names)))

    selected_course = st.selectbox(
        "COURSE",
        course_names
    )

    tee_played = st.text_input(
        "TEE PLAYED",
        value="Blue"
    )

    holes = st.selectbox(
        "HOLES",
        [9, 18],
        index=1
    )

    if st.button("START ROUND"):

        st.session_state.course = selected_course
        st.session_state.tee = tee_played
        st.session_state.holes = holes

        st.session_state.screen = "scorecard"

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------
# SCORECARD
# -----------------------------------

elif st.session_state.screen == "scorecard":

    course = st.session_state.course
    tee = st.session_state.tee
    holes = st.session_state.holes

    st.markdown(
        f"<div class='start-title'>{course}</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='tee-title'>TEE: {tee}</div>",
        unsafe_allow_html=True
    )

    total_score = 0

    for hole in range(1, holes + 1):

        st.markdown(
            f"<div class='hole-title'>HOLE {hole}</div>",
            unsafe_allow_html=True
        )

        score = st.number_input(
            f"Score Hole {hole}",
            min_value=1,
            max_value=20,
            value=4,
            step=1,
            key=f"hole_{hole}"
        )

        total_score += score

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style='
            text-align:center;
            color:white;
            font-size:40px;
            font-weight:900;
            margin-bottom:40px;
        '>
            TOTAL: {total_score}
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("FINISH ROUND"):

        st.session_state.screen = "home"
        st.rerun()
