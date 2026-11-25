from src.app.components import verdict, range_band, range_island, skills_island, skill_label

R = {"p10": 90_000.0, "p50": 120_000.0, "p90": 168_000.0, "bls_median": 120_000.0}


def test_verdict_bands():
    assert verdict(80_000, R)[0] == "Below the market range"
    assert verdict(110_000, R)[0] == "In range, below typical"
    assert verdict(130_000, R)[0] == "At or above typical"
    assert verdict(200_000, R)[0] == "Above the market range"
    assert verdict(120_000, R)[1] == "Right at the typical (P50) pay"


def test_range_band_marker_only_with_salary():
    assert "sa-you" in range_band(R, 110_000)
    assert "sa-you" not in range_band(R, None)


def test_range_island_escapes_user_text():
    html = range_island("<script>x</script>", "Boston, MA", R, None)
    assert "<script>" not in html and "Add your salary" in html


def test_skills_island():
    html = skills_island([("cpp", 4000.0), ("gcp", 2000.0)], 0, None)
    assert "C++" in html and "Google Cloud" in html and "No skills listed yet" in html
    assert "every skill we track" in skills_island([], 22, 2.0)
    assert skill_label("machine_learning") == "Machine learning"
