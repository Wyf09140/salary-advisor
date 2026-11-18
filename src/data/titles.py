"""Map free-text job titles to 2018 SOC codes using O*NET titles. Owner: Yifan.

TF-IDF character n-grams against every O*NET title (all occupations, so non-tech postings
map to non-tech SOCs and get filtered out), keeping the best match above a threshold.
"""
import re
import zipfile
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from src.config import RAW, SOURCES

_NOISE = re.compile(r"\b(sr|senior|jr|junior|lead|principal|staff|intern|i{1,3}|iv|\d+|remote|hybrid|"
                    r"new grad|entry level|associate|level)\b")


def norm_title(t) -> str:
    s = re.sub(r"[\(\[].*?[\)\]]", " ", str(t).lower())
    s = re.sub(r"[^a-z/+# ]", " ", s)
    return re.sub(r"\s+", " ", _NOISE.sub(" ", s)).strip()


def load_onet_titles() -> pd.DataFrame:
    rows = []
    with zipfile.ZipFile(RAW / SOURCES["onet"]["file"]) as z:
        for name in z.namelist():
            base = name.rsplit("/", 1)[-1]
            if not any(k in base for k in ("Occupation Data", "Alternate Titles", "Reported Title", "Job Titles")):
                continue
            df = pd.read_csv(z.open(name), sep="\t", dtype=str)
            code = next(c for c in df.columns if "SOC Code" in c)
            for c in df.columns:
                if "Title" in c and "Short" not in c:
                    rows.append(pd.DataFrame({"soc_code": df[code].str[:7], "onet_title": df[c]}))
    t = pd.concat(rows, ignore_index=True).dropna()
    t["norm"] = t["onet_title"].map(norm_title)
    return t[t["norm"] != ""].drop_duplicates(["soc_code", "norm"])


def match_titles(titles: pd.Series, onet: pd.DataFrame, min_score: float, chunk: int = 5000):
    """Return (soc_code, score) Series aligned with `titles`."""
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=1, sublinear_tf=True)
    ref = vec.fit_transform(onet["norm"])
    q_norm = titles.map(norm_title)
    uniq = q_norm.drop_duplicates()
    best_code, best_score = {}, {}
    codes = onet["soc_code"].to_numpy()
    for i in range(0, len(uniq), chunk):
        part = uniq.iloc[i:i + chunk]
        sims = vec.transform(part) @ ref.T
        idx = np.asarray(sims.argmax(axis=1)).ravel()
        val = np.asarray(sims.max(axis=1).todense()).ravel()
        for t, j, v in zip(part, idx, val):
            best_code[t], best_score[t] = codes[j], float(v)
    soc = q_norm.map(best_code)
    score = q_norm.map(best_score)
    return soc.where(score >= min_score), score
