"""Makes the SYNTHETIC complaint dataset (fake text, written by us, no real people).

Run:  python make_dataset.py
Output: data/complaints_synthetic.csv  (columns: id, text, category, core_id)

Each category has 12 "core" sentences. Every core is reused 5 times with a
different opening sentence and closing sentence, so each category gets 60 rows.
"core_id" lets us keep the SAME core out of both train and test (no leakage).
"""
import csv
import os
import random

SEED = 42
ROWS_PER_CORE = 5
BASE = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE, "data", "complaints_synthetic.csv")
SEED_FILE = os.path.join(BASE, "..", "backend", "seed_categories.py")

# Names must match backend/seed_categories.py exactly.
CATEGORIES = {
    "Verbal harassment": ("VH", [
        "My team lead shouts at me and calls me stupid in front of everyone.",
        "A colleague keeps making insulting remarks about how I speak.",
        "He uses abusive language whenever a deadline is missed.",
        "I was called names and laughed at during the review call.",
        "A senior colleague mocks my accent and tells others to do the same.",
        "Some coworkers swear at me and say I am useless.",
        "My supervisor makes sarcastic, demeaning comments about my work every day.",
        "I get rude and offensive messages in the team chat group.",
        "Someone said I was only good for making tea and everyone laughed.",
        "He yells at me over small mistakes and uses offensive words.",
        "A coworker keeps passing hurtful jokes about my family.",
        "I was told to shut up and sit down in the meeting, in a very rude tone.",
    ]),
    "Sexual harassment": ("SH", [
        "A colleague keeps sending me suggestive messages even after I asked him to stop.",
        "My manager asked me to go out with him and kept asking after I said no.",
        "He makes comments about my body and my clothes.",
        "I received an inappropriate photo from a coworker on my phone.",
        "A senior person hinted that I would get a better project if I was friendly with him.",
        "Someone makes sexual jokes in front of me and says I should take it as a compliment.",
        "A coworker keeps staring at me and asking personal questions about my relationships.",
        "He sent late-night messages saying he wanted to meet me alone.",
        "I was asked intimate questions during a one-to-one meeting.",
        "A colleague told me to dress in a certain way to attract the clients, with a sexual remark.",
        "He keeps asking for my number and sending romantic messages although I am not interested.",
        "Someone made an unwelcome sexual advance at the office party.",
    ]),
    "Physical harassment": ("PH", [
        "A colleague grabbed my arm hard when I tried to leave the room.",
        "He stands too close and blocks the doorway so I cannot walk out.",
        "Someone keeps touching my shoulder and back although I move away.",
        "My supervisor threw a file at me during an argument.",
        "A coworker pushed me in the corridor and said it was an accident.",
        "He cornered me near the stairs and would not let me pass.",
        "A coworker slammed his fist on my desk and moved towards me in a threatening way.",
        "He hit the table and pointed his finger at my face to scare me.",
        "Someone blocked my chair and held my wrist during an argument.",
        "A colleague shoved me while passing and did it again the next day.",
        "He raised his hand as if to slap me when I disagreed with him.",
        "I was physically pulled away from my desk by a coworker.",
    ]),
    "Discrimination": ("DI", [
        "I was passed over for promotion because of my gender.",
        "My manager makes remarks about my caste and gives me the least important tasks.",
        "I was told that people from my religion do not fit our team culture.",
        "Women in my team are never given client-facing work.",
        "I was refused a transfer because I am married and might have children soon.",
        "My salary is lower than a male colleague who does the same job.",
        "I was excluded from the festival celebrations because of my religion.",
        "A coworker said people from my region are lazy, and the manager agreed.",
        "I was denied a leadership role because of my age.",
        "My disability is ignored and I am not given the support I asked for.",
        "I was not shortlisted for the training because of my community.",
        "Hiring for our department favours men and everyone knows it.",
    ]),
    "Bullying / abuse of power": ("BA", [
        "My boss gives me impossible deadlines to humiliate me in front of the team.",
        "My manager keeps taking credit for my work and says he can end my career with one email.",
        "I am made to do personal errands for my senior and cannot say no.",
        "My manager ignores me in meetings and shares my mistakes with the whole department.",
        "I am given extra work every weekend while others are left alone.",
        "A senior keeps reminding me that he controls my appraisal.",
        "My supervisor repeatedly humiliates new joiners to show who is in charge.",
        "I am isolated from the team and not told about important meetings.",
        "My manager changes my targets without notice and then blames me for missing them.",
        "He uses his position to make me stay late without pay.",
        "My boss publicly lists my errors every week and calls it feedback.",
        "I am being pushed to resign by being given pointless tasks all day.",
    ]),
    "Retaliation": ("RE", [
        "After I reported my supervisor, my shifts were cut.",
        "Since I raised a concern, I have been removed from my project.",
        "I was moved to a worse role right after I filed my complaint.",
        "My appraisal rating dropped suddenly after I spoke to HR.",
        "After I complained, colleagues were told not to talk to me.",
        "I was denied leave that was approved earlier, soon after I raised an issue.",
        "My contract was not renewed a week after I supported a coworker's complaint.",
        "I was given a warning letter for the first time right after I reported misconduct.",
        "My access to the team tools was removed after I made a complaint.",
        "I was transferred to another city after I asked the committee for help.",
        "My bonus was held back after I testified for a colleague.",
        "Ever since I spoke up, my manager has been looking for reasons to punish me.",
    ]),
    "Other": ("OT", [
        "My salary for last month has still not been paid.",
        "The air conditioning in our section has been broken for weeks.",
        "There is no clear policy on work-from-home days.",
        "The canteen food quality is poor and unsafe.",
        "My laptop is very old and slows down my work.",
        "The parking area is overcrowded and unsafe at night.",
        "I do not understand how my incentives are calculated.",
        "Two teams give me conflicting instructions about the same task.",
        "The washrooms on our floor are not cleaned properly.",
        "My leave balance shows the wrong number of days.",
        "The shift timings were changed without informing anyone in advance.",
        "I want to know how to apply for an internal job opening.",
    ]),
}

OPENERS = [
    "",
    "I want to put this on record.",
    "I am writing this complaint after thinking for a long time.",
    "This is about my workplace.",
    "Please look into this.",
    "I am not sure who else to tell.",
    "This has been going on for a while.",
    "For the record, I am writing in my own words.",
]
TAILS = [
    "",
    "Other colleagues were present.",
    "This is not the first time.",
    "It happened in the open office.",
    "I feel uncomfortable going to work now.",
    "I have not told anyone else yet.",
    "It happened again last week.",
    "I am worried about what will happen if I speak up.",
]


def check_names_against_seed_file():
    """Stop if a label is not in seed_categories.py (we never guess names)."""
    if not os.path.exists(SEED_FILE):
        print("WARNING: seed_categories.py not found, name check skipped")
        return
    with open(SEED_FILE, encoding="utf-8") as f:
        text = f.read()
    for name in CATEGORIES:
        if '("' + name + '"' not in text:
            raise SystemExit("Category not in seed_categories.py: " + name)
    print("Category names match seed_categories.py: OK")


def main():
    check_names_against_seed_file()
    rng = random.Random(SEED)
    pairs = [(o, t) for o in OPENERS for t in TAILS]
    rows = []
    for name, (code, cores) in CATEGORIES.items():
        for i, core in enumerate(cores, start=1):
            for opener, tail in rng.sample(pairs, ROWS_PER_CORE):
                text = " ".join(p for p in (opener, core, tail) if p)
                rows.append({"text": text, "category": name,
                             "core_id": code + format(i, "02d")})
    assert len(set(r["text"] for r in rows)) == len(rows), "duplicate texts"
    rng.shuffle(rows)
    for n, r in enumerate(rows, start=1):
        r["id"] = "S" + format(n, "04d")

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id", "text", "category", "core_id"])
        w.writeheader()
        w.writerows(rows)

    print("rows:", len(rows))
    for name in CATEGORIES:
        print("  ", name, "=", sum(1 for r in rows if r["category"] == name))
    print("saved:", OUT_FILE)


if __name__ == "__main__":
    main()