import base64
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"

@st.cache_data
def load_courses():
    if Path("opengolfapi-us.csv").exists():
        return pd.read_csv("opengolfapi-us.csv")
    if Path("data/opengolfapi-us.csv").exists():
        return pd.read_csv("data/opengolfapi-us.csv")
    st.error("Course database not found.")
    st.stop()

df = load_courses()

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

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
    display: block;
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
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    round_date = st.date_input("DATE", value=date.today())

    states = sorted(df["state"].dropna().unique())
    selected_state = st.selectbox("STATE", states)

    filtered_courses = df[df["state"] == selected_state]
    course_names = sorted(filtered_courses["name"].dropna().unique())
    selected_course = st.selectbox("COURSE", course_names)

    course_rows = filtered_courses[filtered_courses["name"] == selected_course]

    tee_options = ["Default"]
    if "tee_name" in df.columns:
        tee_options = sorted(course_rows["tee_name"].dropna().unique())
        if len(tee_options) == 0:
            tee_options = ["Default"]

    selected_tee = st.selectbox("TEE", tee_options)

    holes = st.selectbox("HOLES", [9, 18], index=1)

    if st.button("START ROUND"):
        if selected_tee != "Default" and "tee_name" in df.columns:
            selected_rows = course_rows[course_rows["tee_name"] == selected_tee]
        else:
            selected_rows = course_rows

        course_row = selected_rows.iloc[0]

        st.session_state.course = selected_course
        st.session_state.tee = selected_tee
        st.session_state.holes = holes
        st.session_state.course_row = course_row.to_dict()
        st.session_state.screen = "scorecard"
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.screen == "scorecard":
    course = st.session_state.course
    tee = st.session_state.tee
    holes = st.session_state.holes
    row = st.session_state.course_row

    st.markdown(f"<div class='start-title'>{course}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='tee-title'>TEE: {tee}</div>", unsafe_allow_html=True)

    total_score = 0
    total_par = 0

    for hole in range(1, holes + 1):
        par_col = f"hole_{hole}_par"
        yard_col = f"hole_{hole}_yards"

        par = row.get(par_col, 4)
        yards = row.get(yard_col, 0)

        if pd.isna(par):
            par = 4
        if pd.isna(yards):
            yards = 0

        par = int(par)
        yards = int(yards)

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

    if st.button("FINISH ROUND"):
        st.session_state.screen = "home"
        st.rerun()
