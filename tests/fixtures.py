"""Tiny raw files that mimic the real source formats, for an offline end-to-end run."""
import io
import zipfile
import pandas as pd


def write_fixtures(raw):
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "linkedin").mkdir(exist_ok=True)

    oews = pd.DataFrame({
        "AREA": ["41940", "41940", "14460", "14460"],
        "AREA_TITLE": ["San Jose-Sunnyvale-Santa Clara, CA"] * 2 + ["Boston-Cambridge-Newton, MA-NH"] * 2,
        "PRIM_STATE": ["CA", "CA", "MA", "MA"],
        "OCC_CODE": ["15-1252", "15-2051", "15-1252", "15-2051"],
        "A_PCT10": ["130000", "110000", "95000", "85000"],
        "A_MEDIAN": ["200000", "170000", "140000", "120000"],
        "A_PCT90": ["#", "#", "210000", "190000"],
    })
    buf = io.BytesIO(); oews.to_excel(buf, index=False)
    with zipfile.ZipFile(raw / "oesm25ma.zip", "w") as z:
        z.writestr("oesm25ma/MSA_M2025_dl.xlsx", buf.getvalue())

    pd.DataFrame({
        "FIPS code": ["06", "25"], "State abbreviation": ["CA", "MA"],
        "May 2025 MSA code": ["41940", "14460"],
        "May 2025 MSA name": ["San Jose-Sunnyvale-Santa Clara, CA", "Boston-Cambridge-Newton, MA-NH"],
        "County code": ["085", "025"],
        "County name (or Township name for the New England states)": ["Santa Clara County", "Suffolk County"],
    }).to_excel(raw / "area_definitions_m2025.xlsx", index=False)

    def lca(fy, wage):
        return pd.DataFrame({
            "CASE_STATUS": ["Certified", "Certified", "Certified", "Withdrawn", "Certified"],
            "VISA_CLASS": ["H-1B"] * 5,
            "FULL_TIME_POSITION": ["Y"] * 5,
            "JOB_TITLE": ["Software Engineer", "Data Scientist", "Software Engineer II", "Accountant", "SWE"],
            "SOC_CODE": ["15-1252.00", "15-2051.00", "15-1252.00", "13-2011.00", "15-1252.00"],
            "PW_WAGE_LEVEL": ["I", "II", "IV", "I", "I"],
            "WAGE_RATE_OF_PAY_FROM": [str(wage), "65", "250000", "70000", "100000"],
            "WAGE_UNIT_OF_PAY": ["Year", "Hour", "Year", "Year", "Year"],
            "WORKSITE_COUNTY": ["SANTA CLARA", "SUFFOLK", "SANTA CLARA", "SUFFOLK", "SANTA CLARA"],
            "WORKSITE_STATE": ["CA", "MA", "CA", "MA", "CA"],
            "EMPLOYER_NAME": ["Acme, Inc.", "Beta Corp", "Acme Inc", "Gamma LLC", "Acme"],
        })
    lca(2025, 150000).to_excel(raw / "LCA_Disclosure_Data_FY2025_Q1.xlsx", index=False)
    lca(2026, 180000).to_excel(raw / "LCA_Disclosure_Data_FY2026_Q1.xlsx", index=False)

    with zipfile.ZipFile(raw / "db_31_0_text.zip", "w") as z:
        z.writestr("db_31_0_text/Occupation Data.txt",
                   "O*NET-SOC Code\tTitle\tDescription\n15-1252.00\tSoftware Developers\tx\n"
                   "15-2051.00\tData Scientists\tx\n41-2031.00\tRetail Salespersons\tx\n")
        z.writestr("db_31_0_text/Alternate Titles.txt",
                   "O*NET-SOC Code\tTitle\tAlternate Title\tShort Title\tSource(s)\n"
                   "15-1252.00\tSoftware Developers\tSoftware Engineer\t\t\n"
                   "15-2051.00\tData Scientists\tData Scientist\t\t\n"
                   "41-2031.00\tRetail Salespersons\tSales Associate\t\t\n")

    pd.DataFrame({
        "title": ["Software Engineer, New Grad", "Data Scientist I", "Retail Sales Associate", "Software Engineer"],
        "description": ["Python and SQL. 2+ years of experience required.", "PyTorch, Spark", "Retail", "Senior role"],
        "company_name": ["Acme", "Delta Inc", "Shop", "Epsilon"],
        "location": ["San Jose, CA", "Boston, MA", "Austin, TX", "Remote, CA"],
        "normalized_salary": [140000.0, 125000.0, 40000.0, 300000.0],
        "currency": ["USD"] * 4,
        "compensation_type": ["BASE_SALARY"] * 4,
        "work_type": ["FULL_TIME"] * 4,
        "formatted_experience_level": ["Entry level", "Associate", "Entry level", "Mid-Senior level"],
        "fips": [6085.0, 25025.0, 48453.0, None],
        "listed_time": [1.7e12, 1.71e12, 1.7e12, 1.7e12],
    }).to_csv(raw / "linkedin" / "postings.csv", index=False)
