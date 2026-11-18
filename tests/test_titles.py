"""Keyword rules and exclusions in src/data/titles.py (no data files needed)."""
from src.data.titles import rule_soc


def test_rules_fix_common_titles():
    assert rule_soc("Data Analyst") == "15-2051"          # O*NET exact-title tie went to 19-3022
    assert rule_soc("Java Developer") == "15-1252"        # O*NET: 15-1251 (out of scope)
    assert rule_soc("Software Engineer, Back-End") == "15-1252"
    assert rule_soc("QA Automation Engineer") == "15-1253"
    assert rule_soc("Front End Developer") == "15-1254"
    assert rule_soc("Senior Data Engineer") == "15-1243"
    assert rule_soc("Database Administrator") == "15-1242"


def test_exclusions_and_no_match():
    assert rule_soc("UX Designer, Front End") is None     # designer excluded
    assert rule_soc("Web Designer") is None
    assert rule_soc("Business Developer") is None
    assert rule_soc("Technical Curriculum Developer") is None
    assert rule_soc("PLC Programmer") is None             # no bare 'programmer' rule
    assert rule_soc("Project Manager") is None            # falls to TF-IDF, where 15-1299 is rejected
