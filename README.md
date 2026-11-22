# Ride-Sharing Operations Analysis

An end-to-end analysis of a synthetic ride-sharing dataset covering rides, drivers, users, payments and customer support. The project brings data preparation, Excel analysis, SQL queries and Power BI reporting guidance together in one reproducible submission.

## Project contents

| File | Purpose |
|---|---|
| [Ride_Sharing_Submission.xlsx](Ride_Sharing_Submission.xlsx) | Prepared tables, ride-level calculations, analysis summaries, exception checks and Excel findings. |
| [SQL_Analysis.sql](SQL_Analysis.sql) | 21 analytical queries and additional validation queries. Written for SQLite. |
| [ride_sharing.db](ride_sharing.db) | SQLite database containing the five source tables and summary tables. |
| [PowerBI_Implementation_Pack.md](PowerBI_Implementation_Pack.md) | Suggested data model, Power Query steps, DAX measures and report layout. |
| [Executive_Summary_and_Business_Questions.md](Executive_Summary_and_Business_Questions.md) | Findings, recommendations, answers to the business questions, assumptions and limitations. |
| [Ride_Sharing_Submission_Package.zip](Ride_Sharing_Submission_Package.zip) | The complete submission bundle. Download this file to get all project deliverables together. |
| [build_project.py](build_project.py) | Script used to prepare the workbook and SQLite database from the source workbook. |

GitHub does not display Excel workbooks or ZIP archives as formatted pages. Open the file and choose **Download raw file** (or use the package link above) to view them locally. The SQL and Markdown files can be read directly in the repository.

## Analysis scope

The workbook includes cleaned working tables while retaining the original source rows, derived ride measures, revenue and payment-method summaries, driver activity, rating distribution, promotional comparisons, support analysis and data-quality checks. The SQL file addresses the 21 assigned questions. The Power BI guide documents a proposed star-style model and report pages for operations, drivers, customer support, revenue and promotions.

The work is intended to support operational review rather than production decisions. For example, ride revenue is defined as fare plus tip; completion rate uses all recorded rides as the denominator; payment failure rate uses payment transactions as the denominator.

## Key results

- 4,690 of 5,200 rides are marked Completed (90.2%); 354 are Cancelled and 156 are No-show.
- Wallet has the highest observed payment failure rate (4.8%) among the four payment methods; Credit Card has the lowest (3.3%).
- 48.7% of ride ratings are below 3 out of 5.
- The Users table contains 1,200 rows but only 602 distinct UserIDs. Many repeated IDs have conflicting customer attributes, so user-level retention and referral analysis needs an identity-resolution rule.
- Ride dates span January 30 through July 31, 2025. Current-year and recent-30-day measures evaluated against the fixed analysis date of November 22, 2026 are not representative of current operations.

These figures come from a synthetic learning dataset. Unusually large fares, distances and durations are present; averages and city comparisons should be interpreted with that limitation in mind.

## Reproduce the files

The build script reads `RIDE_SHARING_DATA.xlsx` and writes the prepared Excel workbook and SQLite database to its current directory. Set the source workbook path near the top of `build_project.py` to match your machine before running it.

Required Python packages: `pandas`, `numpy`, `openpyxl` and `XlsxWriter`.

```bash
python -m pip install pandas numpy openpyxl XlsxWriter
python build_project.py
```

The SQL file can be run against `ride_sharing.db` using SQLite. The Power BI pack is an implementation guide; this repository does not contain a `.pbix` report file.

## Data handling notes

- Source records are retained; duplicate customer IDs are surfaced for review rather than removed without a rule.
- Rides, payments and support tickets have different row-level grains. Aggregate payment and ticket facts before combining them with rides to avoid multiplying ride totals.
- Promotion comparisons are observational and do not establish a causal effect.
- The database and workbook include synthetic practice data supplied for this project.
