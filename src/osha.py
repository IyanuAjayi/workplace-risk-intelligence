"""Shared helpers for reading and standardising OSHA ITA Form 300A summary files."""
import re
import zipfile
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")

SECTORS = {"11": "Agriculture", "21": "Mining, oil and gas", "22": "Utilities", "23": "Construction",
           "31": "Manufacturing", "32": "Manufacturing", "33": "Manufacturing", "42": "Wholesale",
           "44": "Retail", "45": "Retail", "48": "Transport and warehousing", "49": "Transport and warehousing",
           "51": "Information", "52": "Finance and insurance", "53": "Real estate", "54": "Professional services",
           "55": "Management of companies", "56": "Admin, support and waste", "61": "Education",
           "62": "Health care and social assistance", "71": "Arts and recreation", "72": "Accommodation and food",
           "81": "Other services", "92": "Public administration"}

# Codes 21 and 22 replaced code 2 from the 2023 data onwards; collapse back so every year shares one scale
SIZE_BAND = {"1": "<20", "2": "20-249", "21": "20-249", "22": "20-249", "3": "250+"}


def raw_files():
    return sorted([p for p in RAW.iterdir() if p.suffix.lower() in (".csv", ".zip")], key=year_of)


def year_of(path):
    return int(re.findall(r"20[12]\d", path.name)[0])


def read_year(path):
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            with z.open(name) as f:
                df = pd.read_csv(f, low_memory=False, encoding="latin-1", dtype=str)
    else:
        df = pd.read_csv(path, low_memory=False, encoding="latin-1", dtype=str)
    df.columns = [c.replace("ï»¿", "").strip().lower() for c in df.columns]
    # 2019 stores IDs and NAICS codes as decimals ("272492.00"); strip the trailing zeros so years line up
    for col in ("establishment_id", "naics_code"):
        df[col] = df[col].str.strip().str.replace(r"\.0+$", "", regex=True)
    return df


def num(s):
    return pd.to_numeric(s, errors="coerce")


def link_key(df):
    """Backup link: normalised establishment name, 5-digit zip and 6-digit NAICS."""
    name = (df["establishment_name"].fillna("").str.upper().str.replace(r"[^A-Z0-9 ]", " ", regex=True)
            .str.replace(r"\b(INC|LLC|CORP|CORPORATION|CO|COMPANY|LTD|LP|THE)\b", "", regex=True).str.split().str.join(" "))
    return name + "|" + df["zip_code"].fillna("").str[:5] + "|" + df["naics_code"].fillna("")


def submitted_at(df):
    """Submission time across the formats OSHA has used ('3/22/2019 1:50:52', '26AUG22:17:41:44', '2/16/2026')."""
    raw = (df["created_timestamp"] if "created_timestamp" in df else df["date_submitted"]).fillna("")
    out = pd.to_datetime(raw, format="%m/%d/%Y %H:%M:%S", errors="coerce")
    for fmt in ("%d%b%y:%H:%M:%S", "%m/%d/%Y", "%m/%d/%Y %H:%M"):
        out = out.fillna(pd.to_datetime(raw, format=fmt, errors="coerce"))
    return out


def standardise(df, year):
    """One tidy frame per year with the fields the project uses. EIN and street address are left out on purpose."""
    hours = num(df["total_hours_worked"])
    dafw, djtr, other = num(df["total_dafw_cases"]), num(df["total_djtr_cases"]), num(df["total_other_cases"])
    out = pd.DataFrame({
        "year": year,
        "establishment_id": df["establishment_id"],
        "link_key": link_key(df),
        "establishment_name": df["establishment_name"],
        "company_name": df.get("company_name"),
        "state": df["state"].str.strip().str.upper(),
        "zip5": df["zip_code"].fillna("").str[:5],
        "naics6": df["naics_code"],
        "naics3": df["naics_code"].str[:3],
        "sector2": df["naics_code"].str[:2],
        "size_band": num(df["size"]).astype("Int64").astype(str).map(SIZE_BAND),
        "establishment_type": num(df["establishment_type"]),
        "employees": num(df["annual_average_employees"]),
        "hours": hours,
        "deaths": num(df["total_deaths"]),
        "dafw_cases": dafw, "djtr_cases": djtr, "other_cases": other,
        "dafw_days": num(df["total_dafw_days"]), "djtr_days": num(df["total_djtr_days"]),
        "submitted_at": submitted_at(df),
    })
    out["sector"] = out["sector2"].map(SECTORS).fillna("Unknown")
    out["dart_cases"] = dafw + djtr
    out["total_cases"] = dafw + djtr + other
    ok = hours > 0
    out["dart_rate"] = (out["dart_cases"] * 200_000 / hours).where(ok)
    out["tcr_rate"] = (out["total_cases"] * 200_000 / hours).where(ok)
    out["dafw_rate"] = (dafw * 200_000 / hours).where(ok)
    out["lost_days_rate"] = ((out["dafw_days"] + out["djtr_days"]) * 200_000 / hours).where(ok)
    out["hours_per_employee"] = hours / out["employees"].where(out["employees"] > 0)
    return out
