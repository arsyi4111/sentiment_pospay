import ast
import html
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


DATA_OPTIONS = {
    "Latest pipeline output": "data/processed/reviews.csv",
    "POSPAY 2024-2026": "data/processed/24to26_pospayreviews.csv",
    "BNI benchmark": "data/processed/BNIreviews.csv",
}

SENTIMENT_ORDER = ["negative", "neutral", "positive"]
SENTIMENT_LABELS = {
    "negative": "Negative",
    "neutral": "Neutral",
    "positive": "Positive",
}
SENTIMENT_COLORS = {
    "negative": "#C2410C",
    "neutral": "#64748B",
    "positive": "#15803D",
}

CATEGORY_ORDER = [
    "authentication",
    "feature",
    "transaction",
    "performance",
    "support",
    "ux/ui",
    "security",
    "pricing",
    "other",
]

CATEGORY_LABELS = {
    "authentication": "Authentication & Account Access",
    "feature": "Feature Availability",
    "transaction": "Transaction & Payment",
    "performance": "Performance & Reliability",
    "support": "Customer Support",
    "ux/ui": "UX/UI & Navigation",
    "security": "Security & Trust",
    "pricing": "Pricing & Fees",
    "other": "Other Product Feedback",
    "positive_feedback": "Positive Feedback",
    "neutral_feedback": "Neutral Feedback",
}

CATEGORY_DESCRIPTIONS = {
    "authentication": "Login, password, PIN, OTP, validation, account access, and device changes.",
    "feature": "Unavailable, missing, or broken menu and feature flows.",
    "transaction": "Transfer, QRIS, balance, top-up, refund, payment, billing, and e-wallet flows.",
    "performance": "Error, crash, loading, server, slow, timeout, update, and reliability complaints.",
    "support": "CS response, complaints, service quality, help, and resolution experience.",
    "ux/ui": "Confusing flows, difficult navigation, visual layout, and usability friction.",
    "security": "Fraud, unauthorized activity, privacy, scam, data leak, and trust concerns.",
    "pricing": "Admin fee, charge, price, and cost-related complaints.",
    "other": "Feedback that does not match the major operating categories.",
    "positive_feedback": "Reviews without explicit issues that praise value, ease, speed, or usefulness.",
    "neutral_feedback": "Reviews without explicit issues that do not express a strong direction.",
}

CATEGORY_KEYWORDS = {
    "authentication": [
        "login",
        "log in",
        "masuk",
        "password",
        "pass",
        "access",
        "akses",
        "verification",
        "verifikasi",
        "validasi",
        "email",
        "face",
        "akun",
        "upgrade",
        "pin",
        "username",
        "credentials",
        "otp",
        "two-factor",
        "2fa",
        "biometric",
        "sandi",
        "device",
        "blokir",
    ],
    "security": [
        "fraud",
        "unauthorized",
        "tidak sah",
        "keamanan",
        "uang berkurang",
        "account balance",
        "phishing",
        "scam",
        "hacker",
        "breach",
        "data leak",
        "privacy",
        "privasi",
        "encryption",
        "enkripsi",
        "vulnerability",
        "kerentanan",
        "penipuan",
        "ditipu",
        "kebocoran",
    ],
    "transaction": [
        "transfer",
        "balance",
        "saldo",
        "pulsa",
        "topup",
        "top up",
        "payment",
        "pembayaran",
        "bayar",
        "transaksi",
        "refund",
        "withdrawal",
        "tarik",
        "deposit",
        "billing",
        "invoice",
        "bank transfer",
        "paket",
        "meterai",
        "materai",
        "ewallet",
        "e-wallet",
        "qris",
        "cod",
    ],
    "feature": [
        "cannot",
        "tidak bisa",
        "tidak muncul",
        "not available",
        "fitur",
        "menu",
        "tokopedia",
        "section",
        "option",
        "pilihan",
        "fitur hilang",
        "fitur tidak muncul",
        "fitur tidak tersedia",
        "tidak tersedia",
        "tidak ada",
        "dibuka",
        "digunakan",
    ],
    "performance": [
        "slow",
        "lemot",
        "lelet",
        "loading",
        "unresponsive",
        "always problematic",
        "frequent",
        "gangguan",
        "disruption",
        "server",
        "error",
        "eror",
        "crash",
        "hang",
        "lag",
        "timeout",
        "bug",
        "glitch",
        "freeze",
        "restart",
        "update",
        "upgrade",
        "lambat",
        "lama",
    ],
    "support": [
        "support",
        "service",
        "customer",
        "help",
        "cs",
        "contact",
        "response",
        "respon",
        "tanggapan",
        "bantuan",
        "layanan",
        "pelayanan",
        "dukungan",
        "komplain",
        "keluhan",
        "kantor pos",
        "kurir",
        "karyawan",
    ],
    "ux/ui": [
        "difficult",
        "complicated",
        "ribet",
        "rumit",
        "sulit",
        "not user-friendly",
        "user friendly",
        "ui",
        "appearance",
        "branding",
        "design",
        "navigasi",
        "interface",
        "pusing",
        "bingung",
        "tidak intuitif",
        "tampilan",
        "desain",
        "antarmuka",
    ],
    "pricing": [
        "biaya",
        "fee",
        "expensive",
        "mahal",
        "charge",
        "harga",
        "price",
        "admin",
    ],
}


def inject_style():
    st.markdown(
        """
        <style>
        :root {
            --pospay-ink: #172033;
            --pospay-muted: #667085;
            --pospay-line: #E6EAF0;
            --pospay-panel: #FFFFFF;
            --pospay-soft: #F7F9FC;
            --pospay-accent: #0F766E;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.4rem;
            max-width: 1380px;
        }
        div[data-testid="stMetric"] {
            background: var(--pospay-panel);
            border: 1px solid var(--pospay-line);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetric"] label {
            color: var(--pospay-muted);
            font-size: 0.84rem;
        }
        div[data-testid="stMetricValue"] {
            color: var(--pospay-ink);
            font-size: 1.7rem;
        }
        .hero {
            border: 1px solid var(--pospay-line);
            border-radius: 8px;
            padding: 22px 24px;
            background: linear-gradient(135deg, #FFFFFF 0%, #F6FAF9 48%, #EEF6F2 100%);
            margin-bottom: 18px;
        }
        .hero h1 {
            color: var(--pospay-ink);
            font-size: 2rem;
            line-height: 1.2;
            margin: 0 0 8px;
            letter-spacing: 0;
        }
        .hero p {
            color: var(--pospay-muted);
            margin: 0;
            max-width: 900px;
        }
        .section-title {
            color: var(--pospay-ink);
            font-size: 1.15rem;
            font-weight: 700;
            margin: 20px 0 8px;
        }
        .insight-box {
            border: 1px solid var(--pospay-line);
            border-radius: 8px;
            padding: 14px 16px;
            background: var(--pospay-soft);
            min-height: 106px;
        }
        .insight-box strong {
            color: var(--pospay-ink);
        }
        .insight-box span {
            color: var(--pospay-muted);
            display: block;
            margin-top: 6px;
        }
        .metric-card {
            background: var(--pospay-panel);
            border: 1px solid var(--pospay-line);
            border-radius: 8px;
            padding: 16px 18px;
            min-height: 106px;
            box-shadow: 0 10px 22px rgba(15, 23, 42, 0.04);
        }
        .metric-label {
            color: var(--pospay-muted);
            font-size: 0.84rem;
            margin-bottom: 8px;
        }
        .metric-value {
            color: var(--pospay-ink);
            font-size: 1.7rem;
            font-weight: 700;
            line-height: 1.15;
        }
        .metric-note {
            color: var(--pospay-muted);
            font-size: 0.86rem;
            margin-top: 8px;
        }
        .review-card {
            border: 1px solid var(--pospay-line);
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: #FFFFFF;
        }
        .review-meta {
            color: var(--pospay-muted);
            font-size: 0.82rem;
            margin-bottom: 8px;
        }
        .review-text {
            color: var(--pospay-ink);
            line-height: 1.48;
        }
        .tag {
            display: inline-block;
            border: 1px solid var(--pospay-line);
            border-radius: 999px;
            padding: 2px 8px;
            margin: 8px 6px 0 0;
            color: #334155;
            background: #F8FAFC;
            font-size: 0.78rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_issues(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if pd.isna(value):
        return []

    text = str(value).strip()
    if not text or text == "[]":
        return []

    try:
        parsed = ast.literal_eval(text)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except (ValueError, SyntaxError):
        pass

    return [part.strip(" []'\"") for part in text.split(",") if part.strip(" []'\"")]


def normalize_sentiment(value):
    text = str(value).strip().lower()
    return text if text in SENTIMENT_ORDER else "neutral"


def category_for_issue(issue, sentiment="negative"):
    text = str(issue).lower()
    if not text:
        if sentiment == "positive":
            return "positive_feedback"
        if sentiment == "neutral":
            return "neutral_feedback"
        return "other"

    for category in CATEGORY_ORDER:
        if any(keyword in text for keyword in CATEGORY_KEYWORDS.get(category, [])):
            return category
    return "other"


@st.cache_data(show_spinner=False)
def load_data(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)
    if "review_date" in df.columns:
        df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
    else:
        df["review_date"] = pd.NaT

    if "rating" in df.columns:
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    else:
        df["rating"] = pd.NA

    if "sentiment" not in df.columns:
        df["sentiment"] = "neutral"
    if "issues" not in df.columns:
        df["issues"] = "[]"
    if "summary" not in df.columns:
        df["summary"] = ""
    if "text" not in df.columns:
        df["text"] = ""

    df["sentiment"] = df["sentiment"].apply(normalize_sentiment)
    df["issues_parsed"] = df["issues"].apply(parse_issues)
    df["primary_category"] = df.apply(
        lambda row: category_for_issue(
            row["issues_parsed"][0] if row["issues_parsed"] else "",
            row["sentiment"],
        ),
        axis=1,
    )
    return df


def explode_issues(df):
    records = []
    for idx, row in df.iterrows():
        issues = row["issues_parsed"]
        if not issues:
            continue

        for issue in issues:
            records.append(
                {
                    "row_id": idx,
                    "issue": issue,
                    "category": category_for_issue(issue, row["sentiment"]),
                    "sentiment": row["sentiment"],
                }
            )
    return pd.DataFrame(records)


def format_pct(value):
    if pd.isna(value):
        return "0.0%"
    return f"{value:.1f}%"


def build_sentiment_summary(df):
    summary = df["sentiment"].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
    return summary.rename_axis("sentiment").reset_index(name="count")


def build_category_summary(df, issue_rows):
    if issue_rows.empty:
        return pd.DataFrame(columns=["category", "label", "reviews", "mentions", "share"])

    grouped = (
        issue_rows.groupby("category")
        .agg(reviews=("row_id", "nunique"), mentions=("issue", "count"))
        .reset_index()
    )
    grouped["label"] = grouped["category"].map(CATEGORY_LABELS).fillna(grouped["category"])
    grouped["share"] = grouped["reviews"] / max(len(df), 1) * 100
    ordered = CATEGORY_ORDER + ["positive_feedback", "neutral_feedback"]
    grouped["order"] = grouped["category"].apply(
        lambda value: ordered.index(value) if value in ordered else len(ordered)
    )
    return grouped.sort_values(["reviews", "order"], ascending=[False, True])


def build_issue_summary(issue_rows, category=None):
    scoped = issue_rows.copy()
    if category and category != "all":
        scoped = scoped[scoped["category"] == category]
    if scoped.empty:
        return pd.DataFrame(columns=["issue", "reviews", "mentions"])

    return (
        scoped.groupby("issue")
        .agg(reviews=("row_id", "nunique"), mentions=("issue", "count"))
        .reset_index()
        .sort_values(["reviews", "mentions"], ascending=False)
    )


def build_timeseries(df, granularity):
    scoped = df.dropna(subset=["review_date"]).copy()
    if scoped.empty:
        return pd.DataFrame(columns=["period", "period_label", *SENTIMENT_ORDER, "total"])

    if granularity == "Daily":
        scoped["period"] = scoped["review_date"].dt.to_period("D").dt.to_timestamp()
        scoped["period_label"] = scoped["period"].dt.strftime("%Y-%m-%d")
    elif granularity == "Yearly":
        scoped["period"] = scoped["review_date"].dt.to_period("Y").dt.to_timestamp()
        scoped["period_label"] = scoped["period"].dt.strftime("%Y")
    else:
        scoped["period"] = scoped["review_date"].dt.to_period("M").dt.to_timestamp()
        scoped["period_label"] = scoped["period"].dt.strftime("%b %Y")

    trend = (
        scoped.groupby(["period", "period_label", "sentiment"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
        .sort_index()
    )
    trend["total"] = trend[SENTIMENT_ORDER].sum(axis=1)
    return trend.reset_index().sort_values("period")


def apply_sidebar_filters(df):
    with st.sidebar:
        st.header("Filters")
        dataset_label = st.selectbox("Dataset", list(DATA_OPTIONS.keys()))
        st.divider()

    selected_path = DATA_OPTIONS[dataset_label]
    df = load_data(selected_path)
    if df.empty:
        return df, selected_path

    with st.sidebar:
        sentiment_filter = st.multiselect(
            "Sentiment",
            options=SENTIMENT_ORDER,
            default=SENTIMENT_ORDER,
            format_func=lambda item: SENTIMENT_LABELS[item],
        )

        valid_dates = df["review_date"].dropna()
        if valid_dates.empty:
            date_range = None
        else:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            date_range = st.date_input("Date range", value=(min_date, max_date))

        rating_values = df["rating"].dropna()
        if rating_values.empty:
            rating_range = None
        else:
            min_rating = int(rating_values.min())
            max_rating = int(rating_values.max())
            rating_range = st.slider("Rating", min_rating, max_rating, (min_rating, max_rating))

        search_text = st.text_input("Search review text").strip().lower()

    filtered = df[df["sentiment"].isin(sentiment_filter)].copy()

    if date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        filtered = filtered[
            (filtered["review_date"].isna())
            | ((filtered["review_date"] >= start_date) & (filtered["review_date"] <= end_date))
        ]

    if rating_range:
        filtered = filtered[
            filtered["rating"].isna()
            | ((filtered["rating"] >= rating_range[0]) & (filtered["rating"] <= rating_range[1]))
        ]

    if search_text:
        filtered = filtered[
            filtered["text"].fillna("").str.lower().str.contains(search_text, regex=False)
        ]

    return filtered, selected_path


def render_header(source_path):
    st.markdown(
        """
        <div class="hero">
            <h1>Executive Review Intelligence</h1>
            <p>Prioritize the largest customer pain points, drill into issue categories, and trace every signal back to the original review.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Source: `{source_path}`")


def render_metric_card(column, label, value, note=""):
    column.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-note">{html.escape(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(df):
    total = len(df)
    negative = int((df["sentiment"] == "negative").sum())
    neutral = int((df["sentiment"] == "neutral").sum())
    positive = int((df["sentiment"] == "positive").sum())
    avg_rating = df["rating"].dropna().mean()
    issue_rate = df["issues_parsed"].apply(bool).mean() * 100 if total else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    render_metric_card(c1, "Reviews", f"{total:,}", "Filtered review count")
    render_metric_card(c2, "Negative", f"{negative:,}", f"{format_pct(negative / total * 100 if total else 0)} of reviews")
    render_metric_card(c3, "Neutral", f"{neutral:,}", f"{format_pct(neutral / total * 100 if total else 0)} of reviews")
    render_metric_card(c4, "Positive", f"{positive:,}", f"{format_pct(positive / total * 100 if total else 0)} of reviews")
    render_metric_card(
        c5,
        "Avg Rating",
        f"{avg_rating:.2f}" if pd.notna(avg_rating) else "N/A",
        f"{format_pct(issue_rate)} issue rate",
    )


def render_overview(df, category_summary):
    st.markdown('<div class="section-title">Executive Overview</div>', unsafe_allow_html=True)
    left, right = st.columns([1.05, 1.35])

    with left:
        sentiment_summary = build_sentiment_summary(df)
        fig = px.bar(
            sentiment_summary,
            x="sentiment",
            y="count",
            color="sentiment",
            color_discrete_map=SENTIMENT_COLORS,
            text="count",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        fig.update_layout(
            height=350,
            showlegend=False,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="",
            yaxis_title="Reviews",
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        if category_summary.empty:
            st.info("No explicit issue categories are available in the selected scope.")
        else:
            top_categories = category_summary.head(8)
            chart_data = top_categories.sort_values("reviews")
            fig = px.bar(
                chart_data,
                x="reviews",
                y="label",
                orientation="h",
                color="category",
                color_discrete_sequence=px.colors.qualitative.Safe,
                text=chart_data["share"].map(format_pct),
            )
            fig.update_layout(
                height=350,
                showlegend=False,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Reviews",
                yaxis_title="",
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            fig.update_traces(textposition="outside", cliponaxis=False)
            st.plotly_chart(fig, use_container_width=True)


def render_sentiment_timeseries(df):
    st.markdown('<div class="section-title">Sentiment Movement</div>', unsafe_allow_html=True)
    granularity = st.segmented_control(
        "Time aggregation",
        options=["Daily", "Monthly", "Yearly"],
        default="Monthly",
    )

    trend = build_timeseries(df, granularity)
    if trend.empty:
        st.info("No review date is available for the current selection.")
        return

    x_label = {"Daily": "Day", "Monthly": "Month", "Yearly": "Year"}[granularity]
    x_values = trend["period_label"]
    count_fig = go.Figure()
    for sentiment in SENTIMENT_ORDER:
        bar_text = [f"{value:,}" if value else "" for value in trend[sentiment]]
        count_fig.add_trace(
            go.Bar(
                x=x_values,
                y=trend[sentiment],
                name=f"{SENTIMENT_LABELS[sentiment]} reviews",
                marker_color=SENTIMENT_COLORS[sentiment],
                opacity=0.72,
                legendgroup=sentiment,
                text=bar_text,
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(color="white", size=11),
                hovertemplate=(
                    f"{x_label}: %{{x}}<br>"
                    f"{SENTIMENT_LABELS[sentiment]}: %{{y:,}} reviews<extra></extra>"
                ),
            )
        )

    for sentiment in SENTIMENT_ORDER:
        count_fig.add_trace(
            go.Scatter(
                x=x_values,
                y=trend[sentiment],
                name=f"{SENTIMENT_LABELS[sentiment]} trend",
                mode="lines+markers",
                line=dict(color=SENTIMENT_COLORS[sentiment], width=2.4),
                marker=dict(size=6),
                legendgroup=sentiment,
                showlegend=False,
            )
        )

    count_fig.add_trace(
        go.Scatter(
            x=x_values,
            y=trend["total"],
            name="Total reviews",
            mode="lines+markers+text",
            line=dict(color="#172033", width=2.2, dash="dot"),
            marker=dict(size=7, color="#172033"),
            text=[f"{value:,}" for value in trend["total"]],
            textposition="top center",
            textfont=dict(color="#172033", size=11),
            hovertemplate=f"{x_label}: %{{x}}<br>Total: %{{y:,}} reviews<extra></extra>",
        )
    )

    count_fig.update_layout(
        barmode="group",
        height=460,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title=x_label,
        yaxis_title="Reviews",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text="",
        hovermode="x unified",
        uniformtext=dict(mode="hide", minsize=9),
        xaxis=dict(type="category", tickangle=-35, automargin=True),
    )
    st.plotly_chart(count_fig, use_container_width=True)

    share = trend.copy()
    for sentiment in SENTIMENT_ORDER:
        share[sentiment] = (share[sentiment] / share["total"].where(share["total"] > 0) * 100).fillna(0)

    share_fig = go.Figure()
    for sentiment in SENTIMENT_ORDER:
        share_fig.add_trace(
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

    share_fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title=x_label,
        yaxis_title="Share of reviews",
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        xaxis=dict(type="category", tickangle=-35, automargin=True),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend_title_text="",
        hovermode="x unified",
    )
    st.plotly_chart(share_fig, use_container_width=True)


def render_insight_cards(df, category_summary, issue_summary):
    if df.empty:
        return

    top_category = category_summary.iloc[0] if not category_summary.empty else None
    top_issue = issue_summary.iloc[0] if not issue_summary.empty else None
    negative_share = (df["sentiment"] == "negative").mean() * 100

    c1, c2, c3 = st.columns(3)
    with c1:
        category_text = "No category detected"
        category_detail = "No issue category is available for the selected scope."
        if top_category is not None:
            category_text = top_category["label"]
            category_detail = f"{int(top_category['reviews']):,} reviews, {format_pct(top_category['share'])} of the filtered dataset."
        st.markdown(
            f'<div class="insight-box"><strong>Largest Kategori</strong><span>{category_text}<br>{category_detail}</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        issue_text = "No explicit issue"
        issue_detail = "The selected scope has no issue tags."
        if top_issue is not None:
            issue_text = html.escape(str(top_issue["issue"]))
            issue_detail = f"{int(top_issue['reviews']):,} reviews mention this issue."
        st.markdown(
            f'<div class="insight-box"><strong>Most repeated issue</strong><span>{issue_text}<br>{issue_detail}</span></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="insight-box"><strong>Risk pressure</strong><span>{format_pct(negative_share)} of filtered reviews are negative.<br>Use the kategori drill-down to isolate root causes.</span></div>',
            unsafe_allow_html=True,
        )


def render_category_drilldown(df, issue_rows, category_summary):
    st.markdown('<div class="section-title">Kategori Drill-Down</div>', unsafe_allow_html=True)

    category_options = ["all"] + category_summary["category"].tolist()
    selected_category = st.selectbox(
        "Kategori",
        category_options,
        format_func=lambda item: "All kategori" if item == "all" else CATEGORY_LABELS.get(item, item),
    )

    if selected_category != "all":
        scoped_rows = issue_rows[issue_rows["category"] == selected_category]
        scoped_df = df.loc[df.index.intersection(scoped_rows["row_id"].unique())].copy()
        st.info(CATEGORY_DESCRIPTIONS.get(selected_category, "Kategori description is not available."))
    else:
        scoped_rows = issue_rows.copy()
        scoped_df = df.copy()

    left, right = st.columns([1.25, 1])
    issue_summary = build_issue_summary(scoped_rows, None)

    with left:
        if issue_summary.empty:
            st.warning("No issues are available for this kategori.")
        else:
            top_issues = issue_summary.head(12).sort_values("reviews")
            fig = px.bar(
                top_issues,
                x="reviews",
                y="issue",
                orientation="h",
                color="reviews",
                color_continuous_scale=["#D6F3EA", "#0F766E"],
                text="reviews",
            )
            fig.update_layout(
                height=430,
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=20, b=10),
                xaxis_title="Reviews",
                yaxis_title="",
                plot_bgcolor="white",
                paper_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)

    with right:
        category_sentiment = build_sentiment_summary(scoped_df)
        donut_total = len(scoped_df)
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=[SENTIMENT_LABELS[item] for item in category_sentiment["sentiment"]],
                    values=category_sentiment["count"],
                    hole=0.62,
                    marker=dict(colors=[SENTIMENT_COLORS[item] for item in category_sentiment["sentiment"]]),
                )
            ]
        )
        fig.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=True,
            annotations=[
                dict(
                    text=f"<b>{donut_total:,}</b><br>reviews",
                    x=0.5,
                    y=0.5,
                    font=dict(size=18, color="#172033"),
                    showarrow=False,
                )
            ],
        )
        st.plotly_chart(fig, use_container_width=True)

        if not category_summary.empty:
            table = category_summary.copy()
            table["Share"] = table["share"].map(format_pct)
            table = table.rename(
                columns={"label": "Kategori", "reviews": "Reviews", "mentions": "Mentions"}
            )[["Kategori", "Reviews", "Mentions", "Share"]]
            st.dataframe(table, use_container_width=True, hide_index=True, height=220)

    return scoped_df, selected_category


def render_reviews(df):
    st.markdown('<div class="section-title">Review Traceback</div>', unsafe_allow_html=True)
    if df.empty:
        st.warning("No reviews match the current selection.")
        return

    sort_col = "review_date" if "review_date" in df.columns else None
    display_df = df.sort_values(sort_col, ascending=False) if sort_col else df.copy()

    detail_cols = [
        col
        for col in ["review_date", "rating", "sentiment", "primary_category", "issues", "summary", "text"]
        if col in display_df.columns
    ]
    table_df = display_df[detail_cols].copy()
    if "primary_category" in table_df.columns:
        table_df["primary_category"] = table_df["primary_category"].map(CATEGORY_LABELS).fillna(table_df["primary_category"])
    st.dataframe(table_df, use_container_width=True, hide_index=True, height=360)

    with st.expander("Read highlighted reviews", expanded=False):
        for _, row in display_df.head(6).iterrows():
            date_text = row["review_date"].date().isoformat() if pd.notna(row["review_date"]) else "No date"
            rating_text = "N/A" if pd.isna(row["rating"]) else f"{int(row['rating'])}/5"
            issues = row["issues_parsed"][:4]
            tags = "".join(f'<span class="tag">{html.escape(str(issue))}</span>' for issue in issues)
            review_text = html.escape(str(row["text"]))
            st.markdown(
                f"""
                <div class="review-card">
                    <div class="review-meta">{date_text} | {rating_text} | {SENTIMENT_LABELS.get(row["sentiment"], row["sentiment"])}</div>
                    <div class="review-text">{review_text}</div>
                    {tags}
                </div>
                """,
                unsafe_allow_html=True,
            )


def main():
    st.set_page_config(page_title="Executive Review Intelligence", layout="wide")
    inject_style()

    df, source_path = apply_sidebar_filters(pd.DataFrame())
    render_header(source_path)

    if df.empty:
        st.warning("No data is available for the current selection.")
        return

    issue_rows = explode_issues(df)
    category_summary = build_category_summary(df, issue_rows)
    issue_summary = build_issue_summary(issue_rows)

    render_kpis(df)
    render_overview(df, category_summary)
    render_sentiment_timeseries(df)
    render_insight_cards(df, category_summary, issue_summary)
    scoped_df, selected_category = render_category_drilldown(df, issue_rows, category_summary)
    render_reviews(scoped_df)

    category_label = "all kategori" if selected_category == "all" else CATEGORY_LABELS.get(selected_category, selected_category)
    st.caption(f"Showing {len(scoped_df):,} reviews for {category_label}.")


if __name__ == "__main__":
    main()
