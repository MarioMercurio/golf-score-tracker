import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Golf Score Tracker",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# BASIC STYLING
# -----------------------------
st.markdown(
    """
    <style>
        .stApp {
            background-color: #000000;
        }

        div[data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }

        .main-title {
            font-family: monospace;
            font-size: 96px;
            font-weight: 900;
            letter-spacing: 6px;
            color: #4DDB68;
            text-align: center;
            margin-top: 20px;
            margin-bottom: 20px;
            text-shadow: 0px 10px 0px #137C2A;
        }

        .logo-box {
            border: 1px solid #111111;
            padding: 20px;
            margin-bottom: 60px;
        }

        .play-button button {
            background-color: #4DDB68 !important;
            color: white !important;
            border: none !important;
            border-radius: 0px !important;
            height: 90px !important;
            font-size: 42px !important;
            font-weight: 900 !important;
            letter-spacing: 2px !important;
            width: 100% !important;
        }

        .section-title {
            color: white;
            text-align: center;
            font-size: 34px;
            font-weight: 900;
            margin-bottom: 20px;
        }

        label, .stTextInput label, .stDateInput label, .stNumberInput label, .stSelectbox label {
            color: white !important;
            font-weight: 700 !important;
        }

        .stTextInput input, .stNumberInput input {
            background-color: #111111 !important;
            color: white !important;
            border: 1px solid #4DDB68 !important;
        }

        .stSelectbox div {
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# SIMPLE PAGE STATE
# -----------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# -----------------------------
# HOME PAGE
# -----------------------------
if st.session_state.page == "home":
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)
    st.markdown('<div class="main-title">GOLF</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="play-button">', unsafe_allow_html=True)
    if st.button("PLAY GOLF", use_container_width=True):
        st.session_state.page = "play_golf"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# PLAY GOLF PAGE
# -----------------------------
if st.session_state.page == "play_golf":
    if st.button("← BACK"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown('<div class="section-title">PLAY GOLF</div>', unsafe_allow_html=True)

    with st.form("play_golf_form"):
        round_date = st.date_input("Date", value=date.today())
        course = st.text_input("Course")
        tees = st.text_input("Tees")
        holes = st.selectbox("Holes", [18, 9])

        submitted = st.form_submit_button("START ROUND")

        if submitted:
            st.success("Round started. Next we will build the hole-by-hole score entry screen.")
