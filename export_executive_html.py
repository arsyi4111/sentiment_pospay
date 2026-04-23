import html
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.offline import get_plotlyjs

from dashboard_executive import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    SENTIMENT_COLORS,
    SENTIMENT_LABELS,
    SENTIMENT_ORDER,
    build_category_summary,
    build_issue_summary,
    build_sentiment_summary,
    build_timeseries,
    category_for_issue,
    parse_issues,
)


DATASETS = {
    "POSPAY 2024-2026": Path("data/processed/24to26_pospayreviews.csv"),
    "BNI Benchmark": Path("data/processed/BNIreviews.csv"),
}
OUTPUT_PATH = Path("executive_review_report.html")


def load_reviews(path):
    df = pd.read_csv(path)
    df["review_date"] = pd.to_datetime(df.get("review_date"), errors="coerce")
    df["rating"] = pd.to_numeric(df.get("rating"), errors="coerce")
    df["sentiment"] = df.get("sentiment", "neutral").fillna("neutral").str.lower()
    df["sentiment"] = df["sentiment"].where(df["sentiment"].isin(SENTIMENT_ORDER), "neutral")
    df["issues"] = df.get("issues", "[]")
    df["issues_parsed"] = df["issues"].apply(parse_issues)
    df["text"] = df.get("text", "").fillna("")
    df["primary_category"] = df.apply(
        lambda row: category_for_issue(
            row["issues_parsed"][0] if row["issues_parsed"] else "",
            row["sentiment"],
        ),
        axis=1,
    )
    return df


def explode_issues(df):
    rows = []
    for idx, row in df.iterrows():
        for issue in row["issues_parsed"]:
            rows.append(
                {
                    "row_id": idx,
                    "issue": issue,
                    "category": category_for_issue(issue, row["sentiment"]),
                    "sentiment": row["sentiment"],
                }
            )
    return pd.DataFrame(rows, columns=["row_id", "issue", "category", "sentiment"])


def pct(value):
    return f"{value:.1f}%"


def figure_html(fig):
    return pio.to_html(
        fig,
        include_plotlyjs=False,
        full_html=False,
        config={"displayModeBar": True, "displaylogo": False, "responsive": True},
    )


def sentiment_chart(df):
    summary = build_sentiment_summary(df)
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=[SENTIMENT_LABELS[item] for item in summary["sentiment"]],
            y=summary["count"],
            marker_color=[SENTIMENT_COLORS[item] for item in summary["sentiment"]],
            text=[f"{value:,}" for value in summary["count"]],
            textposition="outside",
            hovertemplate="%{x}: %{y:,} reviews<extra></extra>",
        )
    )
    fig.update_layout(
        height=330,
        margin=dict(l=20, r=20, t=24, b=40),
        xaxis_title="Sentiment",
        yaxis_title="Reviews",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def category_chart(category_summary):
    top = category_summary.head(9).sort_values("reviews")
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=top["reviews"],
            y=top["label"],
            orientation="h",
            marker_color="#0F766E",
            text=[f"{int(value):,}" for value in top["reviews"]],
            textposition="outside",
            hovertemplate="%{y}: %{x:,} reviews<extra></extra>",
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=30, t=24, b=40),
        xaxis_title="Reviews",
        yaxis_title="Kategori",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    return fig


def movement_chart(df):
    trend = build_timeseries(df, "Monthly")
    fig = go.Figure()
    x_values = trend["period_label"]
    for sentiment in SENTIMENT_ORDER:
        fig.add_trace(
            go.Bar(
                x=x_values,
                y=trend[sentiment],
                name=SENTIMENT_LABELS[sentiment],
                marker_color=SENTIMENT_COLORS[sentiment],
                text=[f"{value:,}" if value else "" for value in trend[sentiment]],
                textposition="inside",
                textfont=dict(color="white", size=10),
                hovertemplate=f"Month: %{{x}}<br>{SENTIMENT_LABELS[sentiment]}: %{{y:,}} reviews<extra></extra>",
            )
        )
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=trend["total"],
            name="Total reviews",
            mode="lines+markers+text",
            line=dict(color="#172033", width=2.2, dash="dot"),
            marker=dict(color="#172033", size=7),
            text=[f"{value:,}" for value in trend["total"]],
            textposition="top center",
            hovertemplate="Month: %{x}<br>Total: %{y:,} reviews<extra></extra>",
        )
    )
    fig.update_layout(
        barmode="group",
        height=430,
        margin=dict(l=20, r=20, t=24, b=80),
        xaxis_title="Month",
        yaxis_title="Reviews",
        xaxis=dict(type="category", tickangle=-35, automargin=True),
        uniformtext=dict(mode="hide", minsize=9),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text="",
        hovermode="x unified",
    )
    return fig


def share_chart(df):
    trend = build_timeseries(df, "Monthly")
    share = trend.copy()
    for sentiment in SENTIMENT_ORDER:
        share[sentiment] = (
            share[sentiment] / share["total"].where(share["total"] > 0) * 100
        ).fillna(0)

    fig = go.Figure()
    for sentiment in SENTIMENT_ORDER:
        fig.add_trace(
            go.Scatter(
                x=share["period_label"],
                y=share[sentiment],
                name=SENTIMENT_LABELS[sentiment],
                mode="lines+markers",
                line=dict(color=SENTIMENT_COLORS[sentiment], width=2.8),
                marker=dict(size=6),
                hovertemplate="%{y:.1f}%<extra></extra>",
            )
        )
    fig.update_layout(
        height=330,
        margin=dict(l=20, r=20, t=24, b=80),
        xaxis_title="Month",
        yaxis_title="Share of reviews",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        xaxis=dict(type="category", tickangle=-35, automargin=True),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text="",
        hovermode="x unified",
    )
    return fig


def metric_cards(df):
    total = len(df)
    avg_rating = df["rating"].dropna().mean()
    issue_rate = df["issues_parsed"].apply(bool).mean() * 100 if total else 0
    counts = df["sentiment"].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
    cards = [
        ("Reviews", f"{total:,}", "Total reviews in dataset"),
        ("Avg Rating", f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A", "Average store rating"),
        ("Issue Rate", pct(issue_rate), "Reviews with extracted issue"),
    ]
    for sentiment in SENTIMENT_ORDER:
        count = int(counts[sentiment])
        share = count / total * 100 if total else 0
        cards.append((SENTIMENT_LABELS[sentiment], f"{count:,}", f"{pct(share)} of reviews"))

    return "\n".join(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-note">{html.escape(note)}</div>
        </div>
        """
        for label, value, note in cards
    )


def top_issue_table(issue_summary):
    rows = []
    for _, row in issue_summary.head(12).iterrows():
        rows.append(
            f"""
            <tr>
                <td>{html.escape(str(row["issue"]))}</td>
                <td>{int(row["reviews"]):,}</td>
                <td>{int(row["mentions"]):,}</td>
            </tr>
            """
        )
    return f"""
    <table>
        <thead>
            <tr><th>Issue</th><th>Reviews</th><th>Mentions</th></tr>
        </thead>
        <tbody>{''.join(rows)}</tbody>
    </table>
    """


def review_examples(df):
    scoped = df[df["sentiment"] == "negative"].copy()
    scoped["issue_count"] = scoped["issues_parsed"].apply(len)
    scoped = scoped.sort_values(["issue_count", "review_date"], ascending=[False, False]).head(8)
    cards = []
    for _, row in scoped.iterrows():
        date = row["review_date"].date().isoformat() if pd.notna(row["review_date"]) else "No date"
        rating = "N/A" if pd.isna(row["rating"]) else f"{int(row['rating'])}/5"
        tags = "".join(
            f'<span class="tag">{html.escape(str(issue))}</span>'
            for issue in row["issues_parsed"][:4]
        )
        cards.append(
            f"""
            <div class="review-card">
                <div class="review-meta">{date} | {rating} | Negative</div>
                <div>{html.escape(str(row["text"]))}</div>
                <div>{tags}</div>
            </div>
            """
        )
    return "".join(cards)


def build_dataset_section(name, path, section_id):
    df = load_reviews(path)
    issue_rows = explode_issues(df)
    category_summary = build_category_summary(df, issue_rows)
    issue_summary = build_issue_summary(issue_rows)

    top_category = "No category"
    if not category_summary.empty:
        top = category_summary.iloc[0]
        top_category = f"{top['label']} ({int(top['reviews']):,} reviews)"

    return f"""
    <section class="dataset-section" id="{section_id}">
        <div class="section-heading">
            <div>
                <p class="eyebrow">Dataset</p>
                <h2>{html.escape(name)}</h2>
            </div>
            <div class="source">Source: {html.escape(str(path))}</div>
        </div>
        <div class="metrics">{metric_cards(df)}</div>
        <div class="insight-strip">
            <div><strong>Top kategori</strong><span>{html.escape(top_category)}</span></div>
            <div><strong>Period covered</strong><span>{df["review_date"].min().date()} to {df["review_date"].max().date()}</span></div>
        </div>
        <div class="grid two">
            <div class="panel"><h3>Sentiment Distribution</h3>{figure_html(sentiment_chart(df))}</div>
            <div class="panel"><h3>Top Issue Kategori</h3>{figure_html(category_chart(category_summary))}</div>
        </div>
        <div class="panel"><h3>Monthly Review Movement</h3>{figure_html(movement_chart(df))}</div>
        <div class="panel"><h3>Monthly Sentiment Share</h3>{figure_html(share_chart(df))}</div>
        <div class="grid two">
            <div class="panel"><h3>Top Issues</h3>{top_issue_table(issue_summary)}</div>
            <div class="panel"><h3>Review Traceback Examples</h3>{review_examples(df)}</div>
        </div>
    </section>
    """


def build_comparison_section(datasets):
    rows = []
    for name, df in datasets.items():
        total = len(df)
        avg_rating = df["rating"].dropna().mean()
        counts = df["sentiment"].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
        rows.append(
            f"""
            <tr>
                <td>{html.escape(name)}</td>
                <td>{total:,}</td>
                <td>{avg_rating:.2f}</td>
                <td>{pct(counts["negative"] / total * 100 if total else 0)}</td>
                <td>{pct(counts["neutral"] / total * 100 if total else 0)}</td>
                <td>{pct(counts["positive"] / total * 100 if total else 0)}</td>
            </tr>
            """
        )
    return f"""
    <section class="dataset-section active" id="comparison">
        <div class="section-heading">
            <div>
                <p class="eyebrow">Executive Comparison</p>
                <h2>POSPAY vs BNI</h2>
            </div>
        </div>
        <div class="panel">
            <table>
                <thead>
                    <tr>
                        <th>Dataset</th><th>Reviews</th><th>Avg Rating</th>
                        <th>Negative</th><th>Neutral</th><th>Positive</th>
                    </tr>
                </thead>
                <tbody>{''.join(rows)}</tbody>
            </table>
        </div>
    </section>
    """


def build_html():
    loaded = {name: load_reviews(path) for name, path in DATASETS.items()}
    sections = [
        build_comparison_section(loaded),
        build_dataset_section("POSPAY 2024-2026", DATASETS["POSPAY 2024-2026"], "pospay"),
        build_dataset_section("BNI Benchmark", DATASETS["BNI Benchmark"], "bni"),
    ]

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Executive Review Report</title>
    <script>{get_plotlyjs()}</script>
    <style>
        body {{
            margin: 0;
            background: #F6F8FB;
            color: #172033;
            font-family: Inter, Segoe UI, Arial, sans-serif;
        }}
        header {{
            background: linear-gradient(135deg, #FFFFFF 0%, #EFF8F5 100%);
            border-bottom: 1px solid #E6EAF0;
            padding: 28px 36px 20px;
        }}
        h1, h2, h3, p {{ margin-top: 0; }}
        h1 {{ margin-bottom: 8px; font-size: 32px; }}
        h2 {{ margin-bottom: 0; font-size: 24px; }}
        h3 {{ font-size: 16px; margin-bottom: 12px; }}
        .subtitle {{ color: #667085; max-width: 900px; margin-bottom: 18px; }}
        nav {{ display: flex; gap: 10px; flex-wrap: wrap; }}
        button {{
            border: 1px solid #CBD5E1;
            background: #FFFFFF;
            color: #172033;
            border-radius: 8px;
            padding: 10px 14px;
            cursor: pointer;
            font-weight: 700;
        }}
        button.active {{
            border-color: #0F766E;
            background: #E7F6F2;
            color: #0F766E;
        }}
        main {{ padding: 22px 36px 42px; }}
        .dataset-section {{ display: none; }}
        .dataset-section.active {{ display: block; }}
        .section-heading {{
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: end;
            margin: 10px 0 18px;
        }}
        .eyebrow {{
            color: #0F766E;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}
        .source {{ color: #667085; font-size: 13px; }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(6, minmax(130px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }}
        .metric-card, .panel, .insight-strip > div, .review-card {{
            background: #FFFFFF;
            border: 1px solid #E6EAF0;
            border-radius: 8px;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
        }}
        .metric-card {{ padding: 14px 16px; }}
        .metric-label, .metric-note, .review-meta {{ color: #667085; font-size: 13px; }}
        .metric-value {{ font-size: 24px; font-weight: 800; margin: 7px 0; }}
        .insight-strip {{
            display: grid;
            grid-template-columns: repeat(2, minmax(260px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }}
        .insight-strip > div {{ padding: 14px 16px; }}
        .insight-strip span {{ display: block; color: #667085; margin-top: 6px; }}
        .grid {{ display: grid; gap: 16px; margin-bottom: 16px; }}
        .grid.two {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
        .panel {{ padding: 16px; overflow: hidden; margin-bottom: 16px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        th, td {{ padding: 10px 8px; border-bottom: 1px solid #E6EAF0; text-align: left; vertical-align: top; }}
        th {{ color: #475467; background: #F8FAFC; }}
        .review-card {{ padding: 12px 14px; margin-bottom: 10px; line-height: 1.45; }}
        .tag {{
            display: inline-block;
            border: 1px solid #E6EAF0;
            border-radius: 999px;
            padding: 2px 8px;
            margin: 8px 6px 0 0;
            color: #334155;
            background: #F8FAFC;
            font-size: 12px;
        }}
        @media (max-width: 1000px) {{
            .metrics {{ grid-template-columns: repeat(2, minmax(130px, 1fr)); }}
            .grid.two, .insight-strip {{ grid-template-columns: 1fr; }}
            header, main {{ padding-left: 18px; padding-right: 18px; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Executive Review Report</h1>
        <p class="subtitle">Static stakeholder view built from POSPAY 2024-2026 reviews and BNI review data. Charts remain interactive for hover, zoom, and export through the browser.</p>
        <nav>
            <button class="tab active" data-target="comparison">Comparison</button>
            <button class="tab" data-target="pospay">POSPAY 2024-2026</button>
            <button class="tab" data-target="bni">BNI Benchmark</button>
        </nav>
    </header>
    <main>{''.join(sections)}</main>
    <script>
        document.querySelectorAll('.tab').forEach((button) => {{
            button.addEventListener('click', () => {{
                document.querySelectorAll('.tab').forEach((item) => item.classList.remove('active'));
                document.querySelectorAll('.dataset-section').forEach((item) => item.classList.remove('active'));
                button.classList.add('active');
                document.getElementById(button.dataset.target).classList.add('active');
                setTimeout(() => window.dispatchEvent(new Event('resize')), 30);
            }});
        }});
    </script>
</body>
</html>
"""


if __name__ == "__main__":
    OUTPUT_PATH.write_text(build_html(), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
