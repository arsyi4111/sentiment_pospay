import ast
import os
from collections import Counter

import pandas as pd
import plotly.express as px
import streamlit as st

DATA_PATH = "data/processed/reviews.csv"
SENTIMENT_ORDER = ["positive", "neutral", "negative"]


def parse_issues(value):
    if pd.isna(value):
        return []

    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]

    text = str(value).strip()
    if not text:
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(v).strip() for v in parsed if str(v).strip()]
    except (ValueError, SyntaxError):
        pass

    return [part.strip() for part in text.split(",") if part.strip()]


def load_data(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)
    if "review_date" in df.columns:
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")

    if "sentiment" not in df.columns:
        df["sentiment"] = "unknown"

    if "issues" not in df.columns:
        df["issues"] = [[] for _ in range(len(df))]

    df["issues_parsed"] = df["issues"].apply(parse_issues)
    df["sentiment"] = df["sentiment"].fillna("unknown").str.lower()
    return df


def issue_summary(df):
    counter = Counter()
    for issues in df["issues_parsed"]:
        counter.update(issues)

    if not counter:
        return pd.DataFrame(columns=["issue", "count"])

    summary_df = pd.DataFrame(counter.items(), columns=["issue", "count"])
    return summary_df.sort_values("count", ascending=False)


def sentiment_summary(df):
    summary = (
        df["sentiment"]
        .value_counts()
        .rename_axis("sentiment")
        .reset_index(name="count")
    )
    summary["sentiment"] = pd.Categorical(
        summary["sentiment"], categories=SENTIMENT_ORDER, ordered=True
    )
    return summary.sort_values("sentiment")


def main():
    st.set_page_config(page_title="Executive Review Dashboard", layout="wide")
    st.title("Executive Summary Dashboard - Ulasan Aplikasi")
    st.caption(
        "Alur: Executive overview -> zoom in ke sentimen -> zoom in ke issue -> review detail."
    )

    df = load_data(DATA_PATH)

    if df.empty:
        st.warning(
            "Data belum tersedia. Jalankan pipeline dulu supaya file data/processed/reviews.csv terbentuk."
        )
        return

    total_reviews = len(df)
    sentiment_counts = sentiment_summary(df)
    positive_count = int((df["sentiment"] == "positive").sum())
    neutral_count = int((df["sentiment"] == "neutral").sum())
    negative_count = int((df["sentiment"] == "negative").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Review", f"{total_reviews:,}")
    c2.metric("Positive", f"{positive_count:,}")
    c3.metric("Neutral", f"{neutral_count:,}")
    c4.metric("Negative", f"{negative_count:,}")

    st.subheader("Gambaran Umum Sentimen")
    chart_col, filter_col = st.columns([2, 1])

    with chart_col:
        fig_sent = px.bar(
            sentiment_counts,
            x="sentiment",
            y="count",
            color="sentiment",
            color_discrete_map={
                "positive": "#2ca02c",
                "neutral": "#7f7f7f",
                "negative": "#d62728",
            },
            title="Distribusi Sentimen",
        )
        fig_sent.update_layout(showlegend=False)
        st.plotly_chart(fig_sent, use_container_width=True)

    with filter_col:
        selected_sentiment = st.selectbox(
            "Zoom in: pilih sentimen",
            options=["all"] + SENTIMENT_ORDER,
            index=0,
        )

    filtered = df.copy()
    if selected_sentiment != "all":
        filtered = filtered[filtered["sentiment"] == selected_sentiment]

    st.subheader("Rekapan Isu (Issue) pada Poin Terpilih")
    issue_df = issue_summary(filtered)

    if issue_df.empty:
        st.info("Belum ada issue yang bisa diringkas untuk filter ini.")
        selected_issue = "all"
    else:
        top_n = min(15, len(issue_df))
        fig_issue = px.bar(
            issue_df.head(top_n),
            x="count",
            y="issue",
            orientation="h",
            title="Top Issue",
        )
        fig_issue.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_issue, use_container_width=True)

        selected_issue = st.selectbox(
            "Zoom in lanjutan: pilih issue",
            options=["all"] + issue_df["issue"].tolist(),
            index=0,
        )

    if selected_issue != "all":
        filtered = filtered[
            filtered["issues_parsed"].apply(lambda items: selected_issue in items)
        ]

    st.subheader("Informasi Krusial")
    if "summary" in filtered.columns and not filtered["summary"].dropna().empty:
        crucial = (
            filtered["summary"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .head(10)
        )
        if crucial.empty:
            st.write("Belum ada ringkasan yang tersedia.")
        else:
            for i, point in enumerate(crucial, start=1):
                st.markdown(f"**{i}.** {point}")
    else:
        st.write("Kolom summary belum tersedia. Jalankan pipeline dengan AI enrichment aktif.")

    st.subheader("Review Detail")
    detail_cols = [
        col
        for col in ["review_id", "review_date", "rating", "sentiment", "issues", "summary", "text"]
        if col in filtered.columns
    ]
    st.dataframe(filtered[detail_cols], use_container_width=True, hide_index=True)

    st.caption(f"Menampilkan {len(filtered):,} review dari total {total_reviews:,} review.")


if __name__ == "__main__":
    main()
