# Phase 3 – NoSQL (MongoDB)

## Overview
This phase introduces MongoDB as a NoSQL database to complement the existing PostgreSQL relational database used in earlier phases.

MongoDB is not treated as a primary system of record. Instead, it is used for:
- Flexible document storage
- Read-heavy workloads
- Analytics and aggregation
- Data denormalisation use cases

PostgreSQL remains the source of truth.

---

## Database Used
- MongoDB
- Database name: `heritage_phase3`

---

## Collections
### 1. heritage_sites
Stores heritage site information enriched with MongoDB-specific fields.

Example fields:
- site_id
- name
- province
- category
- ticket_price
- reviews (embedded documents)

### 2. bookings
Stores booking data optimised for analytics.

Example fields:
- booking_id
- site_id
- site_name
- province
- visitors
- booking_date

---

## Design Principles
- Denormalisation is intentional
- Data is duplicated to optimise query performance
- Schema is driven by query patterns, not normalisation
- MongoDB handles analytics and flexible data
