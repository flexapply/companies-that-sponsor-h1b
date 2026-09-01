#!/usr/bin/env python3
"""
Generate the README + forkable dataset for the public h1b-sponsors repo
from the FlexApply sponsor-data aggregate (out/companies.json).

Lazy by design: no live fetching. The DOL LCA file is browser-gated and only
updates quarterly, so this just reshapes data we already build for the site
into a GitHub-native dataset + README, with every company linking back to
flexapply.org. Run after each quarterly sponsor-data refresh.

    python3 generate.py
"""
import csv
import json
import datetime
from pathlib import Path

SITE = "https://flexapply.org"
SRC = Path.home() / "flexapply/tools/sponsor-data/out/companies.json"
SUMMARY = Path.home() / "flexapply/tools/sponsor-data/out/summary.json"
HERE = Path(__file__).parent
TOP_N = 100  # rows shown in the README table; full set goes to data/

FY = "FY2025"  # ponytail: single source, bump when sponsor-data moves to a new DOL year


def wage(v):
    return f"${v:,.0f}" if isinstance(v, (int, float)) and v else "n/a"


def first(items, key):
    return items[0][key] if items else ""


def main():
    companies = json.loads(SRC.read_text())
    companies.sort(key=lambda c: c.get("lcas", 0), reverse=True)
    summary = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    total = len(companies)
    positions = summary.get("rows_certified_h1b")
    today = datetime.date.today().isoformat()

    # --- full dataset: CSV + JSON (all companies) ---
    csv_path = HERE / "data" / f"h1b-sponsors-{FY.lower()}.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["company", "slug", "h1b_positions", "top_role",
                    "top_city", "states", "wage_median", "flexapply_url"])
        for c in companies:
            w.writerow([
                c["name"], c["slug"], c.get("lcas", 0),
                first(c.get("top_roles", []), "role"),
                first(c.get("top_cities", []), "city"),
                " ".join(c.get("states", [])),
                c.get("wage_median", ""),
                f'{SITE}/sponsors/company/{c["slug"]}/',
            ])
    (HERE / "data" / f"h1b-sponsors-{FY.lower()}.json").write_text(
        json.dumps(companies, indent=None, separators=(",", ":")))

    # --- README ---
    rows = []
    for i, c in enumerate(companies[:TOP_N], 1):
        rows.append(
            f'| {i} | [{c["name"]}]({SITE}/sponsors/company/{c["slug"]}/) '
            f'| {c.get("lcas", 0):,} | {first(c.get("top_roles", []), "role")} '
            f'| {first(c.get("top_cities", []), "city")} | {wage(c.get("wage_median"))} |'
        )
    table = "\n".join(rows)
    pos_line = f"{positions:,} certified H-1B positions" if positions else "certified H-1B positions"
    top5 = ", ".join(c["name"] for c in companies[:5])

    readme = f"""# Companies That Sponsor H-1B Visas ({FY[2:]} List)

A free, up-to-date list of companies that sponsor H-1B visas in the United States.
It covers {total:,} employers that filed certified H-1B (H1B) labor condition
applications in fiscal year 2025, {pos_line} in total, taken straight from official
U.S. Department of Labor data.

If you are an international student, an OPT or STEM OPT worker, or anyone job searching
and looking for visa sponsorship, this is a straight answer to "which companies sponsor
H-1B?" Most lists you find are several years old or mix in other countries. This one is
US only and is rebuilt each quarter from the newest DOL file.

Browse the full searchable version, with a page per company showing roles, cities, and
wage bands: **{SITE}/sponsors/companies/**

## Top {TOP_N} companies that sponsor H-1B visas, by volume

| # | Company | H-1B positions ({FY}) | Top role | Top location | Median wage |
|---|---------|----------------------|----------|--------------|-------------|
{table}

This is the top {TOP_N}. The full list of all {total:,} H-1B sponsoring companies is in
[`data/h1b-sponsors-{FY.lower()}.csv`](data/h1b-sponsors-{FY.lower()}.csv)
(and [`.json`](data/h1b-sponsors-{FY.lower()}.json)). Fork it, filter it, build on it.

## How to use this list

- Each company name links to its sponsorship detail (top roles, cities, and wages).
- Filter the CSV by state or role to find H-1B sponsors near you or in your field.
- New to the H-1B job search and not sure where to start? Free guide: {SITE}/free-guide/

## Frequently asked questions

### How do I know if a company sponsors H-1B visas?

The clearest public signal is whether the company has filed certified H-1B labor
condition applications with the Department of Labor. Every employer in this list has.
Past filings predict future sponsorship far better than a recruiter's verbal answer, so
check the data before you spend time applying.

### Which companies sponsor the most H-1B visas?

By {FY} filing volume the largest H-1B sponsors are {top5}, followed by the rest of the
top {TOP_N} in the table above.

### Do these companies sponsor H-1B for international students on OPT?

Many do. A company that regularly files H-1B is far more likely to move an OPT or STEM
OPT hire onto H-1B when the time comes. Use the filing counts here as a shortlist, then
confirm intent with the employer early in the process.

### Is this list free?

Yes. The data is public and the list is free to use, fork, and share.

## Related

- [H-1B Visa Sponsors by State](https://github.com/flexapply/h1b-sponsors-by-state):
  the same {FY} data grouped by state, with the top sponsoring employers in each one.

## About the data

Source: U.S. DOL LCA Disclosure Data {FY} Q4 (the full-year file). Counts are certified
H-1B labor condition applications, the standard public proxy for who sponsors. An LCA is
a step in the process, not a guarantee that a specific role is open today, so read the
counts as a signal of who sponsors and how much, not as a live job board.

Maintained by [FlexApply]({SITE}) and updated quarterly when DOL posts new data.
Last updated: {today}.

## License

The underlying data is public (U.S. Department of Labor). This dataset and its build
script are released under the MIT License. Attribution to FlexApply is appreciated.
"""
    (HERE / "README.md").write_text(readme)
    print(f"OK: README top {TOP_N}, full CSV/JSON = {total} companies, top: "
          f"{companies[0]['name']} ({companies[0].get('lcas')})")


if __name__ == "__main__":
    main()
