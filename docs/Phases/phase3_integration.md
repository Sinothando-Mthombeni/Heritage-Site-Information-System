# Phase 3 – Django & PostgreSQL Integration

## Objective
Integrate the PostgreSQL database with Django, enabling structured access to relational data
through services and ORM abstraction.

## Integration Approach
- Django ORM maps relational tables to models
- Environment variables manage credentials
- Migrations ensure schema consistency

## Configuration
- psycopg2 used as PostgreSQL driver
- dotenv for secure environment loading
- Separation of settings from code

## Access Patterns
- Read-heavy queries optimized via raw SQL
- Write operations handled via ORM
- Services layer abstracts database logic

## Outcome
Django acts as the orchestration layer while PostgreSQL remains the authoritative data store.
