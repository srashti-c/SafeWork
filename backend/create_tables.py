from sqlalchemy import inspect

import app.models  # noqa: F401  (registers the models)
from app.core.database import Base, engine

Base.metadata.create_all(bind=engine)
print("Tables in database:", inspect(engine).get_table_names())