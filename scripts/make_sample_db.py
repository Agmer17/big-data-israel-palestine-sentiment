"""Membuat database DuckDB SAMPEL (data sintetis) dengan skema identik dengan notebook.

Hanya untuk menjalankan/menguji backend tanpa file asli. JANGAN dipakai untuk analisis.
Pemakaian: python scripts/make_sample_db.py data/sample.duckdb
"""
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

import duckdb

DDL = """
CREATE TABLE agg_overall_sentiment (sentiment VARCHAR, n_comments BIGINT);
CREATE TABLE agg_daily_sentiment (comment_date DATE, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT);
CREATE TABLE agg_monthly_sentiment (month_start DATE, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT);
CREATE TABLE agg_subreddit_sentiment (subreddit VARCHAR, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT, sum_score BIGINT, n_score BIGINT, n_posts BIGINT);
CREATE TABLE agg_karma_sentiment (karma_category VARCHAR, category_order INTEGER, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT, sum_score BIGINT, n_score BIGINT, n_accounts BIGINT);
CREATE TABLE agg_account_weighted_sentiment (karma_category VARCHAR, category_order INTEGER, n_accounts BIGINT, sum_prop_positive DOUBLE, sum_prop_negative DOUBLE, sum_prop_neutral DOUBLE);
CREATE TABLE agg_account_age_sentiment (age_category VARCHAR, category_order INTEGER, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT, n_accounts BIGINT);
CREATE TABLE agg_verification_sentiment (verified_status VARCHAR, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT, n_accounts BIGINT);
CREATE TABLE agg_comment_score_sentiment (score_category VARCHAR, category_order INTEGER, sentiment VARCHAR, n_comments BIGINT, sum_score BIGINT, n_score BIGINT, sum_ups BIGINT, n_ups BIGINT, sum_downs BIGINT, n_downs BIGINT);
CREATE TABLE agg_controversiality_sentiment (controversiality INTEGER, sentiment VARCHAR, n_comments BIGINT, sum_score BIGINT, n_score BIGINT);
CREATE TABLE agg_post_comment_sentiment (post_id VARCHAR, subreddit VARCHAR, post_title VARCHAR, post_score BIGINT, post_upvote_ratio DOUBLE, post_created_time TIMESTAMP, n_total BIGINT, n_positive BIGINT, n_negative BIGINT, n_neutral BIGINT);
CREATE TABLE agg_keyword_sentiment (source_field VARCHAR, sentiment VARCHAR, keyword VARCHAR, n_occurrences BIGINT);
CREATE TABLE agg_association_stats (analysis VARCHAR, n_rows_compared BIGINT, n_comments BIGINT, chi2 DOUBLE, dof INTEGER, p_value DOUBLE, cramers_v DOUBLE);
"""


def split(n, rnd, w=(0.06, 0.64, 0.30)):
    p = max(0, round(n * (w[0] + rnd.uniform(-0.02, 0.02))))
    ng = max(0, round(n * (w[1] + rnd.uniform(-0.05, 0.05))))
    ng = min(ng, n - p)
    return p, ng, n - p - ng


def main(path: str) -> None:
    rnd = random.Random(42)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.unlink(missing_ok=True)
    con = duckdb.connect(str(p))
    con.execute(DDL)

    # daily + monthly
    d0, daily = date(2023, 9, 1), []
    for i in range(120):
        n = int(rnd.uniform(200, 3000) * (3 if 50 < i < 60 else 1))
        pos, neg, neu = split(n, rnd)
        daily.append((d0 + timedelta(days=i), n, pos, neg, neu))
    con.executemany("INSERT INTO agg_daily_sentiment VALUES (?,?,?,?,?)", daily)
    con.execute("""INSERT INTO agg_monthly_sentiment
        SELECT CAST(date_trunc('month', comment_date) AS DATE), SUM(n_total), SUM(n_positive), SUM(n_negative), SUM(n_neutral)
        FROM agg_daily_sentiment GROUP BY 1""")
    con.execute("""INSERT INTO agg_overall_sentiment
        SELECT 'positive', SUM(n_positive) FROM agg_daily_sentiment UNION ALL
        SELECT 'negative', SUM(n_negative) FROM agg_daily_sentiment UNION ALL
        SELECT 'neutral', SUM(n_neutral) FROM agg_daily_sentiment""")

    # subreddit
    names = ["IsraelPalestine", "worldnews", "NonCredibleDefense", "politics", "Palestine", "Israel",
             "IsrealPalestineWar_23", "conspiracy", "tinyviolin", "news"]
    for s in names:
        n = rnd.randint(50, 90000)
        pos, neg, neu = split(n, rnd)
        con.execute("INSERT INTO agg_subreddit_sentiment VALUES (?,?,?,?,?,?,?,?)",
                    [s, n, pos, neg, neu, rnd.randint(-500, 400000), n, max(1, n // 40)])

    # karma (kategori sesuai notebook)
    karma = [("Negative karma", 1), ("Zero karma", 2), ("Very low", 3), ("Low", 4), ("Moderate", 5),
             ("High", 6), ("Very high", 7), ("Unknown", 8)]
    for name, o in karma:
        n = rnd.randint(1000, 600000)
        pos, neg, neu = split(n, rnd)
        acc = max(1, n // 12)
        con.execute("INSERT INTO agg_karma_sentiment VALUES (?,?,?,?,?,?,?,?,?)",
                    [name, o, n, pos, neg, neu, rnd.randint(1000, 5000000), n, acc])
        a, b = rnd.uniform(0.04, 0.1), rnd.uniform(0.55, 0.65)
        con.execute("INSERT INTO agg_account_weighted_sentiment VALUES (?,?,?,?,?,?)",
                    [name, o, acc, a * acc, b * acc, (1 - a - b) * acc])

    # usia akun & verifikasi
    for name, o in [("Less than 30 days", 1), ("30-90 days", 2), ("91-365 days", 3), ("1-3 years", 4),
                    ("More than 3 years", 5), ("Unknown", 6)]:
        n = rnd.randint(1000, 900000)
        pos, neg, neu = split(n, rnd)
        con.execute("INSERT INTO agg_account_age_sentiment VALUES (?,?,?,?,?,?,?)", [name, o, n, pos, neg, neu, n // 10])
    for v, n in [("FALSE", 4_000_000), ("TRUE", 250_000), ("NULL", 20_000)]:
        pos, neg, neu = split(n, rnd)
        con.execute("INSERT INTO agg_verification_sentiment VALUES (?,?,?,?,?,?)", [v, n, pos, neg, neu, n // 9])

    # score & controversiality
    cats = [("Strongly negative", 1), ("Negative", 2), ("Zero", 3), ("Low", 4), ("Moderate", 5),
            ("High", 6), ("Very high", 7), ("Unknown", 8)]
    for name, o in cats:
        for s in ("positive", "negative", "neutral"):
            n = rnd.randint(100, 400000)
            con.execute("INSERT INTO agg_comment_score_sentiment VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [name, o, s, n, n * rnd.randint(-3, 60), n, n * rnd.randint(1, 70), n, n * rnd.randint(0, 3), n])
    for c in (0, 1):
        for s in ("positive", "negative", "neutral"):
            n = rnd.randint(1000, 2_000_000) if c == 0 else rnd.randint(100, 60000)
            con.execute("INSERT INTO agg_controversiality_sentiment VALUES (?,?,?,?,?)", [c, s, n, n * 20, n])

    # post (n_total log-uniform)
    for i in range(400):
        n = max(1, int(10 ** rnd.uniform(0, 2.79)))
        pos, neg, neu = split(n, rnd)
        con.execute("INSERT INTO agg_post_comment_sentiment VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [f"p{i:04d}", rnd.choice(names), f"Sample post title number {i} about the conflict", rnd.randint(1, 20000),
                     round(rnd.uniform(0.5, 0.99), 2), f"2023-1{rnd.randint(0, 2)}-{rnd.randint(10, 28)} 12:00:00", n, pos, neg, neu])

    # keyword
    words = ["israel", "hamas", "palestinians", "jews", "war", "people", "civilians", "genocide", "government",
             "ceasefire", "hostages", "trump", "muslim", "law", "aid", "children", "peace", "land", "idf", "biden"]
    words += [f"word{i}" for i in range(60)]
    for w in words:
        for s in ("positive", "negative", "neutral"):
            con.execute("INSERT INTO agg_keyword_sentiment VALUES ('comment',?,?,?)", [s, w, rnd.randint(5, 90000)])
    for f in ("post_title", "post_body"):
        for w in words:
            con.execute("INSERT INTO agg_keyword_sentiment VALUES (?,?,?,?)", [f, "n/a", w, rnd.randint(5, 4000)])

    # asosiasi (satu baris sengaja NaN/Infinity untuk menguji penanganan JSON)
    rows = [("Subreddit vs sentiment (>=100 komentar)", 90, 4_300_000, 52000.0, 178, 0.0, 0.106),
            ("Comment score category vs sentiment", 7, 4_300_000, 8000.0, 12, 0.0, 0.043),
            ("Karma category vs sentiment", 7, 4_200_000, 3600.0, 12, 0.0, 0.029),
            ("Account age vs sentiment", 5, 4_100_000, 1200.0, 8, math.nan, math.inf)]
    con.executemany("INSERT INTO agg_association_stats VALUES (?,?,?,?,?,?,?)", rows)
    con.close()
    print(f"Sampel database dibuat: {p}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/sample.duckdb")
