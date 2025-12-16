# Database Setup Instructions

## Database Engine
PostgreSQL

## Database Name
heritage_site_p2

## Tools Used
- PostgreSQL
- pgAdmin
- Visual Studio Code
- GitHub

## Setup Procedure

1. Create a PostgreSQL database named:
   heritage_site_p2

2. Connect to the database using pgAdmin.

3. Execute SQL scripts in the following order:
   1. schema.sql
   2. sample_data.sql
   3. queries.sql
   4. indexes.sql
   5. explain_analyze.sql

## Notes
- All SQL scripts are written in VS Code and executed via pgAdmin.
- The scripts are idempotent where possible and designed for repeatable execution.
- No database creation or deletion logic is embedded in the schema scripts.
