"""Employer-grouped train/test split. Owner: Pubudu.

- company_key(): collapse legal-entity variants of one company ("AMAZON COM SERVICES",
  "AMAZON WEB SERVICES", ...) into one key, so a company cannot sit in both train and test.
- assign_folds(): every row gets fold "train", "test" or "shift".
  * split == "shift" (FY2026 LCA) -> "shift", never trained on.
  * Otherwise a company goes to "test" iff a stable hash of its key falls in the test share.
    One decision per company across BOTH sources, so an employer's LCA rows and postings rows
    always land in the same fold.

Why a hash and not GroupShuffleSplit: same guarantee (whole groups held out), but the
assignment of a company never changes when rows are added, removed or reordered, so results
stay comparable if Yifan regenerates train.parquet. Python's built-in hash() is salted per
process, so we use md5.

`python -m src.models.split` prints the split report (row shares, largest company, postings
test size, shift rows from companies seen in training).
"""
import hashlib

import pandas as pd

TEST_SHARE = 0.20
SEED = "salary-advisor-2026"

# Words too generic to identify a company on their own ("AMERICAN AIRLINES" vs "AMERICAN EXPRESS").
# For these the key uses the first two tokens. Chosen by eye from the most common first tokens in
# train.parquet. Leftover over-merging only makes the split stricter, never leaks.
GENERIC_FIRST = {
    "ADVANCED", "AMERICAN", "APEX", "APPLIED", "ATLANTIC", "BANK", "BLUE", "BOARD", "CALIFORNIA",
    "CAPITAL", "CENTRAL", "CHILDRENS", "CITY", "CLOUD", "COMMUNITY", "COUNTY", "DATA", "DEPARTMENT",
    "DIGITAL", "EAST", "FIRST", "GENERAL", "GLOBAL", "GREAT", "HEALTH", "INFO", "INNOVATIVE",
    "INTEGRATED", "INTERNATIONAL", "MEDICAL", "NATIONAL", "NEW", "NORTH", "NORTHERN", "PACIFIC",
    "PRIME", "RED", "SAN", "SMART", "SOFTWARE", "SOUTH", "SOUTHERN", "STATE", "SYSTEMS", "TECH",
    "TEXAS", "UNITED", "UNIVERSAL", "UNIVERSITY", "WEST",
}
FILLER = {"THE", "OF", "AND", "FOR", "AT"}


def _key(name: str) -> str:
    tokens = [t for t in str(name).upper().split() if t not in FILLER]
    if not tokens:
        return str(name).upper().strip()
    first = tokens[0]
    if first in GENERIC_FIRST or len(first) <= 2:  # "IT", "AI", "US", initials
        return " ".join(tokens[:2])
    return first


def company_key(employer: pd.Series) -> pd.Series:
    """Normalized employer -> company key (e.g. all AMAZON * entities -> 'AMAZON')."""
    uniq = pd.Series(employer.unique())
    mapping = dict(zip(uniq, uniq.map(_key)))
    return employer.map(mapping)


def _in_test(key: str, test_share: float, seed: str) -> bool:
    h = int(hashlib.md5(f"{seed}|{key}".encode()).hexdigest()[:8], 16)
    return h / 0xFFFFFFFF < test_share


def assign_folds(df: pd.DataFrame, test_share: float = TEST_SHARE, seed: str = SEED) -> pd.DataFrame:
    """Return DataFrame[company, fold, shift_seen] indexed like df.

    shift_seen is True for shift rows whose company has rows in the train fold; report shift
    metrics on all shift rows and on shift_seen == False (unseen companies) separately.
    """
    company = company_key(df["employer"])
    test_keys = {k for k in company.unique() if _in_test(k, test_share, seed)}
    fold = pd.Series("train", index=df.index)
    fold[company.isin(test_keys)] = "test"
    fold[df["split"] == "shift"] = "shift"
    train_companies = set(company[fold == "train"])
    shift_seen = (fold == "shift") & company.isin(train_companies)
    return pd.DataFrame({"company": company, "fold": fold, "shift_seen": shift_seen})


def split_report(df: pd.DataFrame, folds: pd.DataFrame) -> str:
    """Human-readable checks on a split (Stage 1 rows expected)."""
    d = df.join(folds)
    lines = []
    tab = d.groupby(["source", "fold"]).size().unstack(fill_value=0)
    lines.append("Rows by source and fold:\n" + tab.to_markdown())
    nonshift = d[d.fold != "shift"]
    for src, g in nonshift.groupby("source"):
        lines.append(f"{src}: test share of rows = {(g.fold == 'test').mean():.3f}, "
                     f"companies train/test = {g[g.fold == 'train'].company.nunique()}/"
                     f"{g[g.fold == 'test'].company.nunique()}")
    top = nonshift.company.value_counts(normalize=True).head(5)
    lines.append("Largest companies (share of non-shift rows, fold):\n" + "\n".join(
        f"  {k:30s} {v:.3f}  {nonshift.loc[nonshift.company == k, 'fold'].iloc[0]}"
        for k, v in top.items()))
    overlap = set(d[d.fold == "train"].company) & set(d[d.fold == "test"].company)
    lines.append(f"Companies in both train and test: {len(overlap)}")
    sh = d[d.fold == "shift"]
    if len(sh):
        lines.append(f"Shift rows from companies seen in train: {sh.shift_seen.mean():.3f} "
                     f"(unseen-company shift rows: {(~sh.shift_seen).sum():,})")
    return "\n\n".join(lines)


def main() -> None:
    from src.config import PROCESSED
    df = pd.read_parquet(PROCESSED / "train.parquet")
    df = df[df["early_career"]]
    print(f"employers: {df.employer.nunique():,} -> companies: {company_key(df.employer).nunique():,}\n")
    print(split_report(df, assign_folds(df)))


if __name__ == "__main__":
    main()
