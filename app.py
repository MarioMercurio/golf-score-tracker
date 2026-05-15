import streamlit as st
import pandas as pd
from datetime import date

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------
# LOAD COURSE DATA
# -----------------------------------

@st.cache_data
def load_courses():
    df = pd.read_csv("opengolfapi-us.csv")
    return df

df = load_courses()

# -----------------------------------
# SESSION STATE
# -----------------------------------

if "screen" not in st.session_state:
    st.session_state.screen = "home"

# -----------------------------------
# STYLING
# -----------------------------------

st.markdown("""
<style>

.stApp {
    background-color: black;
}

header {
    visibility: hidden;
}

.main-title {
    text-align: center;
    color: #4DDB68;
    font-size: 90px;
    font-weight: 900;
    margin-top: 20px;
    margin-bottom: 40px;
    text-shadow: 0px 6px #137C2A;
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
    font-size: 40px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

.hole-title {
    color: white;
    font-size: 34px;
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

</style>
""", unsafe_allow_html=True)

# -----------------------------------
# HOME SCREEN
# -----------------------------------

if st.session_state.screen == "home":

    st.image("GolfIntro.mp4")

    st.markdown("""
    <div style='text-align:center; margin-top:20px;'>
        <img src='https://raw.githubusercontent.com/MarioMercurio/golf-score-tracker/main/GOLFLOGO.png' width='780'>
    </div>
    """, unsafe_allow_html=True)

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
    # STATE DROPDOWN
    # -----------------------------------

    states = sorted(df["state"].dropna().unique())

    selected_state = st.selectbox(
        "STATE",
        states
    )

    # -----------------------------------
    # FILTER COURSES
    # -----------------------------------

    filtered_courses = df[df["state"] == selected_state]

    course_names = sorted(
        filtered_courses["name"].dropna().unique()
    )

    selected_course = st.selectbox(
        "COURSE",
        course_names
    )

    # -----------------------------------
    # GET COURSE ROW
    # -----------------------------------

    course_row = filtered_courses[
        filtered_courses["name"] == selected_course
    ].iloc[0]

    # -----------------------------------
    # TEE OPTIONS
    # -----------------------------------

    tee_options = []

    if "tee_name" in df.columns:
        tee_options = sorted(
            filtered_courses[
                filtered_courses["name"] == selected_course
            ]["tee_name"].dropna().unique()
        )

    if len(tee_options) == 0:
        tee_options = ["Default"]

    selected_tee = st.selectbox(
        "TEE",
        tee_options
    )

    holes = st.selectbox(
        "HOLES",
        [9, 18],
        index=1
    )

    if st.button("START ROUND"):

        st.session_state.course = selected_course
        st.session_state.tee = selected_tee
        st.session_state.holes = holes
        st.session_state.course_row = course_row.to_dict()

        st.session_state.screen = "scorecard"

        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------
# SCORECARD SCREEN
# -----------------------------------

elif st.session_state.screen == "scorecard":

    course = st.session_state.course
    tee = st.session_state.tee
    holes = st.session_state.holes
    row = st.session_state.course_row

    st.markdown(
        f"<div class='start-title'>{course}</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        f"<div class='tee-title'>TEE: {tee}</div>",
        unsafe_allow_html=True
    )

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

        total_par += int(par)

        st.markdown(
            f"<div class='hole-title'>HOLE {hole} • PAR {int(par)} • {int(yards)} YDS</div>",
            unsafe_allow_html=True
        )

        score = st.number_input(
            f"Score Hole {hole}",
            min_value=1,
            max_value=20,
            value=int(par),
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
            TOTAL: {total_score} (+{total_score-total_par})
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("FINISH ROUND"):
        st.session_state.screen = "home"
        st.rerun()
