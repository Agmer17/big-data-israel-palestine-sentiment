import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def client(tmp_path_factory, monkeypatch_module):
    db_path = tmp_path_factory.mktemp("db") / "sample.duckdb"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "make_sample_db.py"), str(db_path)], check=True, cwd=ROOT)
    monkeypatch_module.setenv("DUCKDB_PATH", str(db_path))
    from app.core.config import get_settings
    get_settings.cache_clear()
    from app.main import create_app
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture(scope="module")
def monkeypatch_module():
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    yield mp
    mp.undo()


ENDPOINTS = [
    "/api/health", "/api/meta/tables",
    "/api/analytics/sentiment/overall", "/api/analytics/sentiment/overall/summary",
    "/api/analytics/sentiment/daily", "/api/analytics/sentiment/daily/top",
    "/api/analytics/sentiment/daily/top?metric=pct_negative",
    "/api/analytics/sentiment/monthly", "/api/analytics/sentiment/monthly/top",
    "/api/analytics/sentiment/monthly/top?metric=pct_positive&min_comments=0",
    "/api/analytics/subreddits", "/api/analytics/subreddits/top?metric=pct_negative",
    "/api/analytics/users/karma/sentiment", "/api/analytics/users/karma/weighted-comparison",
    "/api/analytics/users/account-age", "/api/analytics/users/verification",
    "/api/analytics/engagement/score-distribution", "/api/analytics/engagement/by-sentiment",
    "/api/analytics/engagement/score-category-sentiment", "/api/analytics/engagement/controversiality",
    "/api/analytics/engagement/controversiality/by-sentiment",
    "/api/analytics/posts", "/api/analytics/posts/top", "/api/analytics/posts/top?metric=balance",
    "/api/analytics/posts/top?metric=pct_negative", "/api/analytics/posts/comment-count-distribution",
    "/api/analytics/keywords/top", "/api/analytics/keywords/top?source_field=post_title",
    "/api/analytics/keywords/top?sentiment=negative",
    "/api/analytics/keywords/distinctive?sentiment=positive", "/api/analytics/keywords/distinctive?sentiment=negative",
    "/api/analytics/keywords/distinctive?sentiment=neutral",
    "/api/analytics/keywords/negative-vs-positive", "/api/analytics/keywords/negative-vs-positive?direction=positive",
    "/api/analytics/keywords/themes", "/api/analytics/keywords/themes/definitions",
    "/api/analytics/statistics/associations",
    "/api/analytics/statistics/contingency?variable=karma",
    "/api/analytics/statistics/contingency?variable=comment_score",
    "/api/analytics/statistics/contingency?variable=account_age",
    "/api/analytics/summary",
]


@pytest.mark.parametrize("url", ENDPOINTS)
def test_endpoint_ok_and_strict_json(client, url):
    r = client.get(url)
    assert r.status_code == 200, r.text
    # parse ketat: NaN/Infinity akan menolak
    body = json.loads(r.text, parse_constant=lambda c: (_ for _ in ()).throw(ValueError(c)))
    assert set(body) == {"data", "meta"}
    assert body["data"] not in (None, [], {}), url


def test_nan_inf_become_null(client):
    rows = client.get("/api/analytics/statistics/associations").json()["data"]
    bad = [x for x in rows if x["analysis"] == "Account age vs sentiment"][0]
    assert bad["p_value"] is None and bad["cramers_v"] is None


def test_pagination(client):
    b = client.get("/api/analytics/sentiment/daily?page=2&page_size=10").json()
    assert len(b["data"]) == 10
    assert b["meta"] == {"total": 120, "page": 2, "page_size": 10, "total_pages": 12}
    assert b["data"][0]["comment_date"] == "2023-09-11"  # ISO 8601


def test_daily_ma7_edges_null(client):
    d = client.get("/api/analytics/sentiment/daily?page_size=1000").json()["data"]
    assert d[0]["n_total_ma7"] is None and d[2]["n_total_ma7"] is None
    assert d[3]["n_total_ma7"] == pytest.approx(sum(x["n_total"] for x in d[0:7]) / 7)


def test_overall_percentages_sum_to_100(client):
    d = client.get("/api/analytics/sentiment/overall").json()["data"]
    assert sum(x["percentage"] for x in d) == pytest.approx(100)


def test_histogram_counts_all_posts(client):
    b = client.get("/api/analytics/posts/comment-count-distribution").json()
    assert sum(x["n_posts"] for x in b["data"]) == b["meta"]["n_posts"] == 400
    assert len(b["data"]) == 40


def test_validation_errors(client):
    for url in ["/api/analytics/sentiment/daily?page=0", "/api/analytics/subreddits?sort_by=nope",
                "/api/analytics/keywords/distinctive", "/api/analytics/sentiment/daily?start_date=2024-02-01&end_date=2024-01-01",
                "/api/analytics/keywords/top?source_field=post_title&sentiment=positive"]:
        r = client.get(url)
        assert r.status_code == 422, url
        assert "error" in r.json()


def test_404_and_readonly(client):
    assert client.get("/api/nope").status_code == 404
    with pytest.raises(Exception):
        client.app.state.db.cursor().execute("DELETE FROM agg_overall_sentiment")
