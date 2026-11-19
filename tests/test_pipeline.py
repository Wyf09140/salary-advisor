"""Offline end-to-end run of the data pipeline on fixture files."""
import importlib
import os
import sys
from pathlib import Path


def test_clean_end_to_end(tmp_path):
    os.environ["SA_RAW"] = str(tmp_path / "raw")
    os.environ["SA_PROCESSED"] = str(tmp_path / "processed")
    for m in [m for m in sys.modules if m.startswith("src")]:
        del sys.modules[m]
    from tests.fixtures import write_fixtures
    write_fixtures(Path(os.environ["SA_RAW"]))
    clean = importlib.import_module("src.data.clean")
    clean.main()

    import pandas as pd
    df = pd.read_parquet(Path(os.environ["SA_PROCESSED"]) / "train.parquet")
    lca = df[df.source == "lca"]
    post = df[df.source == "postings"]
    assert set(lca.wage_level) <= {"I", "II"}            # Level IV dropped
    assert "13-2011" not in set(df.soc_code)             # non-tech dropped
    assert set(lca.split) == {"train", "shift"}
    assert lca.metro.notna().all()                       # county name -> metro
    assert (lca.employer == "ACME").sum() == 3           # 'Acme, Inc.' / 'Acme' merged; 1 case deduped
    assert not ((lca.split == "train") & (lca.annual_wage == 150000)).any()  # withdrawn later -> dropped
    assert not (lca.annual_wage == 150000).any()          # and not re-added as shift
    assert lca[lca.title == "Data Scientist"].annual_wage.iloc[0] == 65 * 2080
    assert lca.filter(like="skill_").isna().all().all()  # no skills for LCA
    assert sorted(post.title) == ["Data Engineer", "Data Scientist I", "Software Engineer",
                                  "Software Engineer, New Grad"]  # retail, Director, 15-1299 TF-IDF, designer dropped
    assert set(post.wage_level) == {"entry", "associate", "mid-senior", "unknown"}
    assert post.set_index("title").early_career.to_dict() == {
        "Software Engineer, New Grad": True, "Data Scientist I": True,
        "Software Engineer": False, "Data Engineer": False}
    assert lca.early_career.all() and df.early_career.dtype == bool
    assert post.set_index("title").soc_code["Data Engineer"] == "15-1243"  # keyword rule
    assert post.metro.notna().all()                      # fips -> metro
    assert post.iloc[0].skill_python == 1 and post.iloc[0].years_exp == 2

    baseline = importlib.import_module("src.data.baseline")
    oews = pd.read_parquet(Path(os.environ["SA_PROCESSED"]) / "oews.parquet")
    assert {"41940", "14460", "600001"} <= set(oews.AREA)  # both MSA and BOS files loaded
    assert oews.P90_TOPCODED.sum() == 2                     # only the two '#' rows
    assert not oews[oews.OCC_CODE == "15-1221"].P90_TOPCODED.any()  # real 310,190 is not top-coded
    pred = baseline.baseline_predictions(df, oews)
    assert pred["p50"].notna().all()
    # prediction-time helpers
    geo = importlib.import_module("src.data.geo")
    assert geo.location_to_metro("San Jose, CA") == ("41940", "CA")
    assert geo.location_to_metro("Mountain View, CA") == ("41940", "CA")  # LCA worksite city table
    assert geo.location_to_metro("Cambridge, MA") == ("14460", "MA")      # OEWS principal-city fallback
    assert geo.location_to_metro("Nowhere, TX") == (None, "TX")           # caller falls back to state
    titles = importlib.import_module("src.data.titles")
    m = titles.TitleMatcher()
    assert m.soc("Software Engineer, New Grad") == "15-1252"
    assert m.soc("Data Scientist I") == "15-2051"
    assert m.soc("Project Manager") is None                              # 15-1299 rule-only
    assert m.soc("Retail Sales Associate") == "41-2031"                  # matched, but not a target SOC
    assert m.soc("Retail Sales Associate") not in importlib.import_module("src.config").SOC_CODES
    for k in ("SA_RAW", "SA_PROCESSED"):
        del os.environ[k]
