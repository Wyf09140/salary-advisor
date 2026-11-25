"""Streamlit front end. Owner: Sophak. Runs against the stub until models are trained."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

import streamlit as st
from src.models.predict import predict, recommend
from src.app.resume_parser import extract_text, extract_skills, extract_years
from src.app import theme

st.set_page_config(page_title="Salary Advisor", layout="centered")
theme.apply()
theme.top_bar()

title = st.text_input("Job title", "Data Scientist")
location = st.text_input("Location (city, state)", "San Jose, CA")
current = st.number_input("Current or offered salary (USD/year)", 0, 1_000_000, 110_000, step=5_000)
resume = st.file_uploader("Resume (PDF, DOCX or TXT)", type=["pdf", "docx", "txt"])

if st.button("Estimate my range"):
    text = extract_text(resume.getvalue(), resume.name) if resume else ""
    skills = extract_skills(text)
    years = extract_years(text)
    r = predict(title, location, skills, years)

    c1, c2, c3 = st.columns(3)
    c1.metric("Low (P10)", f"${r['p10']:,.0f}")
    c2.metric("Typical (P50)", f"${r['p50']:,.0f}")
    c3.metric("High (P90)", f"${r['p90']:,.0f}")
    st.write(f"BLS median for this occupation and area: ${r['bls_median']:,.0f}")

    span = max(r["p90"] - r["p10"], 1)
    pos = min(max((current - r["p10"]) / span, 0.0), 1.0)
    st.progress(pos, text=f"Your pay sits at {pos:.0%} of the P10 to P90 range")

    st.subheader("Skills linked to higher pay in similar roles")
    st.caption("Associations in the data, not guaranteed raises.")
    profile = {"title": title, "location": location, "skills": skills, "years_exp": years}
    for skill, delta in recommend(profile):
        st.write(f"- {skill}: +${delta:,.0f} predicted median")
    with st.expander("Skills found in your resume"):
        st.write(", ".join(skills) or "None detected")
