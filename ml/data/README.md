# SafeWork NLP dataset (SYNTHETIC)

**This data is synthetic.** Every complaint text was written by the project author and
expanded by a small script (`ml/make_dataset.py`). No real complaint, person, company or
case was used. There is no personal data in it.

## What "synthetic" means here
- The sentences are made-up examples of what a complaint might look like.
- Each category has 12 base sentences. Each base sentence is reused 5 times with a different
  opening and closing sentence, giving 60 texts per category (420 rows, perfectly balanced).
- Real complaints are longer, messier, mixed-language (Hindi/English), emotional and often
  fit more than one category. This data is cleaner and easier than real life.

## Columns (complaints_synthetic.csv)
| column | meaning |
|---|---|
| id | row number (S0001...) |
| text | the fake complaint text |
| category | label; names match backend/seed_categories.py exactly |
| core_id | which base sentence the row came from (e.g. VH03). Used to keep the same base sentence out of both train and test |

## Categories (7)
Verbal harassment, Sexual harassment, Physical harassment, Discrimination,
Bullying / abuse of power, Retaliation, Other.

## What the scores mean (and do not mean)
- Scores measured on this data show that the pipeline works and let us COMPARE methods.
- They do NOT predict how well the model would work on real complaints. Real accuracy
  would almost certainly be lower.
- The model only SUGGESTS categories for a human reviewer. It never decides truth or guilt.

## Known limitations
- Small (420 rows), English only, one writing style, templated openings and endings.
- Only 12 base sentences per category, so the test set is limited in variety.
- Categories are cleanly separated; real cases overlap (for example harassment followed by retaliation).
- "Other" holds ordinary workplace complaints that are not harassment.
- Labels were given by the author, not by trained Internal Committee members.

## How to rebuild
    cd ml
    python make_dataset.py
The random seed is fixed (42), so the same file is produced every time.