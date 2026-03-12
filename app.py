from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


DATA_PATH = Path("cpsaat39.csv")

# Exact labels as they appear in the cleaned table
OCCUPATION_LABELS = {
    "Management, business, and financial operations occupations": "Management, business, and financial operations",
    "Professional and related occupations": "Professional and related",
    "Production occupations": "Production",
}


def load_data(path: Path) -> pd.DataFrame:
    # The file has an 8‑line text header; data start on line 10 (1‑indexed)
    df = pd.read_csv(
        path,
        skiprows=8,
        names=[
            "occupation",
            "total_workers",
            "total_median",
            "men_workers",
            "men_median",
            "women_workers",
            "women_median",
        ],
        na_values=["–"],
    )
    df = df.dropna(subset=["occupation"])
    df["occupation"] = df["occupation"].str.strip().str.strip('"')
    return df


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["occupation"].isin(OCCUPATION_LABELS.keys())
    subset = df.loc[mask].copy()

    subset["female_to_male_workers"] = subset["women_workers"] / subset["men_workers"]
    subset["female_to_male_earnings"] = subset["women_median"] / subset["men_median"]
    subset["earnings_gap_pct"] = (subset["women_median"] / subset["men_median"] - 1) * 100

    subset["short_label"] = subset["occupation"].map(OCCUPATION_LABELS)

    # Order in a way that reads naturally
    order = [
        "Management, business, and financial operations occupations",
        "Professional and related occupations",
        "Production occupations",
    ]
    subset["order"] = subset["occupation"].map({o: i for i, o in enumerate(order)})
    subset = subset.sort_values("order")

    return subset


def describe_dominance(row: pd.Series) -> str:
    ratio = row["female_to_male_workers"]
    label = row["short_label"]
    if ratio > 1.1:
        return f"{label} is female‑dominated: there are about {ratio:.2f} female workers for every male worker."
    if ratio < 0.9:
        return f"{label} is male‑dominated: there are about {ratio:.2f} female workers for every male worker."
    return f"{label} has a relatively balanced gender composition, with roughly equal numbers of men and women."


def describe_gap(row: pd.Series) -> str:
    gap = row["earnings_gap_pct"]
    label = row["short_label"]
    if np.isnan(gap):
        return f"For {label}, the gender earnings gap cannot be calculated because one of the medians is missing."
    if gap < -10:
        return (
            f"In {label}, women earn substantially less than men: their median weekly earnings are "
            f"about {abs(gap):.1f}% lower."
        )
    if gap < 0:
        return (
            f"In {label}, women earn somewhat less than men: their median weekly earnings are "
            f"around {abs(gap):.1f}% lower."
        )
    if gap > 10:
        return (
            f"In {label}, women out‑earn men by a sizable margin: their median weekly earnings are "
            f"about {gap:.1f}% higher."
        )
    if gap > 0:
        return (
            f"In {label}, women earn slightly more than men on average, with median earnings about "
            f"{gap:.1f}% higher."
        )
    return f"In {label}, men and women have very similar median weekly earnings."


def main() -> None:
    st.set_page_config(
        page_title="Gender Differences in Earnings by Occupation",
        layout="wide",
    )

    st.title("Gender Differences in Earnings by Broad Occupation Group")
    st.caption(
        "Based on CPS annual averages: median weekly earnings of full‑time wage and salary workers "
        "by detailed occupation and sex."
    )

    if not DATA_PATH.exists():
        st.error(f"Data file not found: {DATA_PATH}")
        st.stop()

    df = load_data(DATA_PATH)
    metrics = compute_metrics(df)

    st.sidebar.header("Study design")
    st.sidebar.markdown(
        """
        This dashboard focuses on three broad occupation groups:

        - Management, business, and financial operations  
        - Professional and related  
        - Production  

        For each group we compare:

        - The ratio of female to male workers  
        - The ratio of female to male median weekly earnings  
        - Overall median weekly earnings for the group
        """
    )

    st.subheader("1. Key summary statistics for the three occupation groups")
    display_cols = [
        "short_label",
        "total_workers",
        "total_median",
        "men_workers",
        "men_median",
        "women_workers",
        "women_median",
        "female_to_male_workers",
        "female_to_male_earnings",
    ]
    summary = metrics[display_cols].rename(
        columns={
            "short_label": "Occupation group",
            "total_workers": "Total workers (thousands)",
            "total_median": "Overall median weekly earnings ($)",
            "men_workers": "Men: workers (thousands)",
            "men_median": "Men: median weekly earnings ($)",
            "women_workers": "Women: workers (thousands)",
            "women_median": "Women: median weekly earnings ($)",
            "female_to_male_workers": "Female / male workers",
            "female_to_male_earnings": "Female / male median earnings",
        }
    )
    st.dataframe(
        summary.style.format(
            {
                "Total workers (thousands)": "{:,.0f}",
                "Men: workers (thousands)": "{:,.0f}",
                "Women: workers (thousands)": "{:,.0f}",
                "Overall median weekly earnings ($)": "${:,.0f}",
                "Men: median weekly earnings ($)": "${:,.0f}",
                "Women: median weekly earnings ($)": "${:,.0f}",
                "Female / male workers": "{:.2f}",
                "Female / male median earnings": "{:.2f}",
            }
        ),
        use_container_width=True,
    )

    st.markdown(
        """
        The table summarises the core quantities needed to answer the first question.  
        The worker ratios capture how female‑ or male‑dominated each occupation is, while the earnings
        ratios measure the relative median pay of women and men within the same occupation group.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Ratio of female to male workers")
        workers_chart = metrics.set_index("short_label")["female_to_male_workers"]
        st.bar_chart(workers_chart)
        st.markdown(
            """
            Values above 1 indicate that women outnumber men in the occupation group, whereas values below
            1 indicate male dominance. A ratio close to 1 suggests a more balanced gender composition.
            """
        )

    with col2:
        st.subheader("Ratio of female to male median weekly earnings")
        earnings_chart = metrics.set_index("short_label")["female_to_male_earnings"]
        st.bar_chart(earnings_chart)
        st.markdown(
            """
            Here, a value of 1 corresponds to pay parity at the median. Ratios below 1 signal that women
            earn less than men, and ratios above 1 indicate that women earn more than men in that group.
            """
        )

    st.subheader("Overall median weekly earnings by occupation group")
    st.bar_chart(metrics.set_index("short_label")["total_median"])

    st.markdown(
        """
        Comparing overall medians shows how typical weekly earnings vary across broad occupations,
        abstracting from gender. This helps separate differences due to occupational sorting from
        differences in pay between women and men within the same occupation group.
        """
    )

    st.subheader("2. Which occupations are more male/female dominated and where are gaps largest?")

    dominance_text = [describe_dominance(row) for _, row in metrics.iterrows()]
    gap_text = [describe_gap(row) for _, row in metrics.iterrows()]

    st.markdown("**Gender composition**")
    for sentence in dominance_text:
        st.markdown(f"- {sentence}")

    st.markdown("**Gender earnings gaps**")
    for sentence in gap_text:
        st.markdown(f"- {sentence}")

    st.subheader("3. Brief discussion of patterns by occupation group")
    for _, row in metrics.iterrows():
        label = row["short_label"]
        dominance = describe_dominance(row)
        gap = describe_gap(row)
        overall_median = row["total_median"]

        st.markdown(f"**{label}**")
        st.markdown(
            f"""
            {dominance} At the same time, {gap.lower()} The overall median weekly earnings in this group
            are about **${overall_median:,.0f}**, which places it in the context of the broader earnings
            distribution. Together, these statistics suggest that gender differences in both occupational
            sorting and within‑occupation pay contribute to the observed gaps, rather than a single
            factor operating in isolation.
            """
        )


if __name__ == "__main__":
    main()

