"""Shared settings and data split for all Phase 4 scripts."""
import os
import random

import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, "data", "complaints_synthetic.csv")
RESULTS_DIR = os.path.join(BASE, "results")
MODELS_DIR = os.path.join(BASE, "models")

SEED = 42
TEST_CORES_PER_CLASS = 3          # 3 of 12 base sentences per category go to the test set
EMBED_MODEL = "all-MiniLM-L6-v2"  # small sentence-transformer (384 numbers per text)

# Same names and order as backend/seed_categories.py
LABELS = [
    "Verbal harassment",
    "Sexual harassment",
    "Physical harassment",
    "Discrimination",
    "Bullying / abuse of power",
    "Retaliation",
    "Other",
]


def load_data():
    df = pd.read_csv(DATA_FILE)
    if set(df["category"]) != set(LABELS):
        raise SystemExit("CSV labels do not match LABELS in common.py")
    return df


def split_data(df):
    """Stratified, seeded split. Whole base sentences (core_id) go to train OR test,
    never both, so the test set holds sentences the model has not seen."""
    rng = random.Random(SEED)
    test_cores = []
    for label in LABELS:
        cores = sorted(df.loc[df["category"] == label, "core_id"].unique())
        test_cores += rng.sample(cores, TEST_CORES_PER_CLASS)
    is_test = df["core_id"].isin(test_cores)
    return df[~is_test].reset_index(drop=True), df[is_test].reset_index(drop=True)