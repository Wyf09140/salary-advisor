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
    assert (lca.employer == "ACME").sum() == 4           # 'Acme, Inc.' / 'Acme' merged
    assert lca[lca.title == "Data Scientist"].annual_wage.iloc[0] == 65 * 2080
    assert lca.filter(like="skill_").isna().all().all()  # no skills for LCA
    assert len(post) == 2                                # retail + senior dropped
    assert post.metro.notna().all()                      # fips -> metro
    assert post.iloc[0].skill_python == 1 and post.iloc[0].years_exp == 2

    baseline = importlib.import_module("src.data.baseline")
    oews = pd.read_parquet(Path(os.environ["SA_PROCESSED"]) / "oews.parquet")
    pred = baseline.baseline_predictions(df, oews)
    assert pred["p50"].notna().all()
    for k in ("SA_RAW", "SA_PROCESSED"):
        del os.environ[k]
