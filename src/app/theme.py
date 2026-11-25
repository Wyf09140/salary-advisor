"""Floating-island visual theme for the Streamlit app. Owner: Sophak.

Results float as rounded white "islands" over a soft sky gradient. Every colour, radius and
shadow is a CSS variable below; components in app.py reference them instead of raw values.
Islands are keyed Streamlit containers: st.container(key="island-...") gets class .st-key-island-...
"""
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
  --sky-top: #DCEBFF;
  --sky-bottom: #F6F9FF;
  --ink: #10213A;
  --muted: #5B6B82;
  --line: #E3EAF5;
  --island: #FFFFFF;
  --accent: #2F6BFF;
  --accent-soft: #E6EEFF;
  --you: #FF6B4A;
  --bls: #8A97AB;
  --radius: 24px;
  --radius-sm: 999px;
  --shadow: 0 22px 44px -24px rgba(31, 72, 150, .35), 0 2px 6px rgba(31, 72, 150, .06);
  --font: 'Manrope', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

html, body, [class*="st-"], .stMarkdown, button, input, textarea {
  font-family: var(--font);
}

[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1200px 500px at 85% -10%, rgba(255, 255, 255, .9), transparent 60%),
    linear-gradient(180deg, var(--sky-top) 0%, var(--sky-bottom) 55%);
  color: var(--ink);
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }

/* ---------- islands ---------- */
[class*="st-key-island"] {
  background: var(--island);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 1.6rem 1.7rem 1.5rem;
  animation: rise .5s cubic-bezier(.2, .8, .2, 1) both;
}
.st-key-island-skills { animation-delay: .08s; }
.st-key-island-resume { animation-delay: .16s; }
@keyframes rise {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  [class*="st-key-island"] { animation: none; }
}

/* ---------- top bar ---------- */
.sa-bar { display: flex; align-items: center; gap: .7rem; margin: 0 0 1.6rem; }
.sa-logo {
  width: 34px; height: 34px; border-radius: 12px; display: grid; place-items: center;
  background: var(--ink); color: #fff; font-weight: 800; font-size: 15px;
}
.sa-name { font-weight: 800; font-size: 1.15rem; letter-spacing: -.01em; color: var(--ink); }
.sa-tag {
  margin-left: auto; font-size: .82rem; color: var(--muted); background: rgba(255, 255, 255, .7);
  padding: .35rem .8rem; border-radius: var(--radius-sm);
}

/* ---------- type ---------- */
.sa-eyebrow { font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); margin: 0 0 .35rem; }
.sa-h { font-weight: 800; font-size: 1.25rem; letter-spacing: -.01em; color: var(--ink); margin: 0 0 1rem; }
.sa-note { font-size: .85rem; color: var(--muted); margin: .9rem 0 0; line-height: 1.5; }
.sa-num { font-variant-numeric: tabular-nums; }

/* ---------- widgets ---------- */
[data-testid="stWidgetLabel"] p { font-weight: 600; color: var(--ink); font-size: .9rem; }
.stTextInput input, .stNumberInput input {
  border-radius: 14px; font-size: 16px;
}
.stButton > button[kind="primary"] {
  width: 100%; border-radius: var(--radius-sm); padding: .7rem 1rem; font-weight: 700;
  font-size: 1rem; border: 0; box-shadow: 0 10px 22px -12px rgba(47, 107, 255, .8);
  transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 14px 26px -12px rgba(47, 107, 255, .9); }
.stButton > button[kind="primary"]:active { transform: translateY(1px); }
[data-testid="stFileUploaderDropzone"] { border-radius: 16px; background: var(--accent-soft); }
"""


def apply() -> None:
    st.html(f"<style>{CSS}</style>")


def top_bar() -> None:
    st.html(
        '<div class="sa-bar"><div class="sa-logo">$</div>'
        '<div class="sa-name">Salary Advisor</div>'
        '<div class="sa-tag">Early-career software &amp; data roles</div></div>'
    )
