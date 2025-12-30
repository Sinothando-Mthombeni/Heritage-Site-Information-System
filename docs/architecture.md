## System Architecture

- PostgreSQL: transactional system of record
- MongoDB: read-optimised analytics store
- Django: application layer coordinating both

Write operations:
Django → PostgreSQL → ETL → MongoDB

Read operations:
Django → MongoDB (analytics)
Django → PostgreSQL (transactions)
