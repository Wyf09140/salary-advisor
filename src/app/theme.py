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

/* Not [class*="st-"]: that also hits Material icon spans and prints their ligature names. */
html, body, .stApp, .stMarkdown, p, label, button, input, textarea, [data-baseweb="select"] {
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

/* ---------- range island ---------- */
.sa-hero { display: flex; flex-direction: column; gap: 1rem; }
.sa-big { font-size: clamp(2.4rem, 5vw, 3.4rem); font-weight: 800; letter-spacing: -.03em; line-height: 1; color: var(--ink); }
.sa-sub { margin-top: .45rem; color: var(--muted); font-size: .95rem; }
.sa-sub b { color: var(--ink); font-weight: 700; }
.sa-verdict {
  align-self: flex-start; display: flex; align-items: center; flex-wrap: wrap; gap: .3rem .6rem;
  background: #FFF1EC; padding: .45rem .9rem; border-radius: var(--radius-sm);
}
.sa-verdict b { color: #D9472A; font-size: .92rem; }
.sa-verdict span { color: var(--ink); font-size: .88rem; }

.sa-band-wrap { margin-top: 3.4rem; }
.sa-track { position: relative; height: 14px; border-radius: var(--radius-sm); background: var(--accent-soft); }
.sa-band {
  position: absolute; top: 0; bottom: 0; border-radius: var(--radius-sm);
  background: linear-gradient(90deg, #8FB2FF, var(--accent) 50%, #8FB2FF);
}
.sa-p50 { position: absolute; top: -5px; bottom: -5px; width: 4px; margin-left: -2px; border-radius: 2px; background: var(--ink); }
.sa-bls { position: absolute; top: -10px; bottom: -10px; margin-left: -1px; border-left: 2px dashed var(--bls); }
.sa-you { position: absolute; bottom: 7px; display: flex; flex-direction: column; align-items: center; transform: translateX(-50%); }
.sa-you-left { transform: translateX(-18px); align-items: flex-start; }
.sa-you-right { transform: translateX(calc(-100% + 18px)); align-items: flex-end; }
.sa-you-pill {
  background: var(--you); color: #fff; font-weight: 700; font-size: .82rem; white-space: nowrap;
  padding: .3rem .7rem; border-radius: var(--radius-sm); box-shadow: 0 8px 18px -8px rgba(255, 107, 74, .9);
}
.sa-you-left .sa-you-stem, .sa-you-left .sa-you-dot { margin-left: 12px; }
.sa-you-right .sa-you-stem, .sa-you-right .sa-you-dot { margin-right: 12px; }
.sa-you-stem { width: 2px; height: 12px; background: var(--you); }
.sa-you-dot { width: 14px; height: 14px; border-radius: 50%; background: #fff; border: 4px solid var(--you); margin-bottom: -14px; }

.sa-ticks { position: relative; height: 44px; margin-top: .7rem; }
.sa-tick { position: absolute; transform: translateX(-50%); text-align: center; display: flex; flex-direction: column; white-space: nowrap; }
.sa-tick b { font-size: .95rem; color: var(--ink); }
.sa-tick span { font-size: .75rem; color: var(--muted); }
.sa-legend { display: flex; align-items: center; gap: .5rem; font-size: .82rem; color: var(--muted); margin-top: .6rem; }
.sa-legend-bls { width: 18px; border-top: 2px dashed var(--bls); }

/* ---------- empty state ---------- */
.sa-empty { text-align: center; padding: 1.4rem .5rem .6rem; }
.sa-empty .sa-ghost { height: 14px; border-radius: var(--radius-sm); margin: 1.6rem auto 1.4rem; max-width: 420px;
  background: linear-gradient(90deg, var(--accent-soft) 0 18%, #C9D9FF 18% 82%, var(--accent-soft) 82%); }
.sa-empty p { color: var(--muted); margin: 0; }

/* ---------- widgets ---------- */
[data-testid="stWidgetLabel"] p { font-weight: 600; color: var(--ink); font-size: .9rem; }
.stTextInput input, .stNumberInput input {
  border-radius: 14px; font-size: 16px;
}
.stButton > button[data-testid="stBaseButton-primary"] {
  border-radius: var(--radius-sm); padding: .75rem 1rem; min-height: 48px;
  border: 0; box-shadow: 0 10px 22px -12px rgba(47, 107, 255, .8);
  transition: transform .15s ease, box-shadow .15s ease;
}
.stButton > button[data-testid="stBaseButton-primary"] p { font-weight: 700; font-size: 1rem; }
.stButton > button[data-testid="stBaseButton-primary"]:hover { transform: translateY(-1px); box-shadow: 0 14px 26px -12px rgba(47, 107, 255, .9); }
.stButton > button[data-testid="stBaseButton-primary"]:active { transform: translateY(1px); }
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
