import base64
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"
COURSE_FILE = "courses.csv"

# ---------------------------------------------------
# LOAD COURSE DATA
# ---------------------------------------------------
courses_df = pd.read_csv(COURSE_FILE)

# ---------------------------------------------------
# PAGE STYLING
# ---------------------------------------------------
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

/* Video */
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
    display: block;
}

/* Buttons */
div.stButton > button {
    width: 100%;
    background-color: #59e36a;
    color: white;
    border: none;
    border-radius: 0px;
    height: 90px;
    font-size: 34px;
    font-weight: 900;
    font-family: Arial Black, sans-serif;
    letter-spacing: 2px;
}

div.stButton > button:hover {
    background-color: #45c957;
    color: white;
}

/* Titles */
.section-title {
    color: #59e36a;
    font-size: 54px;
    font-weight: 900;
    text-align: center;
    margin-bottom: 40px;
    font-family: Arial Black, sans-serif;
}

/* Labels */
label {
    color: white !important;
    font-weight: 700 !important;
}

/* Inputs */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox div[data-baseweb="select"] {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #59e36a !important;
}

/* Hole Titles */
.score-hole {
    color: white;
    font-size: 24px;
    font-weight: bold;
    margin-top: 20px;
}

/* Totals */
.score-total {
    color: #59e36a;
    font-size: 40px;
    font-weight: 900;
    text-align: center;
    margin-top: 25px;
    margin-bottom: 25px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def autoplay_video(video_path):

    path = Path(video_path)

    if not path.exists():
        st.warning(f"Video file not found: {video_path}")
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

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

if "holes" not in st.session_state:
    st.session_state.holes = 18

if "scores" not in st.session_state:
    st.session_state.scores = []

# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------
if st.session_state.page == "home":

    autoplay_video(VIDEO_FILE)

    left, middle, right = st.columns([1, 3, 1])

    with middle:
        if st.button("PLAY GOLF"):
            st.session_state.page = "start_round"
            st.rerun()

# ---------------------------------------------------
# START ROUND PAGE
# ---------------------------------------------------
if st.session_state.page == "start_round":

    st.markdown(
        '<div class="section-title">START ROUND</div>',
        unsafe_allow_html=True
    )

    # COURSE OPTIONS
    course_options = sorted(courses_df["course"].unique())

    selected_course = st.selectbox(
        "COURSE",
        course_options
    )

    # TEE OPTIONS BASED ON COURSE
    tee_options = sorted(
        courses_df[courses_df["course"] == selected_course]["tee"].unique()
    )

    selected_tee = st.selectbox(
        "TEES",
        tee_options
    )

    with st.form("start_round_form"):

        round_date = st.date_input(
            "DATE",
            value=date.today()
        )

        holes = st.selectbox(
            "HOLES",
            [18, 9]
        )

        submitted = st.form_submit_button("START ROUND")

        if submitted:

            course_data = courses_df[
                (courses_df["course"] == selected_course) &
                (courses_df["tee"] == selected_tee)
            ]

            st.session_state.holes = len(course_data)
            st.session_state.scores = [4] * len(course_data)

            st.session_state.course = selected_course
            st.session_state.tee = selected_tee
            st.session_state.round_date = round_date

            st.session_state.pars = course_data["par"].tolist()
            st.session_state.yardages = course_data["yardage"].tolist()

            st.session_state.page = "score_entry"
            st.rerun()

# ---------------------------------------------------
# SCORE ENTRY PAGE
# ---------------------------------------------------
if st.session_state.page == "score_entry":

    st.markdown(
        f'<div class="section-title">{st.session_state.course}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"<h3 style='color:white; text-align:center;'>TEE: {st.session_state.tee}</h3>",
        unsafe_allow_html=True
    )

    total_score = 0
    total_par = sum(st.session_state.pars)

    for hole in range(st.session_state.holes):

        par = st.session_state.pars[hole]
        yardage = st.session_state.yardages[hole]

        st.markdown(
            f"""
            <div class="score-hole">
                HOLE {hole + 1} • PAR {par} • {yardage} YDS
            </div>
            """,
            unsafe_allow_html=True
        )

        score = st.number_input(
            f"Score Hole {hole + 1}",
            min_value=1,
            max_value=20,
            value=st.session_state.scores[hole],
            key=f"hole_{hole}"
        )

        st.session_state.scores[hole] = score
        total_score += score

    relative_to_par = total_score - total_par

    if relative_to_par > 0:
        relation_text = f"+{relative_to_par}"
    elif relative_to_par < 0:
        relation_text = f"{relative_to_par}"
    else:
        relation_text = "E"

    st.markdown(
        f"""
        <div class="score-total">
            TOTAL: {total_score}<br>
            ({relation_text})
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("BACK TO HOME"):
            st.session_state.page = "home"
            st.rerun()

    with col2:
        if st.button("SAVE ROUND"):
            st.success("Round Saved")
