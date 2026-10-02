-- ============================================================
-- PROJECT 1: BARCELONA AIRBNB INVESTOR ANALYSIS
-- ============================================================
--
-- The analysis looks at three areas:
-- 1. Nightly pricing potential
-- 2. Recent guest activity relative to supply
-- 3. Competition from hosts with multiple listings
--
-- The final aim is to identify which Barcelona districts
-- are worth investigating further as potential Airbnb markets.
--

-- ============================================================


-- ============================================================
-- QUERY 1
-- Research question:
-- Which Barcelona districts offer the strongest nightly
-- pricing potential?
--
-- Purpose:
-- Compare the median asking price across districts.
-- Median is used rather than average because very expensive
-- listings could otherwise distort the result.
--
-- Finding:
-- Eixample had the highest district median asking price at €229,
-- followed by Sant Martí at €206.50. This gives Eixample the
-- strongest headline pricing signal in the dataset.
-- ============================================================

WITH ranked_prices AS (
    SELECT
        loc.district_name,
        l.price,
        ROW_NUMBER() OVER (
            PARTITION BY loc.district_name
            ORDER BY l.price
        ) AS row_num,
        COUNT(*) OVER (
            PARTITION BY loc.district_name
        ) AS group_size
    FROM listings AS l
    JOIN locations AS loc
        ON l.location_id = loc.location_id
    WHERE l.price IS NOT NULL)

SELECT
    district_name,
    MAX(group_size) AS listings_with_price,
    ROUND(AVG(price), 2) AS median_nightly_price
FROM ranked_prices
WHERE row_num IN (
    CAST((group_size + 1) / 2 AS INTEGER),
    CAST((group_size + 2) / 2 AS INTEGER))
GROUP BY district_name
ORDER BY median_nightly_price DESC;



-- ============================================================
-- QUERY 2
-- Research question:
-- Does the district price difference remain when similar
-- listings are compared?
--
-- Purpose:
-- Compare median prices within the same room type and guest
-- capacity. Groups with fewer than 20 listings are excluded
-- because very small groups could give a misleading comparison.
--
-- Finding:
-- The price difference remains when similar properties are compared.
-- For entire homes/apartments accommodating 2 guests, Eixample still
-- had the highest median asking price at €179.87, followed by
-- Sarrià-Sant Gervasi at €159 and Sant Martí at €147.
-- ============================================================

WITH ranked_comparables AS (
    SELECT
        loc.district_name,
        l.room_type,
        l.accommodates,
        l.price,
        ROW_NUMBER() OVER (
            PARTITION BY
                loc.district_name,
                l.room_type,
                l.accommodates
            ORDER BY l.price) AS row_num,
        COUNT(*) OVER (
            PARTITION BY
                loc.district_name,
                l.room_type,
                l.accommodates
        ) AS group_size
    FROM listings AS l
    JOIN locations AS loc
        ON l.location_id = loc.location_id
    WHERE l.price IS NOT NULL)

SELECT
    district_name,
    room_type,
    accommodates,
    MAX(group_size) AS comparable_listings,
    ROUND(AVG(price), 2) AS median_nightly_price
FROM ranked_comparables
WHERE group_size >= 20
AND row_num IN (
    CAST((group_size + 1) / 2 AS INTEGER),
    CAST((group_size + 2) / 2 AS INTEGER))
GROUP BY
    district_name,
    room_type,
    accommodates
ORDER BY
    room_type,
    accommodates,
    median_nightly_price DESC;



-- ============================================================
-- QUERY 3
-- Research question:
-- Which districts show the strongest recent guest activity
-- relative to the amount of Airbnb supply?
--
-- Purpose:
-- Count reviews during the most recent 12 months in the data
-- and compare them with the number of listings in each district.
-- Reviews per listing gives a fairer comparison than review
-- volume alone because districts have different amounts of supply.
--
-- Finding:
-- Eixample had the highest recent review activity at 15.96 reviews
-- per listing. Sants-Montjuïc (15.27), Sant Martí (15.23) and
-- Gràcia (15.19) were very close behind, showing that strong recent
-- activity is not limited to the district with the largest supply.
-- ============================================================

WITH latest_review AS (
    SELECT
        MAX(review_date) AS latest_date
    FROM reviews),

recent_reviews AS (
    SELECT
        r.listing_id,
        COUNT(*) AS recent_review_count
    FROM reviews AS r
    CROSS JOIN latest_review AS d
    WHERE r.review_date >= DATE(d.latest_date, '-12 months')
    GROUP BY r.listing_id)

SELECT
    loc.district_name,
    COUNT(l.listing_id) AS listings,
    COALESCE(SUM(rr.recent_review_count), 0) AS recent_reviews,

    ROUND(
        COALESCE(SUM(rr.recent_review_count), 0) * 1.0
        / COUNT(l.listing_id),
        2) AS recent_reviews_per_listing,

    SUM(
        CASE
            WHEN COALESCE(rr.recent_review_count, 0) > 0
            THEN 1
            ELSE 0
        END) AS listings_with_recent_reviews,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN COALESCE(rr.recent_review_count, 0) > 0
                THEN 1
                ELSE 0
            END
        )
        / COUNT(l.listing_id),
        2) AS pct_listings_with_recent_reviews

FROM listings AS l
JOIN locations AS loc
    ON l.location_id = loc.location_id
LEFT JOIN recent_reviews AS rr
    ON l.listing_id = rr.listing_id

GROUP BY loc.district_name
ORDER BY recent_reviews_per_listing DESC;



-- ============================================================
-- QUERY 4
-- Research question:
-- Do the modelled occupancy and revenue indicators support the
-- picture shown by recent review activity?
--
-- Purpose:
-- Compare the estimated occupancy and revenue fields by district.
--
-- Important:
-- These are modelled indicators rather than observed bookings
-- or actual revenue, so they are supporting evidence only.
--
-- Finding:
-- The modelled indicators broadly support the recent-review picture,
-- although the ordering is not identical. Sants-Montjuïc had the
-- highest average estimated occupancy at 98.5, while Eixample had
-- the highest average estimated revenue at €28,530.62.
-- These figures are used as supporting evidence only because they
-- are modelled rather than observed bookings or revenue.
-- ============================================================

SELECT
    loc.district_name,
    COUNT(l.listing_id) AS listings,

    ROUND(
        AVG(l.estimated_occupancy_l365d),
        1) AS avg_estimated_occupancy,

    ROUND(
        AVG(l.estimated_revenue_l365d),
        2) AS avg_estimated_revenue,

    COUNT(
        l.estimated_revenue_l365d) AS listings_with_revenue_estimate

FROM listings AS l
JOIN locations AS loc
    ON l.location_id = loc.location_id

GROUP BY loc.district_name
ORDER BY avg_estimated_occupancy DESC;



-- ============================================================
-- QUERY 5
-- Research question:
-- Which districts have the highest concentration of supply
-- controlled by hosts with multiple listings?
--
-- Purpose:
-- First calculate each host's total Barcelona portfolio.
-- Then measure how much of each district's supply belongs to
-- hosts who operate more than one listing.
--
-- Finding:
-- Multi-listing hosts control the majority of Airbnb supply in every
-- district. Concentration was highest in Eixample at 86.08% and
-- lowest in Horta-Guinardó at 64.25%. Sant Martí was lower than
-- Eixample at 71.45%, despite having strong price and activity signals.
-- ============================================================

WITH host_portfolio AS (
    SELECT
        host_id,
        COUNT(*) AS total_listings
    FROM listings
    GROUP BY host_id)

SELECT
    loc.district_name,

    COUNT(l.listing_id) AS district_listings,

    COUNT(
        DISTINCT l.host_id) AS distinct_hosts,

    ROUND(
        COUNT(l.listing_id) * 1.0
        / COUNT(DISTINCT l.host_id),
        2) AS listings_per_host,

    COUNT(
        DISTINCT CASE
            WHEN hp.total_listings > 1
            THEN l.host_id
        END) AS multi_listing_hosts,

    ROUND(
        100.0 *
        COUNT(
            DISTINCT CASE
                WHEN hp.total_listings > 1
                THEN l.host_id
            END)
        / COUNT(DISTINCT l.host_id),
        2) AS pct_hosts_with_multiple_listings,

    SUM(
        CASE
            WHEN hp.total_listings > 1
            THEN 1
            ELSE 0
        END) AS listings_from_multi_listing_hosts,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN hp.total_listings > 1
                THEN 1
                ELSE 0
            END)
            / COUNT(l.listing_id),2) AS pct_listings_from_multi_listing_hosts

FROM listings AS l
JOIN locations AS loc
    ON l.location_id = loc.location_id
JOIN host_portfolio AS hp
    ON l.host_id = hp.host_id

GROUP BY loc.district_name
ORDER BY pct_listings_from_multi_listing_hosts DESC;



-- ============================================================
-- QUERY 6
-- Research question:
-- Who are the largest multi-listing hosts in the Barcelona
-- dataset and how widely are their listings spread?
--
-- Purpose:
-- Look more closely at the competitive landscape behind the
-- district-level concentration figures.
--
-- Only hosts with at least 10 listings are shown so the result
-- focuses on the larger portfolios.
--
-- Finding:
-- The largest host portfolios are substantial and spread across
-- several districts. Ukio had 588 listings across 7 districts,
-- Acomodis Apartments had 448 across 6, and Silvia De Lourdes had
-- 359 listings across all 10 districts. This helps explain why
-- multi-listing hosts account for such a large share of supply.
-- ============================================================

SELECT
    h.host_id,
    h.host_name,

    COUNT(l.listing_id) AS total_listings,

    COUNT(
        DISTINCT loc.district_name) AS districts_present,

    SUM(
        CASE
            WHEN l.room_type = 'Entire home/apt'
            THEN 1
            ELSE 0
        END) AS entire_home_listings,

    ROUND(
        AVG(l.price),
        2) AS avg_nightly_price

FROM hosts AS h
JOIN listings AS l
    ON h.host_id = l.host_id
JOIN locations AS loc
    ON l.location_id = loc.location_id

GROUP BY
    h.host_id,
    h.host_name

HAVING COUNT(l.listing_id) >= 10

ORDER BY total_listings DESC
LIMIT 20;



-- ============================================================
-- QUERY 7
-- Overall investor view
--
-- Purpose:
-- Bring the three main parts of the analysis together:
-- median asking price, recent review activity per listing,
-- and the percentage of supply belonging to multi-listing hosts.
--
-- This is not an investment recommendation. It gives a single
-- district-level view of the evidence so areas can be selected
-- for further investigation.
--
-- Finding:
-- Eixample has the strongest combined headline signal, ranking highest
-- for median asking price (€229) and recent activity (15.96 reviews
-- per listing), but 86.08% of its supply belongs to multi-listing hosts.
-- Sant Martí remains close on price (€206.50) and activity (15.23)
-- with materially lower concentration at 71.45%, making the trade-off
-- between market strength and competitive concentration clear.
-- ============================================================

WITH ranked_prices AS (
    SELECT
        loc.district_name,
        l.price,

        ROW_NUMBER() OVER (
            PARTITION BY loc.district_name
            ORDER BY l.price) AS row_num,

        COUNT(*) OVER (
            PARTITION BY loc.district_name) AS group_size

    FROM listings AS l
    JOIN locations AS loc
        ON l.location_id = loc.location_id

    WHERE l.price IS NOT NULL),

price_metrics AS (
    SELECT
        district_name,
        ROUND(AVG(price), 2) AS median_nightly_price
    FROM ranked_prices
    WHERE row_num IN (
        CAST((group_size + 1) / 2 AS INTEGER),
        CAST((group_size + 2) / 2 AS INTEGER))
    GROUP BY district_name),

latest_review AS (
    SELECT
        MAX(review_date) AS latest_date
    FROM reviews),

recent_reviews AS (
    SELECT
        r.listing_id,
        COUNT(*) AS recent_review_count
    FROM reviews AS r
    CROSS JOIN latest_review AS d
    WHERE r.review_date >= DATE(d.latest_date, '-12 months')
    GROUP BY r.listing_id),

activity_metrics AS (
    SELECT
        loc.district_name,

        COUNT(l.listing_id) AS listings,

        ROUND(
            COALESCE(SUM(rr.recent_review_count), 0) * 1.0
            / COUNT(l.listing_id),
            2
        ) AS recent_reviews_per_listing

    FROM listings AS l
    JOIN locations AS loc
        ON l.location_id = loc.location_id
    LEFT JOIN recent_reviews AS rr
        ON l.listing_id = rr.listing_id

    GROUP BY loc.district_name),

host_portfolio AS (
    SELECT
        host_id,
        COUNT(*) AS total_listings
    FROM listings
    GROUP BY host_id),

competition_metrics AS (
    SELECT
        loc.district_name,

        COUNT(
            DISTINCT l.host_id
        ) AS distinct_hosts,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN hp.total_listings > 1
                    THEN 1
                    ELSE 0
                END
            )
            / COUNT(l.listing_id),
            2
        ) AS pct_listings_from_multi_listing_hosts

    FROM listings AS l
    JOIN locations AS loc
        ON l.location_id = loc.location_id
    JOIN host_portfolio AS hp
        ON l.host_id = hp.host_id

    GROUP BY loc.district_name)

SELECT
    p.district_name,
    a.listings,
    p.median_nightly_price,
    a.recent_reviews_per_listing,
    c.distinct_hosts,
    c.pct_listings_from_multi_listing_hosts

FROM price_metrics AS p
JOIN activity_metrics AS a
    ON p.district_name = a.district_name
JOIN competition_metrics AS c
    ON p.district_name = c.district_name

ORDER BY p.median_nightly_price DESC;





