# ETL & Data Synchronisation Decision

## Source of Truth
PostgreSQL is the authoritative database for all core transactional data.

MongoDB is derived from PostgreSQL using a controlled ETL process.

---

## Why Not Real-Time Synchronisation?
Real-time synchronisation introduces:
- Increased complexity
- Transaction coordination challenges
- Operational overhead
- Infrastructure requirements (e.g. CDC, message brokers)

These were intentionally avoided to keep the project focused on database design and analytics.

---

## Chosen Approach
A one-time, re-runnable ETL script is used to:
1. Extract data from PostgreSQL
2. Transform relational data into documents
3. Load documents into MongoDB

This mirrors common real-world architectures.

---

## Benefits
- Simplicity
- Reproducibility
- Clear separation of concerns
- Easy to explain in interviews
