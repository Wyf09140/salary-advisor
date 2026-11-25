"""Streamlit front end. Owner: Sophak. Runs against the stub until models are trained."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.config import SKILLS
from src.models.predict import predict, recommend
from src.app.resume_parser import extract_text, extract_skills, extract_years
from src.app import theme
from src.app.components import empty_island, range_island, skills_island, skill_label

st.set_page_config(page_title="Salary Advisor", page_icon="$", layout="wide")
theme.apply()
theme.top_bar()


@st.cache_data(show_spinner=False)
def parse_resume(data: bytes, name: str) -> tuple[list[str], float | None]:
    text = extract_text(data, name)
    return extract_skills(text), extract_years(text)


left, right = st.columns([5, 7], gap="large")

with left:
    with st.container(key="island-inputs"):
        st.html('<p class="sa-eyebrow">Your profile</p><p class="sa-h">Is your pay on target?</p>')
        title = st.text_input("Job title", "Data Scientist")
        location = st.text_input("Location (city, state)", "San Jose, CA")
        current = st.number_input("Current or offered salary (USD/year)", 0, 1_000_000, 110_000, step=5_000)
        resume = st.file_uploader("Resume (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])

        found, found_years = [], None
        if resume:
            try:
                found, found_years = parse_resume(resume.getvalue(), resume.name)
                if not found and found_years is None:
                    st.html('<p class="sa-warn">We couldn\'t find skills in this file. If it\'s a scanned PDF, '
                            "try a DOCX or pick your skills below.</p>")
            except Exception:
                st.html('<p class="sa-warn">We couldn\'t read this file. Try another PDF, DOCX or TXT, '
                        "or pick your skills below.</p>")
        # Keyed by file name so the defaults refresh when a different resume is uploaded.
        rid = resume.name if resume else "none"
        skills = st.multiselect(
            "Your skills", list(SKILLS), default=found, format_func=skill_label, key=f"skills-{rid}",
            placeholder="Upload a resume or pick skills",
            help="Filled in from your resume. Add or remove skills the parser missed.",
        )
        years = st.number_input(
            "Years of experience", 0.0, 40.0, value=found_years, step=0.5, format="%.1f", key=f"years-{rid}",
            placeholder="Optional", help="Filled in when your resume states it, e.g. \"2 years of experience\".",
        )
        if st.button("Estimate my range", type="primary", width="stretch"):
            st.session_state.submitted = True

with right:
    missing = [name for name, v in (("job title", title), ("location", location)) if not v.strip()]
    if not st.session_state.get("submitted"):
        with st.container(key="island-empty"):
            st.html(empty_island("See your market range",
                                 "Enter a job title, location and salary, then select <b>Estimate my range</b>."))
    elif missing:
        with st.container(key="island-empty"):
            st.html(empty_island(f"Add a {' and '.join(missing)}",
                                 "The range depends on both the role and where it is."))
    else:
        profile = {"title": title, "location": location, "skills": skills, "years_exp": years}
        try:
            r = predict(title, location, skills, years)
            recs = recommend(profile)
        except Exception:
            with st.container(key="island-empty"):
                st.html(empty_island("We couldn't estimate this role",
                                     "Try a more common job title, such as \"Software Engineer\" or "
                                     "\"Data Analyst\", or a nearby large city."))
        else:
            with st.container(key="island-range"):
                st.html(range_island(title, location, r, current or None))
            with st.container(key="island-skills"):
                st.html(skills_island(recs, len(skills), years))
