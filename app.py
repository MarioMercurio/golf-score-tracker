import base64
from datetime import date
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"

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
    display: block;
}

div.stButton > button {
    width: 100%;
    background-color: #59e36a;
    color: white;
    border: none;
    border-radius: 0px;
    height: 105px;
    font-size: 42px;
    font-weight: 900;
    font-family: Arial Black, sans-serif;
    letter-spacing: 2px;
}

div.stButton > button:hover {
    background-color: #45c957;
    color: white;
    border: none;
}

.section-title {
    color: white;
    font-size: 42px;
    font-weight: 900;
    text-align: center;
    margin-bottom: 30px;
    font-family: Arial Black, sans-serif;
}

label {
    color: white !important;
    font-weight: 700 !important;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input {
    background-color: #111111 !important;
    color: white !important;
    border: 1px solid #59e36a !important;
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


if "page" not in st.session_state:
    st.session_state.page = "home"


if st.session_state.page == "home":
    autoplay_video(VIDEO_FILE)

    left, middle, right = st.columns([1, 3, 1])

    with middle:
        if st.button("PLAY GOLF"):
            st.session_state.page = "play"
            st.rerun()


if st.session_state.page == "play":
    if st.button("← BACK"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown(
        '<div class="section-title">PLAY GOLF</div>',
        unsafe_allow_html=True
    )

    with st.form("round_form"):
        round_date = st.date_input("DATE", value=date.today())
        course = st.text_input("COURSE")
        tees = st.text_input("TEES")
        holes = st.selectbox("HOLES", [18, 9])

        submitted = st.form_submit_button("START ROUND")

        if submitted:
            if course.strip() == "":
                st.error("Please enter a course.")
            else:
                st.success("Round started.")
