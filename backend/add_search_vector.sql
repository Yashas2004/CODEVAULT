-- Add the column (safe if already added via SQLAlchemy create_all, but ensures it exists)
ALTER TABLE snippets ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- Populate it for existing rows, weighting title higher than tags/language
UPDATE snippets SET search_vector =
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(tags, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'C');

-- GIN index for fast search
CREATE INDEX IF NOT EXISTS idx_snippets_search ON snippets USING GIN(search_vector);

-- Trigger to auto-update search_vector whenever a row is inserted/updated
CREATE OR REPLACE FUNCTION snippets_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(NEW.tags, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(NEW.language, '')), 'C');
  RETURN NEW;
END
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS snippets_search_vector_trigger ON snippets;
CREATE TRIGGER snippets_search_vector_trigger
BEFORE INSERT OR UPDATE ON snippets
FOR EACH ROW EXECUTE FUNCTION snippets_search_vector_update();