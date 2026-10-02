# Barcelona Airbnb: Where Would I Look Next?

## SQL: From Data to Insight — Project 1

This project looks at the Barcelona Airbnb market from the point of view of a potential investor.

The aim is **not** to use one dataset to declare where somebody should buy a property. There are far too many things missing for that, including acquisition costs, licensing, tax, operating costs and property-level information.

Instead, I used the data as a screening tool to answer a more useful question:

> **Where in Barcelona should a potential Airbnb investor investigate further, based on pricing potential, evidence of guest activity and the competitive landscape?**

I approached that through three questions:

1. Which Barcelona districts offer the strongest nightly pricing potential for comparable Airbnb listings?
2. Which districts show the strongest recent guest activity relative to the amount of Airbnb supply?
3. Which districts have the highest concentration of supply controlled by hosts with multiple listings?

The final analysis follows a simple path:

**Price → Activity → Competition → Trade-off → Further investigation**

---

## The data

I used the Barcelona snapshot from **Inside Airbnb**, dated **24 June 2026**.

The raw data contained:

- **15,293 listings**
- **1,033,523 review rows**
- **69 neighbourhoods**
- **10 districts**
- **4,595 hosts**

Data from [Inside Airbnb](http://insideairbnb.com), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

A few definitions matter when interpreting the results:

- `price` is the **advertised asking price**, not the price a guest actually paid.
- Recent reviews are used as a **proxy for guest activity**, not as a booking count.
- Estimated occupancy and revenue are **Inside Airbnb modelled metrics**, not observed host revenue.
- A host with more than one listing is described here as a **multi-listing host**. The data does not tell me whether that host is a professional or commercial operator.

---

## From raw files to a relational database

I started with the wide listings dataset and the separate reviews dataset, then reduced them to the fields needed for the analysis.

The final SQLite database contains four related tables:

### `locations`

One row per neighbourhood, with its corresponding Barcelona district.

- `location_id`
- `neighbourhood_name`
- `district_name`

### `hosts`

One row per host.

- `host_id`
- `host_name`
- `host_is_superhost`

### `listings`

One row per Airbnb listing.

- `listing_id`
- `host_id`
- `location_id`
- `room_type`
- `accommodates`
- `price`
- `minimum_nights`
- `number_of_reviews`
- `estimated_occupancy_l365d`
- `estimated_revenue_l365d`

### `reviews`

One row per review.

- `review_id`
- `listing_id`
- `review_date`

I originally considered keeping districts and neighbourhoods as separate lookup tables. During processing I simplified these into a single `locations` table because each neighbourhood already maps directly to one district and the combined table was enough for the questions I was asking.

The final database contains:

- **69 locations**
- **4,595 hosts**
- **15,293 listings**
- **1,026,931 reviews**

---

## The slightly annoying data problem

The most useful data-quality problem in the project appeared when I tried to enforce the relationship between reviews and listings.

The original reviews file contained **6,592 review rows belonging to 77 listing IDs that were not present in the current listings snapshot**.

I did not assume why those listings were missing because the data does not tell me.

Instead, those review rows were excluded from the relational database so that every review had a valid parent listing.

The final SQLite foreign-key check returned:

**0 issues**

That left **1,026,931 valid review rows** in the database.

For me this was an important part of the project. A database can load perfectly happily while still containing relationships that make later analysis unreliable, so I wanted the integrity checks to happen before I started drawing conclusions.

---

## SQL analysis

The analysis is held in `sql/queries.sql`.

I used seven queries which build from individual questions towards the final district comparison:

1. Median asking price by district
2. Like-for-like price by district, room type and guest capacity
3. Recent reviews per listing
4. Modelled occupancy and revenue as supporting context
5. Multi-listing host concentration
6. Largest host portfolios
7. Combined district summary

The aggregation is done in SQL and the resulting tables are then brought into Python for interpretation and visualisation.

---

## What I found

### 1. Eixample has the strongest price signal

At district level, Eixample has the highest median asking price at **€229 per night**.

That could simply have been caused by a different mix of properties, so I also compared similar listings.

For **entire homes/apartments accommodating two guests**, Eixample still had the highest median asking price:

- Eixample — **€179.87**
- Sarrià-Sant Gervasi — **€159**
- Sant Martí — **€147**
- Sants-Montjuïc — **€145.94**

So Eixample's price position is not just a result of comparing very different property types.

---

### 2. Strong pricing does not automatically mean strong activity

I used recent reviews per listing as a proxy for guest activity.

The strongest results were:

- Eixample — **15.96 reviews per listing**
- Sants-Montjuïc — **15.27**
- Sant Martí — **15.23**
- Gràcia — **15.19**

This matters because simply counting reviews would favour districts with more listings. Looking at reviews **per listing** gives a fairer comparison of activity relative to supply.

---

### 3. Much of the Airbnb supply is controlled by multi-listing hosts

Multi-listing hosts control a large proportion of Airbnb supply across Barcelona.

The concentration is particularly high in:

- Eixample — **86.08%**
- Sarrià-Sant Gervasi — **86.04%**
- Les Corts — **84.40%**

Sant Martí is lower at **71.45%**, while Horta-Guinardó has the lowest concentration at **64.25%**.

This creates an interesting trade-off.

The districts with the strongest commercial signals are not necessarily the districts with the least concentrated competitive environment.

---

## So where would I look next?

I deliberately did **not** create a single investment score.

There is no evidence-based reason for me to decide that price should be worth, for example, 40%, guest activity 35% and competition 25%. Doing that would make the output look more precise without actually making it more reliable.

Instead, I kept the measures separate.

The districts I would take into deeper investigation are:

### Eixample

The strongest headline market signal.

It ranks highest for both price and recent activity, but it also has one of the most concentrated competitive landscapes.

### Sant Martí

Very strong pricing and activity, with materially lower multi-listing host concentration than Eixample.

### Sants-Montjuïc

A strong activity-led alternative, although its price signal is lower.

### Horta-Guinardó

Commercial signals are weaker, but it has the least concentrated multi-listing host landscape in the analysis.

The point is not that one of these is automatically the correct answer.

They are interesting **for different reasons**.

---

## Visualisation

The Python report contains three main Matplotlib/Seaborn visualisations:

1. A district market landscape comparing:
   - median asking price
   - recent reviews per listing
   - total supply
   - multi-listing host concentration

2. Like-for-like asking price for entire homes/apartments accommodating two guests

3. Percentage of district supply belonging to multi-listing hosts

The main visualisation is deliberately multi-dimensional because looking at price alone would hide the trade-offs that became important later in the analysis.

---

## Interactive Streamlit dashboard

I also built a Streamlit dashboard:

**Barcelona Airbnb Investment Explorer**

It turns the static analysis into something that can be explored interactively.

The dashboard allows a user to:

- compare two districts directly
- explore asking price, activity, supply and host concentration
- change room type and guest capacity
- look behind the median using listing-level distributions
- compare districts across separate price, activity and competition rankings

I deliberately keep those rankings separate rather than combining them into a made-up investment score.

The dashboard currently runs locally with:

```bash
streamlit run streamlit_app.py
```

If deployed through Streamlit, the same dashboard could be shared as a browser-based tool without the end user needing Python, VS Code or any of the local development setup.

---

## Limitations

This analysis is useful for narrowing the market, but it is not enough to make a property investment decision.

In particular:

- asking price is not achieved price
- review activity is not the same as bookings
- Inside Airbnb occupancy and revenue figures are modelled estimates
- district medians hide variation between neighbourhoods and individual properties
- the data does not include property acquisition prices
- regulatory and licensing feasibility is not assessed
- operating costs are not included
- tax and financing are not included

These are not small details. They are the next stage of the investment decision.

---

## What I would do next

The next stage would move below district level and combine the Airbnb analysis with external property and regulatory data.

I would investigate:

- neighbourhood-level price and activity
- individual property acquisition costs
- Barcelona short-term rental licensing and regulation
- cleaning and maintenance costs
- platform and management fees
- financing
- taxation
- seasonality
- property-level projected returns

That would move the work from **market screening** towards an actual investment case.

---

## Project structure

```text
.
├── data/
│   ├── raw/
│   ├── clean/
│   └── project.db
│
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_processing.ipynb
│   └── 03_hypothesis_and_visualization.ipynb
│
├── sql/
│   ├── schema.sql
│   └── queries.sql
│
├── src/
│   └── functions.py
│
├── streamlit_app.py
├── download_data.py
└── README.md
```

Raw data is not intended to be committed to GitHub.

---

## Running the project

### 1. Download the Airbnb data

From the project root:

```bash
python download_data.py airbnb
```

### 2. Run the notebooks in order

```text
01_eda.ipynb
02_processing.ipynb
03_hypothesis_and_visualization.ipynb
```

Notebook 02 creates the relational SQLite database used in the later analysis.

### 3. Run the Streamlit dashboard

From the project root:

```bash
streamlit run streamlit_app.py
```

The app will normally open at:

```text
http://localhost:8501
```

---

## Final thought

The most useful thing this project did was not identify a single "best" Barcelona district.

It showed why that answer would be too simple.

Eixample leads on price and recent activity. Sant Martí remains close on both while showing materially lower multi-listing host concentration. Sants-Montjuïc gives another strong activity signal, while Horta-Guinardó represents a very different competitive environment.

That is enough to decide **where to look harder next**.

It is not enough to decide where to buy — and I think keeping that distinction clear makes the analysis more useful rather than less.