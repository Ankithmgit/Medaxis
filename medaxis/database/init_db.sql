-- Run this once in psql as superuser to set up the database

CREATE USER medaxis WITH PASSWORD 'medaxis123';
CREATE DATABASE medaxis_db OWNER medaxis;
GRANT ALL PRIVILEGES ON DATABASE medaxis_db TO medaxis;

-- Connect to medaxis_db and grant schema access
\c medaxis_db
GRANT ALL ON SCHEMA public TO medaxis;
