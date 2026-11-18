"""Tiny raw files that mimic the real source formats, for an offline end-to-end run."""
import io
import zipfile
import pandas as pd


def write_fixtures(raw):
    raw.mkdir(parents=True, exist_ok=True)
    (raw / "linkedin").mkdir(exist_ok=True)

    oews = pd.DataFrame({
        # last row: May 2025 publishes real P90 values above the $239,200 cap with no '#'
        "AREA": ["41940", "41940", "14460", "14460", "41940", "14460"],
        "AREA_TITLE": ["San Jose-Sunnyvale-Santa Clara, CA"] * 2 + ["Boston-Cambridge-Newton, MA-NH"] * 2
                      + ["San Jose-Sunnyvale-Santa Clara, CA", "Boston-Cambridge-Newton, MA-NH"],
        "PRIM_STATE": ["CA", "CA", "MA", "MA", "CA", "MA"],
        "OCC_CODE": ["15-1252", "15-2051", "15-1252", "15-2051", "15-1221", "15-1243"],
        "A_PCT10": ["130000", "110000", "95000", "85000", "150000", "100000"],
        "A_MEDIAN": ["200000", "170000", "140000", "120000", "218420", "150000"],
        "A_PCT90": ["#", "#", "210000", "190000", "310190", "200000"],
    })
    # Real May 2025 zip: file_descriptions.xlsx and BOS (nonmetro) come before MSA in namelist order
    bos = pd.DataFrame({
        "AREA": ["0600001"], "AREA_TITLE": ["Eastern Sierra-Mother Lode Region of California nonmetropolitan area"],
        "PRIM_STATE": ["CA"], "OCC_CODE": ["15-1252"],
        "A_PCT10": ["70000"], "A_MEDIAN": ["100000"], "A_PCT90": ["150000"],
    })
    def xlsx(df):
        b = io.BytesIO(); df.to_excel(b, index=False); return b.getvalue()
    with zipfile.ZipFile(raw / "oesm25ma.zip", "w") as z:
        z.writestr("oesm25ma/", "")
        z.writestr("oesm25ma/BOS_M2025_dl.xlsx", xlsx(bos))
        z.writestr("oesm25ma/file_descriptions.xlsx",
                   xlsx(pd.DataFrame({"File name": ["MSA_M2025_dl.xlsx"], "File contents": ["MSA estimates"]})))
        z.writestr("oesm25ma/MSA_M2025_dl.xlsx", xlsx(oews))

    # Real May 2025 headers: "May 2025 Area Code", not "MSA code"
    pd.DataFrame({
        "FIPS Code": ["06", "25"], "State": ["California", "Massachusetts"], "State Abbreviation": ["CA", "MA"],
        "May 2025 Area Code": ["41940", "14460"],
        "May 2025 Area Title": ["San Jose-Sunnyvale-Santa Clara, CA", "Boston-Cambridge-Newton, MA-NH"],
        "County Code": ["085", "025"],
        "County Name": ["Santa Clara County", "Suffolk County"],
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
                   "15-2051.00\tData Scientists\tx\n41-2031.00\tRetail Salespersons\tx\n"
                   "15-1299.09\tInformation Technology Project Managers\tx\n"
                   "27-1024.00\tGraphic Designers\tx\n")
        z.writestr("db_31_0_text/Alternate Titles.txt",
                   "O*NET-SOC Code\tTitle\tAlternate Title\tShort Title\tSource(s)\n"
                   "15-1252.00\tSoftware Developers\tSoftware Engineer\t\t\n"
                   "15-2051.00\tData Scientists\tData Scientist\t\t\n"
                   "41-2031.00\tRetail Salespersons\tSales Associate\t\t\n"
                   "15-1299.09\tInformation Technology Project Managers\tProject Manager\t\t\n"
                   "27-1024.00\tGraphic Designers\tUX Designer\t\t\n")

    # Rows 0-1 early career; 2 non-tech; 3 mid-senior (kept, not early career); 4 missing level
    # (kept as "unknown"); 5 Director (dropped); 6 exact O*NET 15-1299 title via TF-IDF (dropped:
    # 15-1299 is rule-only); 7 designer title that would hit the front-end rule (excluded -> dropped)
    titles = ["Software Engineer, New Grad", "Data Scientist I", "Retail Sales Associate", "Software Engineer",
              "Data Engineer", "Director of Software Engineering", "Project Manager", "UX Designer, Front End"]
    n = len(titles)
    pd.DataFrame({
        "title": titles,
        "description": ["Python and SQL. 2+ years of experience required.", "PyTorch, Spark", "Retail", "Senior role",
                        "Spark and SQL", "Lead teams", "Plan projects", "Figma"],
        "company_name": ["Acme", "Delta Inc", "Shop", "Epsilon", "Zeta", "Eta", "Theta", "Iota"],
        "location": ["San Jose, CA", "Boston, MA", "Austin, TX", "San Jose, CA", "Boston, MA", "San Jose, CA",
                     "San Jose, CA", "San Jose, CA"],
        "normalized_salary": [140000.0, 125000.0, 40000.0, 300000.0, 150000.0, 400000.0, 120000.0, 110000.0],
        "currency": ["USD"] * n,
        "compensation_type": ["BASE_SALARY"] * n,
        "work_type": ["FULL_TIME"] * n,
        "formatted_experience_level": ["Entry level", "Associate", "Entry level", "Mid-Senior level", None,
                                       "Director", "Entry level", "Entry level"],
        "fips": [6085.0, 25025.0, 48453.0, 6085.0, 25025.0, 6085.0, 6085.0, 6085.0],
        "listed_time": [1.7e12, 1.71e12, 1.7e12, 1.7e12, 1.7e12, 1.7e12, 1.7e12, 1.7e12],
    }).to_csv(raw / "linkedin" / "postings.csv", index=False)
