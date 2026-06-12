-- Run this once in your Supabase SQL editor.
-- SQLAlchemy create_all does not add indexes to existing tables,
-- so this brings the live DB in sync with models.py.

CREATE INDEX IF NOT EXISTS ix_brands_created_at          ON brands (created_at);
CREATE INDEX IF NOT EXISTS ix_leads_brand_id             ON leads  (brand_id);
CREATE INDEX IF NOT EXISTS ix_leads_created_at           ON leads  (created_at);
CREATE INDEX IF NOT EXISTS ix_leads_status_first_contact ON leads  (status, first_contact_at);
CREATE INDEX IF NOT EXISTS ix_shoots_brand_id            ON shoots (brand_id);
CREATE INDEX IF NOT EXISTS ix_shoots_shoot_date          ON shoots (shoot_date);
CREATE INDEX IF NOT EXISTS ix_shoots_created_at          ON shoots (created_at);
