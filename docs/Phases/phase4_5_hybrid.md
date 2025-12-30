# Phase 4.5 – Hybrid SQL & NoSQL Strategy

## Objective
Demonstrate real-world hybrid persistence using both PostgreSQL and MongoDB.

## Responsibility Split
| Concern | Database |
|------|---------|
| Transactions | PostgreSQL |
| Reporting | PostgreSQL |
| Analytics | MongoDB |
| Flexible Metadata | MongoDB |

## Data Flow
- PostgreSQL remains the source of truth
- MongoDB stores derived or duplicated data
- Synchronization handled manually (intentional)

## Trade-offs
- No real-time sync
- Some data duplication
- Simpler architecture over complexity

## Outcome
A pragmatic, realistic hybrid data architecture.
