import streamlit as st
from datetime import date

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------
# PAGE STYLING
# ---------------------------------------------------
st.markdown("""
<style>

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

.stApp {
    background-color: black;
}

.block-container {
    padding-top: 1rem;
    max-width: 850px;
}

/* Video spacing */
.video-container {
    margin-bottom: 20px;
}

/* Main Logo */
.golf-title {
    text-align: center;
    font-size: 120px;
    font-weight: 900;
    color: #59e36a;
    line-height: 1;
    margin-top: 10px;
    margin-bottom: 50px;
    letter-spacing: 4px;
    font-family: Arial Black, sans-serif;
    text-shadow:
        0px 8px 0px #15892d;
}

/* Big green buttons */
div.stButton > button {
    width: 100%;
    background-color: #59e36a;
    color: white;
    border: none;
    border-radius: 0px;
    height: 105px;
    font-size: 44px;
    font-weight: 900;
    margin-top: 20px;
    margin-bottom: 10px;
    font-family: Arial Black, sans-serif;
    letter-spacing: 2px;
}

div.stButton > button:hover {
    background-color: #45c957;
    color: white;
}

/* Form section */
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

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "home"

# ---------------------------------------------------
# HOME PAGE
# ---------------------------------------------------
if st.session_state.page == "home":

    st.markdown('<div class="video-container">', unsafe_allow_html=True)

    st.video("GolfIntro.mp4")

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="golf-title">GOLF</div>',
        unsafe_allow_html=True
    )

    if st.button("PLAY GOLF"):
        st.session_state.page = "play"
        st.rerun()

# ---------------------------------------------------
# PLAY GOLF PAGE
# ---------------------------------------------------
if st.session_state.page == "play":

    if st.button("← BACK"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown(
        '<div class="section-title">PLAY GOLF</div>',
        unsafe_allow_html=True
    )

    with st.form("round_form"):

        round_date = st.date_input(
            "DATE",
            value=date.today()
        )

        course = st.text_input("COURSE")

        tees = st.text_input("TEES")

        holes = st.selectbox(
            "HOLES",
            [18, 9]
        )

        submitted = st.form_submit_button("START ROUND")

        if submitted:

            if course.strip() == "":
                st.error("Please enter a course.")
            else:
                st.success("Round started.")
