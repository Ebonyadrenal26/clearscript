-- clearscript terminology library schema (v0.0.1)
--
-- Storage philosophy: SQLite as canonical store, markdown views as exports.
-- The schema is designed for the v0.1 features even where the v0.0.1 code
-- only exercises a subset, so that future migrations stay additive.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- Schema version for future migrations
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('version', '1');

-- 1. Terms: companies, products, acronyms, jargon, etc.
CREATE TABLE IF NOT EXISTS terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical TEXT NOT NULL,
    type TEXT,                         -- company / product / acronym / jargon / person
    domain TEXT,                       -- vc / ai-infra / medical / null = universal
    definition TEXT,
    notes TEXT,
    status TEXT NOT NULL DEFAULT 'proposed',  -- proposed / confirmed / verified / disputed / deprecated
    confidence REAL NOT NULL DEFAULT 0.5,
    confirm_count INTEGER NOT NULL DEFAULT 0,
    reject_count INTEGER NOT NULL DEFAULT 0,
    times_used INTEGER NOT NULL DEFAULT 0,
    scope TEXT NOT NULL DEFAULT 'library',    -- library / project:<slug>
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    UNIQUE (canonical, scope)
);
CREATE INDEX IF NOT EXISTS idx_terms_canonical ON terms(canonical);
CREATE INDEX IF NOT EXISTS idx_terms_domain ON terms(domain, status);
CREATE INDEX IF NOT EXISTS idx_terms_used ON terms(last_used_at DESC);

-- 2. Aliases: many-to-one with terms, this is the table you hit on every chunk
CREATE TABLE IF NOT EXISTS term_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term_id INTEGER NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    alias_type TEXT,                    -- asr-error / abbreviation / nickname / variant
    seen_count INTEGER NOT NULL DEFAULT 1,
    last_seen_at TIMESTAMP,
    UNIQUE (term_id, alias)
);
CREATE INDEX IF NOT EXISTS idx_aliases_lookup ON term_aliases(alias);

-- 3. Speakers
CREATE TABLE IF NOT EXISTS speakers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_name TEXT NOT NULL,
    display_label TEXT NOT NULL,        -- "Siqi：" / "Eileen："
    primary_language TEXT,              -- zh / en / mixed
    style_fingerprint TEXT,             -- JSON
    notes TEXT,
    confidence REAL NOT NULL DEFAULT 0.5,
    times_seen INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (canonical_name)
);

CREATE TABLE IF NOT EXISTS speaker_aliases (
    speaker_id INTEGER NOT NULL REFERENCES speakers(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    PRIMARY KEY (speaker_id, alias)
);
CREATE INDEX IF NOT EXISTS idx_speaker_aliases ON speaker_aliases(alias);

-- 4. Organizations
CREATE TABLE IF NOT EXISTS orgs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical TEXT,
    canonical_zh TEXT,
    org_type TEXT,                      -- vc / startup / public / lab / ngo
    industry TEXT,
    website TEXT,
    notes TEXT
);

-- 5. Speaker ↔ Org with time
CREATE TABLE IF NOT EXISTS affiliations (
    speaker_id INTEGER NOT NULL REFERENCES speakers(id) ON DELETE CASCADE,
    org_id INTEGER NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    role TEXT,
    start_year INTEGER,
    end_year INTEGER,
    PRIMARY KEY (speaker_id, org_id, role, start_year)
);

-- 6. Edit patterns (user preferences)
CREATE TABLE IF NOT EXISTS edit_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    trigger_desc TEXT,
    action TEXT,
    rationale TEXT,
    domain TEXT,
    confirmed_count INTEGER NOT NULL DEFAULT 1,
    last_applied_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. Sessions
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_slug TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    provider TEXT,
    model TEXT,
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0.0,
    domains TEXT,                       -- JSON list
    status TEXT NOT NULL DEFAULT 'running',   -- running / paused / complete / failed
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_slug);

-- 8. Applied corrections (link sessions ↔ terms)
CREATE TABLE IF NOT EXISTS applied_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    term_id INTEGER REFERENCES terms(id),
    chunk_position INTEGER,
    original_text TEXT,
    corrected_text TEXT,
    layer TEXT,
    confidence REAL,
    user_action TEXT,                   -- accepted / rejected / modified / pending
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 9. Negative list: explicit "do not change" rules
CREATE TABLE IF NOT EXISTS negative_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    do_not_change_to TEXT,              -- NULL = don't change at all
    domain TEXT,
    reason TEXT,
    source_session_id INTEGER REFERENCES sessions(id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (text, do_not_change_to, domain)
);

-- 10. FTS5 index for free-text term search
CREATE VIRTUAL TABLE IF NOT EXISTS terms_fts USING fts5(
    canonical, definition, notes,
    content='terms', content_rowid='id', tokenize='unicode61'
);

-- 11. Pack membership tracking
CREATE TABLE IF NOT EXISTS pack_membership (
    term_id INTEGER NOT NULL REFERENCES terms(id) ON DELETE CASCADE,
    pack_name TEXT NOT NULL,
    pack_version TEXT,
    PRIMARY KEY (term_id, pack_name)
);

-- Trigger to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS terms_ai AFTER INSERT ON terms BEGIN
    INSERT INTO terms_fts(rowid, canonical, definition, notes)
    VALUES (new.id, new.canonical, new.definition, new.notes);
END;
CREATE TRIGGER IF NOT EXISTS terms_ad AFTER DELETE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, canonical, definition, notes)
    VALUES ('delete', old.id, old.canonical, old.definition, old.notes);
END;
CREATE TRIGGER IF NOT EXISTS terms_au AFTER UPDATE ON terms BEGIN
    INSERT INTO terms_fts(terms_fts, rowid, canonical, definition, notes)
    VALUES ('delete', old.id, old.canonical, old.definition, old.notes);
    INSERT INTO terms_fts(rowid, canonical, definition, notes)
    VALUES (new.id, new.canonical, new.definition, new.notes);
END;
