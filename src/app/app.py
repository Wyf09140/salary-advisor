"""Streamlit front end. Owner: Sophak. Runs against the stub until models are trained."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.models.predict import predict, recommend
from src.app.resume_parser import extract_text, extract_skills, extract_years
from src.app import theme
from src.app.components import range_island

st.set_page_config(page_title="Salary Advisor", page_icon="$", layout="wide")
theme.apply()
theme.top_bar()

left, right = st.columns([5, 7], gap="large")

with left:
    with st.container(key="island-inputs"):
        st.html('<p class="sa-eyebrow">Your profile</p><p class="sa-h">Is your pay on target?</p>')
        title = st.text_input("Job title", "Data Scientist")
        location = st.text_input("Location (city, state)", "San Jose, CA")
        current = st.number_input("Current or offered salary (USD/year)", 0, 1_000_000, 110_000, step=5_000)
        resume = st.file_uploader("Resume (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])
        if st.button("Estimate my range", type="primary", width="stretch"):
            st.session_state.submitted = True

with right:
    if not st.session_state.get("submitted"):
        with st.container(key="island-empty"):
            st.html(
                '<div class="sa-empty"><p class="sa-h">See your market range</p><div class="sa-ghost"></div>'
                "<p>Enter a job title, location and salary, then select <b>Estimate my range</b>.</p></div>"
            )
    else:
        text = extract_text(resume.getvalue(), resume.name) if resume else ""
        skills = extract_skills(text)
        years = extract_years(text)
        r = predict(title, location, skills, years)

        with st.container(key="island-range"):
            st.html(range_island(title, location, r, current or None))

        with st.container(key="island-skills"):
            st.html('<p class="sa-eyebrow">Next steps</p><p class="sa-h">Skills linked to higher pay</p>')
            profile = {"title": title, "location": location, "skills": skills, "years_exp": years}
            for skill, delta in recommend(profile):
                st.write(f"- {skill}: +${delta:,.0f} predicted median")
