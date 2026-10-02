# Graduation Questionnaire Insights – mock dashboard

Synthetic data + an executive-style 3-page web report.

- `generate_data.py` – builds the made-up dataset (seeded). Run `python3 generate_data.py` to regenerate `data.js` and `survey_data.csv`.
- `survey_data.csv` – long-format dataset: year × question × entity (Medical School A, National Benchmark, Campus 1–9), % favorable.
- `index.html` – the report (open directly in a browser; needs `data.js` beside it). Class-year toggle, clickable campus heatmap, domain drill-down.
- Export: **Download PDF** (browser print → 3 pages), **Download PPT** (editable native charts via `vendor-pptxgen.bundle.js`), **Dataset (CSV)**.

All numbers are fabricated for illustration. Mistreatment items are positively framed (higher = better).
