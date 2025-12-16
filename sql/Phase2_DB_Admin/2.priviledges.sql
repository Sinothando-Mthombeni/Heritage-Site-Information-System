-- Read-only permissions
GRANT CONNECT ON DATABASE heritage_site_p2 TO heritage_readonly;
GRANT USAGE ON SCHEMA public TO heritage_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO heritage_readonly;

-- Read-write permissions
GRANT CONNECT ON DATABASE heritage_site_p2 TO heritage_rw;
GRANT USAGE ON SCHEMA public TO heritage_rw;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO heritage_rw;

-- Admin permissions
GRANT ALL PRIVILEGES ON DATABASE heritage_site_p2 TO heritage_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO heritage_admin;
