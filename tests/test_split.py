"""Checks for src/models/split.py (no data files needed)."""
import pandas as pd

from src.models.split import assign_folds, company_key


def _frame(n_companies=200):
    rows = []
    for i in range(n_companies):
        rows.append({"employer": f"ACMECO{i} SERVICES", "source": "lca", "split": "train"})
        rows.append({"employer": f"ACMECO{i} LABS", "source": "postings", "split": "train"})
    rows += [{"employer": "AMAZON WEB SERVICES", "source": "lca", "split": "shift"},
             {"employer": "AMAZON COM SERVICES", "source": "lca", "split": "train"}]
    return pd.DataFrame(rows)


def test_company_key_merges_entities_and_keeps_generic_names_apart():
    k = company_key(pd.Series(["AMAZON COM SERVICES", "AMAZON WEB SERVICES", "AMAZON",
                               "AMERICAN AIRLINES", "AMERICAN EXPRESS TRAVEL",
                               "BANK OF AMERICA N A", "BANK OF CHINA", "IT SOLUTIONS GROUP"]))
    assert k.iloc[0] == k.iloc[1] == k.iloc[2] == "AMAZON"
    assert k.iloc[3] != k.iloc[4]             # generic first word -> two tokens
    assert k.iloc[5] == "BANK AMERICA" and k.iloc[6] == "BANK CHINA"  # filler 'OF' dropped
    assert k.iloc[7] == "IT SOLUTIONS"         # short first token -> two tokens


def test_no_company_in_both_train_and_test():
    f = assign_folds(_frame())
    assert not set(f.company[f.fold == "train"]) & set(f.company[f.fold == "test"])
    assert {"train", "test"} <= set(f.fold)


def test_lca_and_postings_of_one_company_share_a_fold():
    df = _frame()
    f = assign_folds(df)
    nonshift = f[df.split != "shift"]
    assert (nonshift.groupby("company").fold.nunique() == 1).all()


def test_shift_rows_are_never_train_or_test():
    df = _frame()
    f = assign_folds(df)
    assert (f.fold[df.split == "shift"] == "shift").all()
    assert (f.fold[df.split != "shift"] != "shift").all()


def test_assignment_is_stable_under_reordering_and_subsetting():
    df = _frame()
    a = assign_folds(df)
    b = assign_folds(df.sample(frac=1, random_state=0))  # shuffled
    c = assign_folds(df.iloc[: len(df) // 2])            # fewer rows
    assert a.fold.equals(b.fold.loc[a.index])
    assert a.fold.loc[c.index].equals(c.fold)


def test_shift_seen_flags_companies_present_in_train_fold():
    df = _frame()
    f = assign_folds(df)
    amazon_in_train = (f.fold[df.employer == "AMAZON COM SERVICES"] == "train").all()
    shift_row = f[df.split == "shift"].iloc[0]
    assert shift_row.shift_seen == amazon_in_train


def test_test_share_is_roughly_respected():
    f = assign_folds(_frame(2000))
    share = (f.fold == "test").mean()
    assert 0.15 < share < 0.25
