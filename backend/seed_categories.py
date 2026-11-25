import app.models  # noqa: F401
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.category import Category

CATEGORIES = [
    ("Verbal harassment", "Insults, offensive remarks, abusive language"),
    ("Sexual harassment", "Unwelcome sexual behaviour, comments or advances"),
    ("Physical harassment", "Unwanted physical contact or intimidation"),
    ("Discrimination", "Unfair treatment based on gender, caste, religion, etc."),
    ("Bullying / abuse of power", "Repeated humiliation or misuse of authority"),
    ("Retaliation", "Adverse action after raising a concern"),
    ("Other", "Anything that does not fit the above"),
]

with SessionLocal() as db:
    added = 0
    for name, desc in CATEGORIES:
        if db.scalar(select(Category).where(Category.name == name)) is None:
            db.add(Category(name=name, description=desc))
            added += 1
    db.commit()
    print(f"categories added: {added}")