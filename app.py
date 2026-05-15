import os
import requests
import pandas as pd
import streamlit as st

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Golf App",
    page_icon="⛳",
    layout="wide"
)

API_KEY = st.secrets.get("GOLF_COURSE_API_KEY", os.getenv("GOLF_COURSE_API_KEY", ""))

BASE_URL = "https://api.golfcourseapi.com/v1"

HEADERS = {
    "Authorization": f"Key {API_KEY}"
}

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

# =========================================================
# API HELPERS
# =========================================================

def api_get(endpoint, params=None):
    if not API_KEY:
        st.error("Missing Golf Course API key. Add GOLF_COURSE_API_KEY to Streamlit secrets.")
        st.stop()

    url = f"{BASE_URL}{endpoint}"

    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=20)

        if r.status_code != 200:
            st.error(f"API Error {r.status_code}: {r.text}")
            return None

        return r.json()

    except Exception as e:
        st.error(f"API request failed: {e}")
        return None


@st.cache_data(show_spinner=False)
def search_courses(query):
    """
    Searches Golf Course API.
    """
    data = api_get("/search", params={"search_query": query})

    if not data:
        return []

    if isinstance(data, dict):
        return data.get("courses", []) or data.get("data", []) or []

    if isinstance(data, list):
        return data

    return []


@st.cache_data(show_spinner=False)
def get_course_details(course_id):
    """
    Gets full course details, including tees and yardages.
    """
    data = api_get(f"/courses/{course_id}")

    if not data:
        return {}

    if isinstance(data, dict):
        return data.get("course", data)

    return {}


def normalize_course_name(course):
    return (
        course.get("course_name")
        or course.get("name")
        or course.get("club_name")
        or "Unknown Course"
    )


def normalize_location(course):
    location = course.get("location", {})

    if isinstance(location, dict):
        city = location.get("city", "")
        state = location.get("state", "")
        return f"{city}, {state}".strip(", ")

    return course.get("city", "")


def get_course_id(course):
    return course.get("id") or course.get("course_id")


def filter_courses_by_state(courses, state_abbrev):
    filtered = []

    for course in courses:
        location = course.get("location", {})

        state = ""
        if isinstance(location, dict):
            state = location.get("state", "")
        else:
            state = course.get("state", "")

        if state and state.upper() == state_abbrev.upper():
            filtered.append(course)

    return filtered


def extract_tees(course_details):
    tees = []

    raw_tees = (
        course_details.get("tees")
        or course_details.get("tee_boxes")
        or course_details.get("teeSets")
        or []
    )

    if isinstance(raw_tees, dict):
        for gender_group in raw_tees.values():
            if isinstance(gender_group, list):
                tees.extend(gender_group)
    elif isinstance(raw_tees, list):
        tees = raw_tees

    return tees


def tee_display_name(tee):
    name = (
        tee.get("tee_name")
        or tee.get("name")
        or tee.get("color")
        or "Tee"
    )

    yardage = (
        tee.get("total_yards")
        or tee.get("yardage")
        or tee.get("yards")
        or ""
    )

    rating = tee.get("course_rating") or tee.get("rating") or ""
    slope = tee.get("slope_rating") or tee.get("slope") or ""

    parts = [str(name)]

    if yardage:
        parts.append(f"{yardage} yards")
    if rating:
        parts.append(f"Rating {rating}")
    if slope:
        parts.append(f"Slope {slope}")

    return " | ".join(parts)


def extract_holes_from_tee(tee):
    holes = (
        tee.get("holes")
        or tee.get("yardages")
        or tee.get("scorecard")
        or []
    )

    rows = []

    if isinstance(holes, list):
        for i, hole in enumerate(holes, start=1):
            if isinstance(hole, dict):
                rows.append({
                    "Hole": hole.get("hole") or hole.get("number") or i,
                    "Par": hole.get("par", ""),
                    "Yards": hole.get("yards") or hole.get("yardage") or "",
                    "Handicap": hole.get("handicap") or hole.get("hcp") or ""
                })
            else:
                rows.append({
                    "Hole": i,
                    "Par": "",
                    "Yards": hole,
                    "Handicap": ""
                })

    return pd.DataFrame(rows)


# =========================================================
# UI
# =========================================================

st.title("⛳ Golf Course App")

st.markdown(
    """
    Search courses directly from the Golf Course API.  
    The old CSV course system has been removed.
    """
)

st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    selected_state_name = st.selectbox(
        "Select State",
        list(US_STATES.keys()),
        index=list(US_STATES.keys()).index("Kentucky")
    )

    selected_state = US_STATES[selected_state_name]

with col2:
    search_text = st.text_input(
        "Search Course Name",
        placeholder="Example: Lassing Pointe, Bethpage, Pebble Beach"
    )

if not search_text:
    st.info("Enter a course name to search.")
    st.stop()

with st.spinner("Searching Golf Course API..."):
    courses = search_courses(search_text)

if not courses:
    st.warning("No courses found from the API.")
    st.stop()

state_filtered_courses = filter_courses_by_state(courses, selected_state)

if state_filtered_courses:
    courses_to_show = state_filtered_courses
else:
    st.warning(
        f"No exact matches found in {selected_state_name}. Showing all API matches for this search."
    )
    courses_to_show = courses

course_options = {
    f"{normalize_course_name(c)} — {normalize_location(c)}": c
    for c in courses_to_show
}

selected_course_label = st.selectbox(
    "Select Course",
    list(course_options.keys())
)

selected_course = course_options[selected_course_label]
course_id = get_course_id(selected_course)

if not course_id:
    st.error("Selected course does not include a usable course ID.")
    st.stop()

with st.spinner("Loading tees and yardages..."):
    course_details = get_course_details(course_id)

st.divider()

st.subheader(normalize_course_name(course_details or selected_course))

location = normalize_location(course_details or selected_course)
if location:
    st.caption(location)

tees = extract_tees(course_details)

if not tees:
    st.warning("No tee or yardage information was returned for this course.")
    with st.expander("Raw API response"):
        st.json(course_details)
    st.stop()

tee_options = {
    tee_display_name(t): t
    for t in tees
}

selected_tee_label = st.selectbox(
    "Select Tee Box",
    list(tee_options.keys())
)

selected_tee = tee_options[selected_tee_label]

st.markdown("### Tee Information")

tee_summary = {
    "Tee": selected_tee.get("tee_name") or selected_tee.get("name") or selected_tee.get("color"),
    "Total Yards": selected_tee.get("total_yards") or selected_tee.get("yardage") or selected_tee.get("yards"),
    "Course Rating": selected_tee.get("course_rating") or selected_tee.get("rating"),
    "Slope Rating": selected_tee.get("slope_rating") or selected_tee.get("slope"),
}

st.dataframe(
    pd.DataFrame([tee_summary]).dropna(axis=1, how="all"),
    use_container_width=True,
    hide_index=True
)

holes_df = extract_holes_from_tee(selected_tee)

if not holes_df.empty:
    st.markdown("### Hole Yardages")
    st.dataframe(
        holes_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("This tee box did not include hole-by-hole yardages.")

with st.expander("Raw API course details"):
    st.json(course_details)
