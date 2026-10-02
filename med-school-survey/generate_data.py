"""Generate the SYNTHETIC graduation-questionnaire dataset used by the dashboard.

Every number is made up (seeded, so reproducible). Values are "% favorable"
(agree / strongly agree, or satisfied / very satisfied). Mistreatment items are
positively framed so that higher is always better.

Outputs: survey_data.csv (long format, for analysts) and data.js (loaded by index.html).
"""
import csv, json, random

random.seed(2026)
YEARS = [2024, 2025, 2026]
CAMPUSES = [f"Campus {i}" for i in range(1, 10)]

# (domain, [(question, national 2026 baseline %)])
QUESTIONS = {
    "Overall": [
        ("Overall satisfaction with the quality of your medical education", 83),
        ("Would choose this medical school again", 81),
        ("Feel prepared to begin residency", 85),
    ],
    "Curriculum": [
        ("Quality of pre-clinical basic science instruction", 80),
        ("Integration of basic science with clinical medicine", 76),
        ("Quality of teaching by faculty", 84),
        ("Fairness and transparency of assessments", 78),
        ("Support for Step 1 / Step 2 preparation", 74),
        ("Opportunities for research and scholarly activity", 77),
    ],
    "Clerkships": [
        ("Satisfaction with Internal Medicine clerkship", 86),
        ("Satisfaction with Surgery clerkship", 79),
        ("Satisfaction with Pediatrics clerkship", 88),
        ("Satisfaction with OBGYN clerkship", 82),
        ("Satisfaction with Psychiatry clerkship", 85),
        ("Satisfaction with Family Medicine clerkship", 87),
        ("Satisfaction with Neurology clerkship", 80),
        ("Satisfaction with Emergency Medicine clerkship", 87),
    ],
    "Admin Support": [
        ("Quality of academic advising", 75),
        ("Quality of residency / career advising", 77),
        ("Responsiveness of registrar and student records", 82),
        ("Accessibility of student affairs deans", 80),
        ("Availability of wellness and mental-health services", 73),
    ],
    "Mistreatment & Climate": [
        ("Learning environment free from mistreatment", 87),
        ("Confidence that mistreatment reports are handled fairly", 72),
        ("Comfort reporting mistreatment without fear of retaliation", 69),
        ("Faculty and residents model professional behavior", 84),
        ("Inclusive and respectful climate for all students", 83),
    ],
    "Facilities": [
        ("Library and study spaces", 84),
        ("Simulation and skills-lab facilities", 82),
        ("Technology and IT support", 79),
        ("Quality of clinical training sites", 81),
    ],
    "Financial Support": [
        ("Quality of financial-aid counseling", 74),
        ("Affordability of cost of attendance", 52),
        ("Availability of scholarships", 58),
        ("Education on debt management", 68),
    ],
}
DOMAINS = list(QUESTIONS)

# National drift by year (pts vs 2026 baseline)
NAT_DRIFT = {2024: 0.8, 2025: 0.4, 2026: 0.0}
NAT_DRIFT_DOMAIN = {"Financial Support": {2024: 2.0, 2025: 1.0, 2026: 0.0}}

# Medical School A offset vs national (pts) by domain and year -- the "story"
SCHOOL_OFFSET = {
    "Overall":                {2024: 3.0, 2025: 0.0, 2026: -3.0},
    "Curriculum":             {2024: 2.0, 2025: 3.0, 2026: 4.0},
    "Clerkships":             {2024: 1.0, 2025: 0.5, 2026: 0.0},
    "Admin Support":          {2024: -3.0, 2025: -1.0, 2026: 2.0},
    "Mistreatment & Climate": {2024: 1.0, 2025: -3.0, 2026: -7.0},
    "Facilities":             {2024: 5.0, 2025: 5.0, 2026: 4.0},
    "Financial Support":      {2024: -4.0, 2025: -5.0, 2026: -7.0},
}
# Question-specific story overrides (extra pts on top of the domain offset, 2026 value; scaled by year)
Q_STORY = {
    "Satisfaction with Surgery clerkship": -6,
    "Satisfaction with OBGYN clerkship": -4,
    "Satisfaction with Internal Medicine clerkship": 3,
    "Satisfaction with Family Medicine clerkship": 4,
    "Satisfaction with Pediatrics clerkship": 2,
    "Comfort reporting mistreatment without fear of retaliation": -5,
    "Affordability of cost of attendance": -3,
    "Support for Step 1 / Step 2 preparation": 3,
    "Simulation and skills-lab facilities": 4,
}
YEAR_SCALE = {2024: 0.2, 2025: 0.6, 2026: 1.0}

# Campus effects (pts) by domain; "*" applies to every domain
CAMPUS_EFFECT = {
    "Campus 1": {"*": 2},
    "Campus 2": {"*": 1},
    "Campus 3": {"Clerkships": -6, "Facilities": -5, "*": -1},
    "Campus 4": {"*": 0},
    "Campus 5": {"Mistreatment & Climate": -8, "Overall": -4, "*": -2},
    "Campus 6": {"*": 1},
    "Campus 7": {"*": 4, "Financial Support": 2},
    "Campus 8": {"Admin Support": -4, "*": -1},
    "Campus 9": {"Financial Support": -7, "Admin Support": -4, "*": -2},
}
# Extra deterioration at Campus 5 learning environment over time
CAMPUS_YEAR_EXTRA = {("Campus 5", "Mistreatment & Climate"): {2024: 0, 2025: -2, 2026: -5}}
BASE_N = {"Campus 1": 120, "Campus 2": 60, "Campus 3": 45, "Campus 4": 50, "Campus 5": 35,
          "Campus 6": 40, "Campus 7": 30, "Campus 8": 25, "Campus 9": 20}
N_YEAR = {2024: 0.93, 2025: 0.97, 2026: 1.0}

def campus_eff(c, d):
    e = CAMPUS_EFFECT[c]
    return e.get(d, e.get("*", 0))

qlist = [(d, q, b) for d, qs in QUESTIONS.items() for q, b in qs]
n = {(y, c): round(BASE_N[c] * N_YEAR[y] + random.uniform(-3, 3)) for y in YEARS for c in CAMPUSES}

# centre campus effects (weighted by n) so School A offsets stay as designed
centre = {}
for d in DOMAINS:
    for y in YEARS:
        tot = sum(n[(y, c)] for c in CAMPUSES)
        centre[(d, y)] = sum(n[(y, c)] * (campus_eff(c, d) + CAMPUS_YEAR_EXTRA.get((c, d), {}).get(y, 0))
                             for c in CAMPUSES) / tot

def clip(v): return max(35.0, min(98.5, v))

rows = []
values = {}
for y in YEARS:
    nat, camp = [], {c: [] for c in CAMPUSES}
    for d, q, base in qlist:
        drift = NAT_DRIFT[y] + NAT_DRIFT_DOMAIN.get(d, {}).get(y, 0)
        nv = clip(base + drift + random.gauss(0, 0.5))
        nat.append(round(nv, 1))
        for c in CAMPUSES:
            off = SCHOOL_OFFSET[d][y] + Q_STORY.get(q, 0) * YEAR_SCALE[y]
            ce = campus_eff(c, d) + CAMPUS_YEAR_EXTRA.get((c, d), {}).get(y, 0) - centre[(d, y)]
            camp[c].append(round(clip(nv + off + ce + random.gauss(0, 1.6)), 1))
    tot = sum(n[(y, c)] for c in CAMPUSES)
    school = [round(sum(camp[c][i] * n[(y, c)] for c in CAMPUSES) / tot, 1) for i in range(len(qlist))]
    values[y] = {"Medical School A": school, "National Benchmark": nat, **camp}

entities = ["Medical School A", "National Benchmark"] + CAMPUSES
with open("survey_data.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "domain", "question", "entity", "pct_favorable", "respondents"])
    for y in YEARS:
        for e in entities:
            for i, (d, q, _) in enumerate(qlist):
                resp = (sum(n[(y, c)] for c in CAMPUSES) if e == "Medical School A"
                        else "" if e == "National Benchmark" else n[(y, e)])
                w.writerow([y, d, q, e, values[y][e][i], resp])

payload = {
    "years": YEARS, "domains": DOMAINS, "campuses": CAMPUSES,
    "questions": [{"id": i, "domain": d, "text": q} for i, (d, q, _) in enumerate(qlist)],
    "respondents": {str(y): {c: n[(y, c)] for c in CAMPUSES} for y in YEARS},
    "values": {str(y): v for y, v in values.items()},
}
with open("data.js", "w") as f:
    f.write("// Synthetic data generated by generate_data.py\nwindow.SURVEY = " + json.dumps(payload) + ";\n")

# quick sanity summary
for y in YEARS:
    print(y, "n =", sum(n[(y, c)] for c in CAMPUSES))
    for d in DOMAINS:
        idx = [i for i, (dd, _, _) in enumerate(qlist) if dd == d]
        a = sum(values[y]["Medical School A"][i] for i in idx) / len(idx)
        b = sum(values[y]["National Benchmark"][i] for i in idx) / len(idx)
        print(f"  {d:24s} A {a:5.1f}  Nat {b:5.1f}  gap {a-b:+5.1f}")
