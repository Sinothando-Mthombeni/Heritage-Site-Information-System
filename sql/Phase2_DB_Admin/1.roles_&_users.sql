-- Read-only role
CREATE ROLE heritage_readonly;

-- Read-write role
CREATE ROLE heritage_rw;

-- Admin role
CREATE ROLE heritage_admin;

-- Create users
CREATE USER analyst_user WITH PASSWORD 'analyst123';
CREATE USER app_user WITH PASSWORD 'app123';
CREATE USER admin_user WITH PASSWORD 'admin123';

-- Assign roles
GRANT heritage_readonly TO analyst_user;
GRANT heritage_rw TO app_user;
GRANT heritage_admin TO admin_user;
