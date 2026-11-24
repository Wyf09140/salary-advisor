from src.models.predict import predict, recommend
from src.models.evaluate import pinball, coverage
from src.app.resume_parser import extract_skills, extract_years
from src.data.clean import to_annual
import pandas as pd


def test_predict_contract():
    r = predict("Data Scientist", "San Jose, CA", ["python"], 1.0)
    assert set(r) == {"p10", "p50", "p90", "bls_median"}
    assert r["p10"] <= r["p50"] <= r["p90"]


def test_recommend_contract():
    out = recommend({"title": "SWE", "location": "Boston, MA", "skills": ["python"]}, top_k=3)
    assert len(out) == 3 and all(isinstance(s, str) for s, _ in out)


def test_parser():
    t = "3 years of experience with Python, SQL and Docker"
    assert {"python", "sql", "docker"} <= set(extract_skills(t))
    assert extract_years(t) == 3.0


def test_extract_years_ignores_unrelated_numbers():
    assert extract_years("Interned at a firm with 50 years of history") is None
    assert extract_years("5+ yrs professional Python experience; 2 years of experience in SQL") == 5.0
    assert extract_years("Built 3 dashboards") is None
    assert extract_years("") is None


def test_to_annual():
    out = to_annual(pd.Series([50, 100000]), pd.Series(["Hour", "Year"]))
    assert list(out) == [104000, 100000]


def test_metrics():
    assert pinball([1, 2], [1, 2], 0.5) == 0
    assert abs(coverage([1, 2, 3], 1, 2) - 2 / 3) < 1e-9
