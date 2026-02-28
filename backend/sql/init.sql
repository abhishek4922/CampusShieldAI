-- ============================================================
-- CampusShield AI — PostgreSQL Initialisation
-- Run automatically by Docker on first boot.
-- Creates schema and extensions.
-- Tables are managed by Alembic migrations.
-- ============================================================

-- UUID generation support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS campusshield;

-- Grant permissions to app user
GRANT ALL PRIVILEGES ON SCHEMA campusshield TO campusshield_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA campusshield
    GRANT ALL ON TABLES TO campusshield_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA campusshield
    GRANT ALL ON SEQUENCES TO campusshield_user;
