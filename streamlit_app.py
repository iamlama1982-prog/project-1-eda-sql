from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="Barcelona Airbnb Investment Explorer",
    page_icon="🏠",
    layout="wide"
)


# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "project.db"
SQL_PATH = ROOT / "sql" / "queries.sql"


# ---------------------------------------------------------
# LOAD ANALYSIS FROM SQL
# ---------------------------------------------------------

@st.cache_data
def load_analysis():
    sql_text = SQL_PATH.read_text(encoding="utf-8")

    queries = [
        query.strip()
        for query in sql_text.split(";")
        if query.strip()
    ]

    with sqlite3.connect(DB_PATH) as conn:

        district_summary = pd.read_sql(
            queries[6],
            conn
        )

        listing_detail = pd.read_sql(
            """
            SELECT
                loc.district_name,
                l.room_type,
                l.accommodates,
                l.price
            FROM listings AS l
            JOIN locations AS loc
                ON l.location_id = loc.location_id
            WHERE l.price IS NOT NULL
              AND l.price > 0
            """,
            conn
        )

    return district_summary, listing_detail


district_summary, listing_detail = load_analysis()


# ---------------------------------------------------------
# DISTRICT COLOURS
# ---------------------------------------------------------

district_colors = {
    "Eixample": "#D98B73",
    "Sant Martí": "#5FA8A8",
    "Gràcia": "#C58CA5",
    "Sants-Montjuïc": "#D8A45D",
    "Les Corts": "#8FAF87",
    "Sarrià-Sant Gervasi": "#A78CC4",
    "Horta-Guinardó": "#6F93A8",
    "Ciutat Vella": "#C96B5B",
    "Nou Barris": "#9B927F",
    "Sant Andreu": "#7E9B76"
}


# ---------------------------------------------------------
# VISUAL STYLE
# ---------------------------------------------------------

st.markdown(
    """
    <style>

        .stApp {
            background:
                radial-gradient(
                    circle at top right,
                    rgba(190, 95, 70, 0.12),
                    transparent 30%
                ),
                #0d1117;
        }

        .block-container {
            padding-top: 3rem;
            padding-bottom: 4rem;
        }

        h1 {
            font-size: 3rem !important;
            letter-spacing: -1.5px;
        }

        h2 {
            margin-top: 2rem;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 1.2rem;
            border-radius: 14px;
        }

        .eyebrow {
            color: #d98b73;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.12rem;
            text-transform: uppercase;
            margin-bottom: 0.4rem;
        }

        .intro {
            color: #b8c0cc;
            font-size: 1.15rem;
            max-width: 850px;
            margin-bottom: 1.5rem;
        }

        .investor-note {
            background: rgba(217, 139, 115, 0.08);
            border-left: 4px solid #d98b73;
            padding: 1rem 1.2rem;
            border-radius: 8px;
            margin-top: 1rem;
            margin-bottom: 1.5rem;
        }

    </style>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    '<div class="eyebrow">Barcelona market intelligence</div>',
    unsafe_allow_html=True
)

st.title("Barcelona Airbnb Investment Explorer")

st.markdown(
    """
    <div class="intro">
    Where should a potential Airbnb investor investigate further?
    Explore pricing potential, recent guest activity and the competitive
    landscape across Barcelona's districts.
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()


# ---------------------------------------------------------
# MARKET SNAPSHOT
# ---------------------------------------------------------

total_listings = district_summary["listings"].sum()

total_districts = district_summary[
    "district_name"
].nunique()

highest_price = district_summary.loc[
    district_summary["median_nightly_price"].idxmax()
]

highest_activity = district_summary.loc[
    district_summary["recent_reviews_per_listing"].idxmax()
]


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Airbnb listings",
        f"{total_listings:,}"
    )


with col2:
    st.metric(
        "Districts analysed",
        total_districts
    )


with col3:
    st.metric(
        "Highest median asking price",
        f"€{highest_price['median_nightly_price']:.0f}"
    )
    st.caption(
        highest_price["district_name"]
    )


with col4:
    st.metric(
        "Highest recent activity",
        f"{highest_activity['recent_reviews_per_listing']:.2f}"
    )
    st.caption(
        f"{highest_activity['district_name']} · reviews per listing"
    )


# ---------------------------------------------------------
# INVESTMENT LANDSCAPE
# ---------------------------------------------------------

st.markdown("## The investment landscape")

st.markdown(
    """
    <div class="investor-note">
    <b>How to read this:</b>
    further right means higher typical nightly prices,
    higher means stronger recent review activity,
    larger bubbles mean more Airbnb supply,
    and colour shows how much of that supply belongs
    to multi-listing hosts.
    </div>
    """,
    unsafe_allow_html=True
)


fig = px.scatter(
    district_summary,
    x="median_nightly_price",
    y="recent_reviews_per_listing",
    size="listings",
    color="pct_listings_from_multi_listing_hosts",
    hover_name="district_name",

    hover_data={
        "median_nightly_price": ":.2f",
        "recent_reviews_per_listing": ":.2f",
        "listings": ":,",
        "pct_listings_from_multi_listing_hosts": ":.2f"
    },

    labels={
        "median_nightly_price":
            "Median nightly asking price (€)",

        "recent_reviews_per_listing":
            "Recent reviews per listing",

        "listings":
            "Listings",

        "pct_listings_from_multi_listing_hosts":
            "Multi-listing host supply (%)"
    },

    color_continuous_scale=[
        "#39424e",
        "#a85f55",
        "#d98b73",
        "#f0c4a8"
    ],

    size_max=55
)


fig.update_traces(
    marker=dict(
        line=dict(
            width=1.2,
            color="rgba(255,255,255,0.35)"
        )
    )
)


fig.update_layout(
    height=650,

    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20
    ),

    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.025)",

    font=dict(
        color="#e8edf3"
    ),

    xaxis=dict(
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False
    ),

    yaxis=dict(
        gridcolor="rgba(255,255,255,0.08)",
        zeroline=False
    ),

    coloraxis_colorbar=dict(
        title="Multi-listing<br>host supply %"
    )
)


st.plotly_chart(
    fig,
    use_container_width=True
)


st.caption(
    "Hover over a district to inspect its pricing, recent activity, "
    "market size and multi-listing host concentration."
)


# ---------------------------------------------------------
# DISTRICT COMPARISON
# ---------------------------------------------------------

st.markdown("## Compare districts")

st.write(
    "Choose two Barcelona districts to compare their pricing potential, "
    "recent guest activity, market size and competitive concentration."
)


districts = district_summary[
    "district_name"
].tolist()


selector_col1, selector_col2 = st.columns(2)


with selector_col1:
    district_a = st.selectbox(
        "First district",
        districts,
        index=0,
        key="district_a"
    )


with selector_col2:
    district_b = st.selectbox(
        "Second district",
        districts,
        index=1,
        key="district_b"
    )


row_a = district_summary.loc[
    district_summary["district_name"] == district_a
].iloc[0]


row_b = district_summary.loc[
    district_summary["district_name"] == district_b
].iloc[0]


# ---------------------------------------------------------
# COMPARISON CHART FUNCTION
# ---------------------------------------------------------

def comparison_chart(
    title,
    column,
    prefix="",
    suffix="",
    decimals=2
):

    chart_data = pd.DataFrame({
        "District": [
            district_a,
            district_b
        ],

        "Value": [
            row_a[column],
            row_b[column]
        ]
    })


    fig = px.bar(
        chart_data,
        x="Value",
        y="District",
        orientation="h",
        text="Value",
        color="District",
        color_discrete_map=district_colors
    )


    if decimals == 0:
        text_template = (
            f"{prefix}%{{x:,.0f}}{suffix}"
        )
    else:
        text_template = (
            f"{prefix}%{{x:,.2f}}{suffix}"
        )


    fig.update_traces(
        texttemplate=text_template,
        textposition="outside",
        cliponaxis=False,
        marker_line_width=0
    )


    fig.update_layout(
        title=title,
        height=230,

        margin=dict(
            l=10,
            r=65,
            t=55,
            b=20
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.025)",

        font=dict(
            color="#e8edf3"
        ),

        showlegend=False,

        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.07)",
            title=None
        ),

        yaxis=dict(
            title=None,
            categoryorder="array",
            categoryarray=[
                district_b,
                district_a
            ]
        )
    )


    return fig


# ---------------------------------------------------------
# HEAD-TO-HEAD VISUALS
# ---------------------------------------------------------

st.markdown("### Head-to-head")


visual_col1, visual_col2 = st.columns(2)


with visual_col1:
    st.plotly_chart(
        comparison_chart(
            "Nightly asking price",
            "median_nightly_price",
            prefix="€"
        ),
        use_container_width=True
    )


with visual_col2:
    st.plotly_chart(
        comparison_chart(
            "Recent guest activity",
            "recent_reviews_per_listing"
        ),
        use_container_width=True
    )


visual_col3, visual_col4 = st.columns(2)


with visual_col3:
    st.plotly_chart(
        comparison_chart(
            "Airbnb supply",
            "listings",
            decimals=0
        ),
        use_container_width=True
    )


with visual_col4:
    st.plotly_chart(
        comparison_chart(
            "Supply controlled by multi-listing hosts",
            "pct_listings_from_multi_listing_hosts",
            suffix="%"
        ),
        use_container_width=True
    )


# ---------------------------------------------------------
# COMPARISON SUMMARY
# ---------------------------------------------------------

st.markdown("### What does the comparison tell us?")


def get_stronger_district(
    column,
    higher_is_stronger=True
):

    value_a = row_a[column]
    value_b = row_b[column]

    if value_a == value_b:
        return "Tie"

    if higher_is_stronger:
        return (
            district_a
            if value_a > value_b
            else district_b
        )

    return (
        district_a
        if value_a < value_b
        else district_b
    )


price_leader = get_stronger_district(
    "median_nightly_price"
)

activity_leader = get_stronger_district(
    "recent_reviews_per_listing"
)

supply_leader = get_stronger_district(
    "listings"
)

competition_leader = get_stronger_district(
    "pct_listings_from_multi_listing_hosts",
    higher_is_stronger=False
)


summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)


def summary_card(label, leader, description):

    color = district_colors.get(
        leader,
        "#e8edf3"
    )

    card_html = (
        f'<div style="'
        f'background: rgba(255,255,255,0.045);'
        f'border: 1px solid rgba(255,255,255,0.08);'
        f'border-radius: 14px;'
        f'padding: 18px;'
        f'min-height: 145px;">'

        f'<div style="'
        f'color:#9fa8b5;'
        f'font-size:0.85rem;">'
        f'{label}'
        f'</div>'

        f'<div style="'
        f'color:{color};'
        f'font-size:1.35rem;'
        f'font-weight:700;'
        f'margin-top:8px;">'
        f'{leader}'
        f'</div>'

        f'<div style="'
        f'color:#c7cdd5;'
        f'font-size:0.9rem;'
        f'margin-top:6px;">'
        f'{description}'
        f'</div>'

        f'</div>'
    )

    st.markdown(
        card_html,
        unsafe_allow_html=True
    )


with summary_col1:
    summary_card(
        "PRICING POTENTIAL",
        price_leader,
        "Higher median nightly asking price"
    )


with summary_col2:
    summary_card(
        "RECENT ACTIVITY",
        activity_leader,
        "More recent reviews per listing"
    )


with summary_col3:
    summary_card(
        "MARKET SIZE",
        supply_leader,
        "Larger Airbnb listing supply"
    )


with summary_col4:
    summary_card(
        "COMPETITIVE LANDSCAPE",
        competition_leader,
        "Lower multi-listing host concentration"
    )


# ---------------------------------------------------------
# OVERALL INTERPRETATION
# ---------------------------------------------------------

price_a = row_a[
    "median_nightly_price"
]

price_b = row_b[
    "median_nightly_price"
]

activity_a = row_a[
    "recent_reviews_per_listing"
]

activity_b = row_b[
    "recent_reviews_per_listing"
]

competition_a = row_a[
    "pct_listings_from_multi_listing_hosts"
]

competition_b = row_b[
    "pct_listings_from_multi_listing_hosts"
]


st.markdown(
    f"""
    <div class="investor-note">

    <b>Investor interpretation</b><br><br>

    <b>{district_a}</b> has a median nightly asking price of
    <b>€{price_a:.2f}</b> and recent activity of
    <b>{activity_a:.2f} reviews per listing</b>.
    Multi-listing hosts control
    <b>{competition_a:.2f}%</b> of its supply.

    <br><br>

    <b>{district_b}</b> has a median nightly asking price of
    <b>€{price_b:.2f}</b> and recent activity of
    <b>{activity_b:.2f} reviews per listing</b>.
    Multi-listing hosts control
    <b>{competition_b:.2f}%</b> of its supply.

    <br><br>

    <b>The trade-off:</b>
    {price_leader} shows stronger pricing potential,
    {activity_leader} shows stronger recent guest activity,
    while {competition_leader} has the less concentrated
    multi-listing competitive landscape.

    A larger Airbnb market is not automatically a better investment market,
    and lower competition does not compensate automatically for weaker
    pricing or guest activity. These measures should therefore be considered
    together before deciding which district deserves deeper investigation.

    </div>
    """,
    unsafe_allow_html=True
)


# ---------------------------------------------------------
# COMPARABLE PRICE DISTRIBUTION
# ---------------------------------------------------------

st.markdown("## What sits behind the median?")

st.write(
    "Compare the actual spread of asking prices for similar listings "
    "in the two selected districts."
)


room_types = sorted(
    listing_detail["room_type"]
    .dropna()
    .unique()
)


default_room_index = (
    room_types.index("Entire home/apt")
    if "Entire home/apt" in room_types
    else 0
)


filter_col1, filter_col2 = st.columns(2)


with filter_col1:
    selected_room_type = st.selectbox(
        "Room type",
        room_types,
        index=default_room_index,
        key="distribution_room_type"
    )


district_a_capacities = set(
    listing_detail.loc[
        (
            listing_detail["district_name"]
            == district_a
        )
        &
        (
            listing_detail["room_type"]
            == selected_room_type
        ),
        "accommodates"
    ]
    .dropna()
    .astype(int)
)


district_b_capacities = set(
    listing_detail.loc[
        (
            listing_detail["district_name"]
            == district_b
        )
        &
        (
            listing_detail["room_type"]
            == selected_room_type
        ),
        "accommodates"
    ]
    .dropna()
    .astype(int)
)


shared_capacities = sorted(
    district_a_capacities.intersection(
        district_b_capacities
    )
)


if shared_capacities:

    default_capacity_index = (
        shared_capacities.index(2)
        if 2 in shared_capacities
        else 0
    )


    with filter_col2:
        selected_capacity = st.selectbox(
            "Guest capacity",
            shared_capacities,
            index=default_capacity_index,
            key="distribution_capacity"
        )


    comparable_prices = listing_detail.loc[
        (
            listing_detail["district_name"]
            .isin([
                district_a,
                district_b
            ])
        )
        &
        (
            listing_detail["room_type"]
            == selected_room_type
        )
        &
        (
            listing_detail["accommodates"]
            == selected_capacity
        )
    ].copy()


    distribution_fig = px.box(
        comparable_prices,
        x="district_name",
        y="price",
        color="district_name",
        points="outliers",
        color_discrete_map=district_colors,

        labels={
            "district_name":
                "District",

            "price":
                "Nightly asking price (€)"
        }
    )


    distribution_fig.update_layout(
        height=520,

        title=(
            f"{selected_room_type} · "
            f"accommodates {selected_capacity}"
        ),

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.025)",

        font=dict(
            color="#e8edf3"
        ),

        showlegend=False,

        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        ),

        xaxis=dict(
            title=None,
            gridcolor="rgba(255,255,255,0.05)"
        ),

        yaxis=dict(
            title="Nightly asking price (€)",
            gridcolor="rgba(255,255,255,0.08)",
            zeroline=False
        )
    )


    st.plotly_chart(
        distribution_fig,
        use_container_width=True
    )


    median_a = comparable_prices.loc[
        comparable_prices["district_name"]
        == district_a,
        "price"
    ].median()


    median_b = comparable_prices.loc[
        comparable_prices["district_name"]
        == district_b,
        "price"
    ].median()


    sample_a = comparable_prices.loc[
        comparable_prices["district_name"]
        == district_a
    ].shape[0]


    sample_b = comparable_prices.loc[
        comparable_prices["district_name"]
        == district_b
    ].shape[0]


    st.markdown(
        f"""
        <div class="investor-note">

        <b>Like-for-like comparison</b><br><br>

        For <b>{selected_room_type.lower()}</b> listings accommodating
        <b>{selected_capacity}</b> guests, the median asking price is
        <b>€{median_a:.2f}</b> in {district_a} and
        <b>€{median_b:.2f}</b> in {district_b}.

        <br><br>

        This comparison includes
        <b>{sample_a}</b> listings in {district_a} and
        <b>{sample_b}</b> listings in {district_b}.

        <br><br>

        The boxes show the middle 50% of asking prices, while the whiskers
        and individual points show how widely prices vary around the median.
        This gives more context than comparing one headline price alone.

        </div>
        """,
        unsafe_allow_html=True
    )


else:

    st.warning(
        "These two districts do not have a shared guest-capacity group "
        "for the selected room type."
    )

    import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# INVESTOR DECISION MATRIX
# ---------------------------------------------------------
# ---------------------------------------------------------
# FINAL INVESTOR TRADE-OFF VIEW
# ---------------------------------------------------------

st.markdown("## Where should an investor investigate next?")

st.write(
    "Rather than combining different measures into an arbitrary score, "
    "this view shows where each priority district ranks among all 10 Barcelona "
    "districts for pricing potential, recent guest activity and competitive concentration."
)


# ---------------------------------------------------------
# CALCULATE CITYWIDE RANKS
# ---------------------------------------------------------

ranked_districts = district_summary.copy()

ranked_districts["price_rank"] = (
    ranked_districts["median_nightly_price"]
    .rank(method="min", ascending=False)
    .astype(int)
)

ranked_districts["activity_rank"] = (
    ranked_districts["recent_reviews_per_listing"]
    .rank(method="min", ascending=False)
    .astype(int)
)

# Lower concentration = less concentrated competitive landscape
ranked_districts["competition_rank"] = (
    ranked_districts["pct_listings_from_multi_listing_hosts"]
    .rank(method="min", ascending=True)
    .astype(int)
)


priority_districts = [
    "Eixample",
    "Sant Martí",
    "Sants-Montjuïc",
    "Horta-Guinardó"
]


priority_ranked = ranked_districts[
    ranked_districts["district_name"].isin(priority_districts)
].copy()


# Keep the presentation order deliberate rather than alphabetical
priority_ranked["display_order"] = priority_ranked[
    "district_name"
].map({
    "Eixample": 1,
    "Sant Martí": 2,
    "Sants-Montjuïc": 3,
    "Horta-Guinardó": 4
})

priority_ranked = priority_ranked.sort_values(
    "display_order"
)


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def rank_track(rank, colour):

    segments = ""

    for position in range(1, 11):

        if position == rank:
            segment_colour = colour
            opacity = "1"
            height = "10px"
        else:
            segment_colour = "#56606d"
            opacity = "0.30"
            height = "6px"

        segments += (
            f'<div style="'
            f'flex:1;'
            f'height:{height};'
            f'background:{segment_colour};'
            f'opacity:{opacity};'
            f'border-radius:5px;">'
            f'</div>'
        )

    return (
        f'<div style="'
        f'display:flex;'
        f'gap:5px;'
        f'align-items:center;'
        f'height:14px;'
        f'margin-top:10px;">'
        f'{segments}'
        f'</div>'
    )


def metric_card(
    value,
    rank,
    colour,
    value_prefix="",
    value_suffix="",
    decimals=2,
    rank_note=""
):

    formatted_value = f"{value:,.{decimals}f}"

    html = (
        f'<div style="'
        f'background:rgba(255,255,255,0.035);'
        f'border:1px solid rgba(255,255,255,0.08);'
        f'border-radius:14px;'
        f'padding:16px 18px;'
        f'min-height:135px;">'

        f'<div style="'
        f'font-size:1.55rem;'
        f'font-weight:700;'
        f'color:{colour};">'
        f'{value_prefix}{formatted_value}{value_suffix}'
        f'</div>'

        f'<div style="'
        f'font-size:0.88rem;'
        f'color:#c3cad3;'
        f'margin-top:3px;">'
        f'Rank <b>#{rank}</b> of 10'
        f'</div>'

        f'{rank_track(rank, colour)}'

        f'<div style="'
        f'font-size:0.78rem;'
        f'color:#89929e;'
        f'margin-top:8px;">'
        f'{rank_note}'
        f'</div>'

        f'</div>'
    )

    st.markdown(
        html,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# COLUMN HEADERS
# ---------------------------------------------------------

header_name, header_price, header_activity, header_competition = st.columns(
    [1.25, 1, 1, 1]
)

with header_name:
    st.markdown("#### District")

with header_price:
    st.markdown("#### Pricing potential")
    st.caption("Higher asking price = stronger")

with header_activity:
    st.markdown("#### Recent activity")
    st.caption("More recent reviews/listing = stronger")

with header_competition:
    st.markdown("#### Competitive landscape")
    st.caption("Lower concentration = less concentrated")


# ---------------------------------------------------------
# DISTRICT ROWS
# ---------------------------------------------------------

district_reads = {

    "Eixample": {
        "pro": "Strongest pricing and activity signals.",
        "con": "Most concentrated multi-listing host market."
    },

    "Sant Martí": {
        "pro": "Very strong price and activity with lower concentration.",
        "con": "Does not match Eixample's headline pricing."
    },

    "Sants-Montjuïc": {
        "pro": "Second-highest recent guest activity.",
        "con": "Lower pricing potential than the two leaders."
    },

    "Horta-Guinardó": {
        "pro": "Least concentrated competitive landscape.",
        "con": "Weaker pricing and activity signals."
    }
}


for _, row in priority_ranked.iterrows():

    district = row["district_name"]

    colour = district_colors.get(
        district,
        "#D98B73"
    )

    district_col, price_col, activity_col, competition_col = st.columns(
        [1.25, 1, 1, 1]
    )


    with district_col:

        district_html = (
            f'<div style="'
            f'border-left:4px solid {colour};'
            f'padding:12px 14px;'
            f'margin-top:4px;">'

            f'<div style="'
            f'font-size:1.25rem;'
            f'font-weight:700;'
            f'color:{colour};">'
            f'{district}'
            f'</div>'

            f'<div style="'
            f'font-size:0.82rem;'
            f'color:#c3cad3;'
            f'margin-top:8px;">'
            f'<b>Pro:</b> {district_reads[district]["pro"]}'
            f'</div>'

            f'<div style="'
            f'font-size:0.82rem;'
            f'color:#89929e;'
            f'margin-top:5px;">'
            f'<b>Watch:</b> {district_reads[district]["con"]}'
            f'</div>'

            f'</div>'
        )

        st.markdown(
            district_html,
            unsafe_allow_html=True
        )


    with price_col:

        metric_card(
            row["median_nightly_price"],
            row["price_rank"],
            colour,
            value_prefix="€",
            decimals=2,
            rank_note="1 = highest pricing potential"
        )


    with activity_col:

        metric_card(
            row["recent_reviews_per_listing"],
            row["activity_rank"],
            colour,
            decimals=2,
            rank_note="1 = strongest recent activity"
        )


    with competition_col:

        metric_card(
            row["pct_listings_from_multi_listing_hosts"],
            row["competition_rank"],
            colour,
            value_suffix="%",
            decimals=2,
            rank_note="1 = least concentrated"
        )


    st.markdown(
        "<div style='height:10px;'></div>",
        unsafe_allow_html=True
    )


# ---------------------------------------------------------
# FINAL TAKEAWAY
# ---------------------------------------------------------

st.markdown(
    """
    <div class="investor-note">

    <b>What does the evidence suggest?</b><br><br>

    <b>Eixample</b> is the clearest market-strength leader:
    #1 for both pricing potential and recent guest activity.
    Its trade-off is competition — it is also the most concentrated
    district among multi-listing hosts.

    <br><br>

    <b>Sant Martí</b> is consistently near the top:
    #2 for pricing and #3 for recent activity, while its competitive
    concentration is materially lower than Eixample.

    <br><br>

    <b>Sants-Montjuïc</b> is an activity-led alternative,
    ranking #2 for recent guest activity while remaining strong on price.

    <br><br>

    <b>Horta-Guinardó</b> offers the opposite trade-off:
    weaker commercial signals, but the least concentrated competitive
    environment in Barcelona.

    <br><br>

    <b>Investor takeaway:</b>
    The evidence supports <b>Eixample and Sant Martí as the first areas
    for deeper investigation</b>, with Sants-Montjuïc as a strong
    alternative. Horta-Guinardó is useful as a contrasting lower-competition
    option rather than a direct market-strength leader.

    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "These rankings describe relative position within this dataset only. "
    "They do not predict investment returns. Property acquisition costs, "
    "operating costs, regulation and licensing require separate due diligence."
)