# Phase 2 – PostgreSQL Implementation

## Objective
Design and implement a normalized relational database for South African heritage sites,
demonstrating strong SQL fundamentals, performance awareness, and transactional integrity.

## Schema Overview
The PostgreSQL schema models:
- Heritage Sites
- Provinces & Locations
- Site Categories
- Bookings
- Visitors

The design follows Third Normal Form (3NF) to avoid redundancy and ensure data integrity.

## Key Features Implemented
- Primary & foreign key constraints
- CHECK constraints for data validation
- Composite and single-column indexes
- Aggregation queries
- Common Table Expressions (CTEs)
- ACID-compliant transactions

## Example Operations
- Monthly booking summaries
- Most visited heritage sites
- Revenue per province
- Booking trends using window functions

## Performance Considerations
Indexes were created on:
- Foreign keys
- Frequently filtered columns
- Aggregation group-by columns

## Outcome
This phase establishes PostgreSQL as the system of record for transactional and structured data.
