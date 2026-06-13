-- Leapto university & programme portfolio (Phase A)
-- PostgreSQL 14+. Run: psql -f schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------------
-- Reference
-- ---------------------------------------------------------------------------

CREATE TABLE countries (
    id              SERIAL PRIMARY KEY,
    code            CHAR(2) NOT NULL UNIQUE,          -- ISO 3166-1 alpha-2
    name_en         TEXT NOT NULL,
    name_fa         TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    source_url      TEXT,
    last_verified_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE leapto_field_tags (
    id              SERIAL PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,             -- e.g. cs_data_science
    label_en        TEXT NOT NULL,
    label_fa        TEXT,
    leapto_category TEXT,                             -- maps to mentor homepage category
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Institutions & programmes
-- ---------------------------------------------------------------------------

CREATE TABLE universities (
    id              SERIAL PRIMARY KEY,
    country_id      INTEGER NOT NULL REFERENCES countries(id),
    name_en         TEXT NOT NULL,
    name_fa         TEXT,
    city_en         TEXT,
    ranking_band    TEXT,                             -- e.g. top100, top200, other
    website_url     TEXT,
    source_url      TEXT NOT NULL,
    last_verified_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (country_id, name_en)
);

CREATE TABLE programmes (
    id              SERIAL PRIMARY KEY,
    university_id   INTEGER NOT NULL REFERENCES universities(id),
    title_en        TEXT NOT NULL,
    title_fa        TEXT,
    degree_level    TEXT NOT NULL CHECK (degree_level IN ('Bachelor', 'Master', 'PhD')),
    field_tag_id    INTEGER REFERENCES leapto_field_tags(id),
    field_tags_extra TEXT[],                         -- secondary tags
    programme_url   TEXT NOT NULL,
    duration_months INTEGER,
    delivery_mode   TEXT,                             -- on_campus, online, hybrid
    source_url      TEXT NOT NULL,
    last_verified_at TIMESTAMPTZ,
    requirements_confidence TEXT NOT NULL DEFAULT 'medium'
        CHECK (requirements_confidence IN ('high', 'medium', 'low')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (university_id, title_en, degree_level)
);

CREATE TABLE programme_requirements (
    id                      SERIAL PRIMARY KEY,
    programme_id            INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    min_ielts_overall       NUMERIC(2,1),
    min_toefl_ibt            INTEGER,
    min_gpa_4                NUMERIC(3,2),
    min_gpa_20               NUMERIC(4,2),
    gre_required             BOOLEAN,
    gmat_required            BOOLEAN,
    work_experience_years_min NUMERIC(3,1),
    entry_notes_en           TEXT,
    entry_notes_fa           TEXT,
    source_url               TEXT NOT NULL,
    last_verified_at         TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (programme_id)
);

CREATE TABLE programme_costs (
    id              SERIAL PRIMARY KEY,
    programme_id    INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    academic_year   TEXT NOT NULL,                    -- e.g. 2025/26
    tuition_amount  NUMERIC(12,2) NOT NULL,
    currency        CHAR(3) NOT NULL DEFAULT 'GBP',
    living_cost_estimate NUMERIC(12,2),
    source_url      TEXT NOT NULL,
    last_verified_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (programme_id, academic_year)
);

CREATE TABLE intakes (
    id              SERIAL PRIMARY KEY,
    programme_id    INTEGER NOT NULL REFERENCES programmes(id) ON DELETE CASCADE,
    start_term      TEXT NOT NULL,                    -- e.g. September 2026
    application_deadline DATE,
    is_rolling      BOOLEAN NOT NULL DEFAULT FALSE,
    source_url      TEXT NOT NULL,
    last_verified_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_programmes_degree ON programmes(degree_level) WHERE is_active;
CREATE INDEX idx_programmes_field ON programmes(field_tag_id) WHERE is_active;
CREATE INDEX idx_universities_country ON universities(country_id) WHERE is_active;
CREATE INDEX idx_intakes_deadline ON intakes(application_deadline);

COMMIT;
