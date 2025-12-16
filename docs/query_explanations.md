# SQL Query Explanations

This document explains the intent behind the SQL queries used
in Phase 2 of the Heritage Sites database project.

The focus is on **why** specific SQL constructs were used.

---

## 1. Basic Selects and Joins

Basic SELECT queries combined with JOINs are used to:
- Combine normalized data across multiple tables
- Present user-friendly results such as site names, provinces, and categories

These queries validate that:
- Foreign key relationships are correct
- The schema supports meaningful data retrieval

---

## 2. Aggregations and Grouping

Aggregation queries using COUNT, SUM, and AVG answer questions such as:
- Which heritage sites receive the most bookings
- Which provinces sell the most tickets
- What the average rating is per site

GROUP BY is used to summarize data at different business levels
(e.g., per site or per province).

---

## 3. Subqueries

Subqueries are used to:
- Filter entities based on aggregated conditions
- Identify records that do not exist in related tables (e.g., sites with no bookings)

This demonstrates understanding of nested query logic and data filtering.

---

## 4. Common Table Expressions (CTEs)

CTEs are used to:
- Improve query readability
- Break complex logic into logical steps

For example, booking counts are calculated first and then reused
to determine the most popular site per province.

CTEs make analytical SQL easier to maintain and understand.

---

## 5. Window Functions

Window functions are used to:
- Rank heritage sites by popularity
- Calculate running totals without collapsing result sets

Functions such as RANK() and SUM() OVER() enable advanced analytics
that cannot be achieved with simple GROUP BY queries.

---

## 6. Data Quality Checks

Queries are included to detect:
- Reviews that do not have corresponding bookings

This demonstrates awareness of data integrity and validation beyond constraints.
