import base64
from datetime import date
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="GOLF",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VIDEO_FILE = "GolfIntro.mp4"
COURSE_CSV = "opengolfapi-us.csv"
API_BASE_URL = "https://api.golfcourseapi.com"

# ---------------------------------------------------
# DATA
# ---------------------------------------------------
@st.cache_data
def load_local_courses():
    if Path(COURSE_CSV).exists():
        return pd.read_csv(COURSE_CSV)

    if Path(f"data/{COURSE_CSV}").exists():
        return pd.read_csv(f"data/{COURSE_CSV}")

    return pd.DataFrame()


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

        data = response.json()
        return data.get("courses", [])

    except Exception:
        return []


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


def get_course_display_name(course):
    club = course.get("club_name", "")
    course_name = course.get("course_name", "")
    city = course.get("city", "")
    state = course.get("state", "")

    main_name = course_name or club or "Unknown Course"

    location = ""
    if city and state:
        location = f" — {city}, {state}"
    elif state:
        location = f" — {state}"

    return f"{main_name}{location}"


def get_tee_options(course_details):
    tee_options = []

    tees = course_details.get("tees", {})

    if not isinstance(tees, dict):
        return tee_options

    for gender in ["male", "female"]:
        gender_tees = tees.get(gender, [])

        if not isinstance(gender_tees, list):
            continue

        for tee in gender_tees:
            tee_name = (
                tee.get("tee_name")
                or tee.get("name")
                or tee.get("color")
                or "Unnamed Tee"
            )

            total_yards = (
                tee.get("total_yards")
                or tee.get("total_distance")
                or tee.get("yards")
                or ""
            )

            rating = tee.get("course_rating", tee.get("rating", ""))
            slope = tee.get("slope_rating", tee.get("slope", ""))

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

    return tee_options


def get_holes_from_tee(tee):
    holes = tee.get("holes", [])

    clean_holes = []

    if not isinstance(holes, list):
        return clean_holes

    for index, hole in enumerate(holes, start=1):
        par = (
            hole.get("par")
            or hole.get("hole_par")
            or 4
        )

        yards = (
            hole.get("yards")
            or hole.get("yardage")
            or hole.get("distance")
            or hole.get("tee_yards")
            or 0
        )

        handicap = (
            hole.get("handicap")
            or hole.get("hcp")
            or hole.get("stroke_index")
            or ""
        )

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


local_df = load_local_courses()

# ---------------------------------------------------
# STYLING
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# VIDEO
# ---------------------------------------------------
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

# ---------------------------------------------------
# SESSION STATE
# ---------------------------------------------------
if "screen" not in st.session_state:
    st.session_state.screen = "home"

# ---------------------------------------------------
# HOME
# ---------------------------------------------------
if st.session_state.screen == "home":
    autoplay_video(VIDEO_FILE)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button("PLAY GOLF"):
            st.session_state.screen = "start_round"
            st.rerun()

# ---------------------------------------------------
# START ROUND
# ---------------------------------------------------
elif st.session_state.screen == "start_round":
    st.markdown("<div class='start-title'>START ROUND</div>", unsafe_allow_html=True)

    round_date = st.date_input("DATE", value=date.today())

    if local_df.empty:
        st.error("The local course file was not found.")
        st.stop()

    states = sorted(local_df["state"].dropna().unique())
    selected_state = st.selectbox("STATE", states)

    state_df = local_df[local_df["state"] == selected_state]

    course_names = sorted(state_df["name"].dropna().unique())
    selected_course = st.selectbox("COURSE", course_names)

    st.markdown(
        "<div class='api-note'>The app is using the selected course name to search the Golf Course API for tee boxes and hole yardages.</div>",
        unsafe_allow_html=True
    )

    api_matches = api_search_courses(selected_course)

    if not api_matches:
        st.warning("No API course match found yet. Try another course.")
        st.stop()

    api_match_labels = [get_course_display_name(course) for course in api_matches]

    selected_match_label = st.selectbox(
        "API COURSE MATCH",
        api_match_labels
    )

    selected_match_index = api_match_labels.index(selected_match_label)
    selected_match = api_matches[selected_match_index]

    course_id = selected_match.get("id")

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

    selected_tee_label = st.selectbox(
        "TEE",
        tee_labels
    )

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
        st.session_state.course = selected_course
        st.session_state.api_course = selected_match_label
        st.session_state.tee = selected_tee_label
        st.session_state.holes = holes
        st.session_state.hole_data = tee_holes[:holes]
        st.session_state.round_date = round_date

        st.session_state.screen = "scorecard"
        st.rerun()

# ---------------------------------------------------
# SCORECARD
# ---------------------------------------------------
elif st.session_state.screen == "scorecard":
    course = st.session_state.course
    tee = st.session_state.tee
    holes = st.session_state.holes
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
