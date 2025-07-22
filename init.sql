-- schema.sql

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL,
    password TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    zip_code TEXT NOT NULL,
    library_name TEXT NOT NULL
);

-- Authors table: unique authors
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Works table: a unique book title by an author
CREATE TABLE works (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT
);

-- Works-authors join table
CREATE TABLE work_authors (
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    PRIMARY KEY (author_id, work_id)
);

-- Editions table: specific published versions of a work (e.g., different ISBNs)
CREATE TABLE editions (
    id SERIAL PRIMARY KEY,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    isbn TEXT UNIQUE,
    publisher TEXT,
    published_date TEXT,
    edition_notes TEXT,
    thumbnail TEXT
);

-- User editions table: physical copy owned by a user
CREATE TABLE user_editions (
    id SERIAL PRIMARY KEY,
    edition_id INTEGER NOT NULL REFERENCES editions(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL, -- Foreign key if you have a users table
    condition TEXT,
    location TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(edition_id, user_id)
);

CREATE TABLE zip_locations (
    zip VARCHAR(10) PRIMARY KEY,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    city TEXT,
    state_id CHAR(2),
    state_name TEXT,
    zcta TEXT,
    parent_zcta TEXT,
    population TEXT,
    density TEXT,
    county_fips TEXT,
    county_name TEXT,
    county_weights TEXT,
    county_names_all TEXT,
    county_fips_all TEXT,
    imprecise TEXT,
    military TEXT,
    timezone TEXT
);
COPY zip_locations FROM '/tmp/uszips.csv' WITH CSV HEADER;

CREATE OR REPLACE FUNCTION haversine(
    lat1 DOUBLE PRECISION, lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION, lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
DECLARE
    r INTEGER := 3959; -- Earth radius in miles
    dlat DOUBLE PRECISION := radians(lat2 - lat1);
    dlon DOUBLE PRECISION := radians(lon2 - lon1);
    a DOUBLE PRECISION;
BEGIN
    a := sin(dlat / 2)^2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)^2;
    RETURN 2 * r * atan2(sqrt(a), sqrt(1 - a));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Borrow events (requested + accepted + active/returned)
CREATE TABLE borrows (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES user_editions(id) ON DELETE CASCADE,
    borrower_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    status TEXT NOT NULL CHECK (status IN (
        'requested',       -- borrower requested the book
        'approved',        -- lender approved but not picked up
        'borrowed',        -- book is in borrower’s possession
        'returned',        -- borrower returned the book
        'canceled'        -- request canceled by either party
    )),

    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    confirmed_at TIMESTAMP,     -- when lender confirmed the request
    borrowed_at TIMESTAMP,      -- when possession transferred
    due_date DATE,
    returned_at TIMESTAMP,

    renewal_count INTEGER NOT NULL DEFAULT 0,
    max_renewals INTEGER NOT NULL DEFAULT 2,

    UNIQUE (book_id) -- prevent concurrent borrows of same book
);