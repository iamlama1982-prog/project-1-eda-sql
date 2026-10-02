PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS listings;
DROP TABLE IF EXISTS hosts;
DROP TABLE IF EXISTS locations;

CREATE TABLE locations (
    location_id INTEGER PRIMARY KEY,
    neighbourhood_name TEXT NOT NULL,
    district_name TEXT NOT NULL);

CREATE TABLE hosts (
    host_id INTEGER PRIMARY KEY,
    host_name TEXT,
    host_is_superhost TEXT);

CREATE TABLE listings (
    listing_id INTEGER PRIMARY KEY,
    host_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    accommodates INTEGER NOT NULL,
    price REAL,
    minimum_nights INTEGER,
    number_of_reviews INTEGER NOT NULL,
    estimated_occupancy_l365d REAL,
    estimated_revenue_l365d REAL,
    FOREIGN KEY (host_id) REFERENCES hosts(host_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id));

CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY,
    listing_id INTEGER NOT NULL,
    review_date TEXT NOT NULL,
    FOREIGN KEY (listing_id) REFERENCES listings(listing_id));