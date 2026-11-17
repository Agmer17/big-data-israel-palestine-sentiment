"""Konstanta yang mengikuti definisi di notebook."""

# Tabel agregasi yang dibuat notebook di AGREGATION_ANALYSYS_TABLE.duckdb
REQUIRED_TABLES: tuple[str, ...] = (
    "agg_overall_sentiment",
    "agg_daily_sentiment",
    "agg_monthly_sentiment",
    "agg_subreddit_sentiment",
    "agg_karma_sentiment",
    "agg_account_weighted_sentiment",
    "agg_account_age_sentiment",
    "agg_verification_sentiment",
    "agg_comment_score_sentiment",
    "agg_controversiality_sentiment",
    "agg_post_comment_sentiment",
    "agg_keyword_sentiment",
    "agg_association_stats",
)

SENTIMENTS: tuple[str, ...] = ("positive", "negative", "neutral")

# Pengelompokan tema keyword (identik dengan cell "Keyword and topic Analysys").
THEMES: dict[str, list[str]] = {
    "Konflik militer & kekerasan": [
        "war", "military", "attack", "attacks", "bomb", "bombs", "bombing", "killed", "kill",
        "killing", "army", "idf", "hamas", "rockets", "rocket", "missiles", "terrorist",
        "terrorists", "terrorism", "soldiers", "strike", "strikes", "weapons", "hostages", "hostage",
    ],
    "Kemanusiaan & korban sipil": [
        "civilians", "civilian", "children", "kids", "women", "innocent", "hospital", "hospitals",
        "aid", "food", "famine", "humanitarian", "genocide", "starvation", "refugees", "victims",
        "deaths", "dead",
    ],
    "Pemerintahan & politik": [
        "government", "trump", "biden", "netanyahu", "president", "congress", "election",
        "democrats", "republicans", "politics", "political", "vote", "party", "leaders",
        "administration", "usa", "america", "american",
    ],
    "Agama, etnis & identitas": [
        "jews", "jewish", "muslim", "muslims", "arab", "arabs", "islam", "islamic", "christian",
        "antisemitism", "antisemitic", "zionist", "zionism", "religion", "racist", "racism", "nazi",
    ],
    "Hukum, perdamaian & isu internasional": [
        "law", "international", "nations", "court", "icj", "ceasefire", "peace", "sanctions",
        "occupation", "occupied", "borders", "land", "settlements", "settlers",
    ],
}
