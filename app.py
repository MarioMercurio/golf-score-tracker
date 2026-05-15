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

US_STATES = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
    "New Mexico": "NM", "New York": "NY", "North Carolina": "NC",
    "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK", "Oregon": "OR",
    "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT",
    "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

CLUBS = [
    "DR", "3W", "5W", "HYB",
    "4I", "5I", "6I", "7I", "8I", "9I",
    "PW", "GW", "SW", "LW"
]

TEE_LOCATIONS = ["LOST LEFT", "LEFT", "CENTER", "RIGHT", "LOST RIGHT"]
TEE_QUALITIES = ["CRUSHED", "AVERAGE", "MIS-HIT"]

HAZARDS = ["OB", "GREEN BUNKER", "FAIRWAY BUNKER", "WATER", "DROP"]
GASHES = ["DUFF", "HERO SHOT", "MISREAD", "UNDER CLUB", "BAD TARGET AREA"]


def get_api_key():
    return st.secrets.get("GOLF_API_KEY", "") or st.secrets.get("GOLF_COURSE_API_KEY", "")


@st.cache_data(show_spinner=False)
def api_search_courses(search_query):
    api_key = get_api_key()
    if not api_key:
        return []

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/search",
            headers={"Authorization": f"Key {api_key}"},
            params={"search_query": search_query},
            timeout=20
        )

        if response.status_code != 200:
            return []

        data = response.json()
        return data.get("courses", []) if isinstance(data, dict) else []

    except Exception:
        return []


@st.cache_data(show_spinner=False)
def api_get_course_details(course_id):
    api_key = get_api_key()
    if not api_key:
        return {}

    try:
        response = requests.get(
            f"{API_BASE_URL}/v1/courses/{course_id}",
            headers={"Authorization": f"Key {api_key}"},
            timeout=20
        )

        if response.status_code != 200:
            return {}

        return response.json()

    except Exception:
        return {}


def get_course_display_name(course):
    name = course.get("course_name") or course.get("name") or course.get("club_name") or "Unknown Course"
    city = course.get("city", "")
    state = course.get("state", "")

    location = course.get("location", {})
    if isinstance(location, dict):
        city = city or location.get("city", "")
        state = state or location.get("state", "")

    if city and state:
        return f"{name} — {city}, {state}"
    if state:
        return f"{name} — {state}"
    return name


def get_course_state(course):
    state = course.get("state", "")
    location = course.get("location", {})
    if isinstance(location, dict):
        state = state or location.get("state", "")
    return str(state).upper().strip()


def filter_courses_by_state(courses, state_abbrev):
    return [c for c in courses if get_course_state(c) == state_abbrev.upper()]


def get_course_id(course):
    return course.get("id") or course.get("course_id")


def get_tee_options(course_details):
    tee_options = []
    course_data = course_details.get("course", course_details)
    tees = course_data.get("tees", {})

    if not isinstance(tees, dict):
        return tee_options

    for gender in ["male", "female"]:
        for tee in tees.get(gender, []):
            tee_name = tee.get("tee_name", "Unnamed Tee")
            total_yards = tee.get("total_yards", "")
            rating = tee.get("course_rating", "")
            slope = tee.get("slope_rating", "")

            parts = [tee_name]
            if total_yards:
                parts.append(f"{total_yards} yds")
            if rating:
                parts.append(f"Rating {rating}")
            if slope:
                parts.append(f"Slope {slope}")
            parts.append(gender.title())

            tee_options.append({
                "label": " • ".join(parts),
                "tee": tee
            })

    return tee_options


def get_holes_from_tee(tee):
    holes = tee.get("holes", [])
    clean_holes = []

    for index, hole in enumerate(holes, start=1):
        try:
            par = int(hole.get("par", 4))
        except Exception:
            par = 4

        try:
            yards = int(hole.get("yards") or hole.get("yardage") or 0)
        except Exception:
            yards = 0

        clean_holes.append({
            "hole": index,
            "par": par,
            "yards": yards,
            "handicap": hole.get("handicap") or hole.get("hcp") or ""
        })

    return clean_holes


def default_hole_entry(hole_info):
    return {
        "hole": hole_info["hole"],
        "par": hole_info["par"],
        "yards": hole_info["yards"],
        "handicap": hole_info["handicap"],
        "score": hole_info["par"],
        "putts": 2,
        "tee_club": "DR",
        "tee_location": "CENTER",
        "tee_quality": "AVERAGE",
        "inside_100_in_3": "NO",
        "hazards": {h: 0 for h in HAZARDS},
        "gashes": {g: 0 for g in GASHES},
    }


def init_round_entries():
    st.session_state.round_entries = {}

    for hole_info in st.session_state.hole_data:
        hole_num = hole_info["hole"]
        st.session_state.round_entries[hole_num] = default_hole_entry(hole_info)

    st.session_state.current_hole_index = 0


def set_value(hole_num, field, value):
    st.session_state.round_entries[hole_num][field] = value


def set_nested_value(hole_num, group, key, value):
    st.session_state.round_entries[hole_num][group][key] = value


st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {background-color: black;}

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
    height: 80px !important;
    font-size: 28px !important;
    font-weight: 900 !important;
    width: 100% !important;
}

label {
    color: white !important;
    font-weight: 800 !important;
    font-size: 18px !important;
}

input {
    color: white !important;
}

.api-note {
    color: #AAAAAA;
    text-align: center;
    font-size: 16px;
    margin-bottom: 20px;
}

.hole-header {
    background: #4DDB68;
    color: white;
    font-size: 58px;
    font-weight: 1000;
    text-align: center;
    padding: 18px;
    margin-bottom: 22px;
}

.hole-meta {
    color: white;
    font-size: 24px;
    font-weight: 900;
    line-height: 1.45;
}

.hole-meta span {
    color: red;
}

.big-label {
    color: white;
    font-size: 44px;
    font-weight: 1000;
}

.section-title {
    color: #4DDB68;
    font-size: 48px;
    font-weight: 1000;
    text-align: center;
    margin-top: 25px;
    margin-bottom: 15px;
}

.white-line {
    border-top: 5px solid white;
    margin: 30px 0 20px 0;
}

.choice-grid-title {
    color: yellow;
    text-align: center;
    font-weight: 900;
    font-size: 16px;
}

.small-note {
    color: red;
    text-align: center;
    font-size: 14px;
    font-weight: 900;
}

.summary-box {
    color: white;
    border: 2px solid #333;
    padding: 20px;
    font-size: 22px;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)


def autoplay_video(video_path):
    path = Path(video_path)
    if not path.exists():
        return

    encoded = base64.b64encode(path.read_bytes()).decode()

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

    round_date = st.date_input("DATE", value=date.today())

    selected_state_name = st.selectbox(
        "STATE",
        list(US_STATES.keys()),
        index=list(US_STATES.keys()).index("Kentucky")
    )

    selected_state = US_STATES[selected_state_name]

    search_query = st.text_input(
        "COURSE SEARCH",
        value="",
        placeholder="Type course name..."
    )

    st.markdown(
        "<div class='api-note'>Course search, tee boxes and hole yardages are powered only by the Golf Course API.</div>",
        unsafe_allow_html=True
    )

    if not get_api_key():
        st.error("Missing Golf API key. Add GOLF_API_KEY to Streamlit secrets.")
        st.stop()

    if not search_query.strip():
        st.info("Type a course name to search.")
        st.stop()

    api_matches = api_search_courses(search_query.strip())

    if not api_matches:
        st.warning("No API course matches found. Try a more specific course name.")
        st.stop()

    state_matches = filter_courses_by_state(api_matches, selected_state)
    courses_to_show = state_matches if state_matches else api_matches

    if not state_matches:
        st.warning(f"No exact matches found in {selected_state_name}. Showing all API matches.")

    api_match_labels = [get_course_display_name(course) for course in courses_to_show]
    selected_match_label = st.selectbox("COURSE", api_match_labels)

    selected_match = courses_to_show[api_match_labels.index(selected_match_label)]
    course_id = get_course_id(selected_match)

    if not course_id:
        st.warning("This API match does not include a course ID.")
        st.stop()

    course_details = api_get_course_details(course_id)

    if not course_details:
        st.warning("Could not load course details from API.")
        st.stop()

    tee_options = get_tee_options(course_details)

    if not tee_options:
        st.warning("Course loaded, but no tee boxes were found.")
        st.stop()

    tee_labels = [option["label"] for option in tee_options]
    selected_tee_label = st.selectbox("TEE", tee_labels)

    selected_tee = tee_options[tee_labels.index(selected_tee_label)]["tee"]
    tee_holes = get_holes_from_tee(selected_tee)

    if not tee_holes:
        st.warning("Tee selected, but no hole-by-hole yardage data was found.")
        st.stop()

    max_holes = len(tee_holes)
    holes = st.selectbox("HOLES", [9, 18], index=1) if max_holes >= 18 else st.selectbox("HOLES", [max_holes])

    if st.button("START ROUND"):
        clean_course_name = (
            selected_match.get("course_name")
            or selected_match.get("name")
            or selected_match.get("club_name")
            or selected_match_label
        )

        st.session_state.course = clean_course_name
        st.session_state.api_course = selected_match_label
        st.session_state.tee = selected_tee_label
        st.session_state.holes = holes
        st.session_state.hole_data = tee_holes[:holes]
        st.session_state.round_date = round_date

        init_round_entries()

        st.session_state.screen = "scorecard"
        st.rerun()


elif st.session_state.screen == "scorecard":
    if "round_entries" not in st.session_state:
        init_round_entries()

    hole_data = st.session_state.hole_data
    current_index = st.session_state.current_hole_index
    hole_info = hole_data[current_index]
    hole_num = hole_info["hole"]
    entry = st.session_state.round_entries[hole_num]

    top1, top2, top3 = st.columns([1, 2, 1])

    with top1:
        if st.button("◀ PREV") and current_index > 0:
            st.session_state.current_hole_index -= 1
            st.rerun()

    with top2:
        selected_hole = st.selectbox(
            "GO TO HOLE",
            [h["hole"] for h in hole_data],
            index=current_index
        )

        new_index = [h["hole"] for h in hole_data].index(selected_hole)
        if new_index != current_index:
            st.session_state.current_hole_index = new_index
            st.rerun()

    with top3:
        if st.button("NEXT ▶") and current_index < len(hole_data) - 1:
            st.session_state.current_hole_index += 1
            st.rerun()

    col1, col2 = st.columns([1.25, 1])

    with col1:
        st.markdown(f"<div class='hole-header'>HOLE {hole_num}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown(
            f"""
            <div class='hole-meta'>
            PAR: <span>{entry['par']}</span><br>
            YARDS: <span>{entry['yards']}</span><br>
            HANDICAP: <span>{entry['handicap']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    score_col, putt_col = st.columns(2)

    with score_col:
        st.markdown("<div class='big-label'>SCORE:</div>", unsafe_allow_html=True)
        score = st.number_input(
            " ",
            min_value=1,
            max_value=20,
            value=int(entry["score"]),
            step=1,
            key=f"score_{hole_num}"
        )
        set_value(hole_num, "score", score)

    with putt_col:
        st.markdown("<div class='big-label'>PUTTS:</div>", unsafe_allow_html=True)
        putts = st.number_input(
            "  ",
            min_value=0,
            max_value=10,
            value=int(entry["putts"]),
            step=1,
            key=f"putts_{hole_num}"
        )
        set_value(hole_num, "putts", putts)

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>TEE SHOT</div>", unsafe_allow_html=True)

    selected_club = st.selectbox(
        "CLUB",
        CLUBS,
        index=CLUBS.index(entry["tee_club"]) if entry["tee_club"] in CLUBS else 0,
        key=f"club_{hole_num}"
    )
    set_value(hole_num, "tee_club", selected_club)

    st.markdown("<div class='big-label' style='font-size:34px;'>LOCATION:</div>", unsafe_allow_html=True)

    loc_cols = st.columns(5)

    for i, location in enumerate(TEE_LOCATIONS):
        with loc_cols[i]:
            st.markdown(f"<div class='choice-grid-title'>{location}</div>", unsafe_allow_html=True)

            for quality in TEE_QUALITIES:
                selected = (
                    entry["tee_location"] == location
                    and entry["tee_quality"] == quality
                )

                label = f"{'✓ ' if selected else ''}{quality}"

                if st.button(label, key=f"tee_{hole_num}_{location}_{quality}"):
                    set_value(hole_num, "tee_location", location)
                    set_value(hole_num, "tee_quality", quality)
                    st.rerun()

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>PENALTIES / HAZARDS</div>", unsafe_allow_html=True)

    hazard_cols = st.columns(5)

    for i, hazard in enumerate(HAZARDS):
        with hazard_cols[i]:
            st.markdown(f"<div class='choice-grid-title'>{hazard}</div>", unsafe_allow_html=True)
            value = st.number_input(
                hazard,
                min_value=0,
                max_value=10,
                value=int(entry["hazards"][hazard]),
                step=1,
                key=f"hazard_{hole_num}_{hazard}",
                label_visibility="collapsed"
            )
            set_nested_value(hole_num, "hazards", hazard, value)
            st.markdown("<div class='small-note'>DEFAULT IS 0</div>", unsafe_allow_html=True)

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>SCORING ZONE</div>", unsafe_allow_html=True)

    inside_cols = st.columns(2)

    with inside_cols[0]:
        st.markdown(
            "<div class='big-label' style='font-size:32px;'>INSIDE 100 YARDS IN 3 SHOTS?</div>",
            unsafe_allow_html=True
        )

    with inside_cols[1]:
        yes_col, no_col = st.columns(2)

        with yes_col:
            if st.button(
                "YES" if entry["inside_100_in_3"] != "YES" else "✓ YES",
                key=f"inside_yes_{hole_num}"
            ):
                set_value(hole_num, "inside_100_in_3", "YES")
                st.rerun()

        with no_col:
            if st.button(
                "NO" if entry["inside_100_in_3"] != "NO" else "✓ NO",
                key=f"inside_no_{hole_num}"
            ):
                set_value(hole_num, "inside_100_in_3", "NO")
                st.rerun()

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>GASHES</div>", unsafe_allow_html=True)

    gash_cols = st.columns(5)

    for i, gash in enumerate(GASHES):
        with gash_cols[i]:
            st.markdown(f"<div class='choice-grid-title'>{gash}</div>", unsafe_allow_html=True)
            value = st.number_input(
                gash,
                min_value=0,
                max_value=10,
                value=int(entry["gashes"][gash]),
                step=1,
                key=f"gash_{hole_num}_{gash}",
                label_visibility="collapsed"
            )
            set_nested_value(hole_num, "gashes", gash, value)
            st.markdown("<div class='small-note'>DEFAULT IS 0</div>", unsafe_allow_html=True)

    st.markdown("<div class='white-line'></div>", unsafe_allow_html=True)

    nav1, nav2 = st.columns(2)

    with nav1:
        if st.button("BACK TO SETUP"):
            st.session_state.screen = "start_round"
            st.rerun()

    with nav2:
        if st.button("FINISH ROUND"):
            st.session_state.screen = "round_summary"
            st.rerun()


elif st.session_state.screen == "round_summary":
    st.markdown("<div class='start-title'>ROUND SUMMARY</div>", unsafe_allow_html=True)

    entries = st.session_state.round_entries

    total_score = sum(v["score"] for v in entries.values())
    total_par = sum(v["par"] for v in entries.values())
    total_putts = sum(v["putts"] for v in entries.values())

    relation = total_score - total_par
    relation_text = "E" if relation == 0 else f"+{relation}" if relation > 0 else str(relation)

    st.markdown(
        f"""
        <div class='summary-box'>
        COURSE: {st.session_state.course}<br>
        TEE: {st.session_state.tee}<br>
        SCORE: {total_score} ({relation_text})<br>
        PUTTS: {total_putts}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(entries)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("EDIT ROUND"):
            st.session_state.screen = "scorecard"
            st.rerun()

    with col2:
        if st.button("HOME"):
            st.session_state.screen = "home"
            st.rerun()
