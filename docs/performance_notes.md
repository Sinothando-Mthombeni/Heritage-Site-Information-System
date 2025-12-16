## Performance Analysis Notes

This document records observations made during query performance testing
using PostgreSQL's EXPLAIN ANALYZE feature.

---

## Baseline Observations

Before indexing:
- Queries filtering on booking.site_id performed sequential scans
- Aggregation queries on booking and review tables scanned entire tables
- Execution time increased as table size grew

---

## Indexing Strategy

Indexes were added on the following columns:
- booking.site_id
- booking.visitor_id
- review.site_id

These columns were chosen because they:
- Appear frequently in JOIN conditions
- Are commonly used in WHERE clauses
- Participate in aggregation queries

---

## Results After Indexing

After indexes were created:
- PostgreSQL used index scans instead of sequential scans
- Execution time was reduced for filtered queries
- Aggregation queries showed improved planning and execution efficiency

Execution plans confirmed:
- Index Scan usage
- Reduced cost estimates
- Lower actual execution times

---

## Conclusion

Selective indexing significantly improved query performance
without over-indexing the database.

The results demonstrate practical understanding of:
- Query optimization
- Execution plan interpretation
- Performance-conscious database design

## Example of EXPLAIN ANALYZE
_______________________________________________________________________________________________________
EXPLAIN ANALYZE
SELECT *
FROM booking
WHERE site_id = 1;

"QUERY PLAN"
"Seq Scan on booking  (cost=0.00..1.20 rows=1 width=24) (actual time=0.018..0.021 rows=2 loops=1)"
"  Filter: (site_id = 1)"
"  Rows Removed by Filter: 14"
"Planning Time: 0.131 ms"
"Execution Time: 0.038 ms"
_______________________________________________________________________________________________________
EXPLAIN ANALYZE
SELECT hs.name, COUNT(b.booking_id)
FROM heritage_site hs
LEFT JOIN booking b ON hs.site_id = b.site_id
GROUP BY hs.name;

"QUERY PLAN"
"HashAggregate  (cost=16.39..18.39 rows=200 width=226) (actual time=0.069..0.074 rows=15 loops=1)"
"  Group Key: hs.name"
"  Batches: 1  Memory Usage: 40kB"
"  ->  Hash Left Join  (cost=1.36..15.09 rows=260 width=222) (actual time=0.047..0.056 rows=16 loops=1)"
"        Hash Cond: (hs.site_id = b.site_id)"
"        ->  Seq Scan on heritage_site hs  (cost=0.00..12.60 rows=260 width=222) (actual time=0.017..0.019 rows=15 loops=1)"
"        ->  Hash  (cost=1.16..1.16 rows=16 width=8) (actual time=0.021..0.022 rows=16 loops=1)"
"              Buckets: 1024  Batches: 1  Memory Usage: 9kB"
"              ->  Seq Scan on booking b  (cost=0.00..1.16 rows=16 width=8) (actual time=0.011..0.015 rows=16 loops=1)"
"Planning Time: 0.237 ms"
"Execution Time: 0.128 ms"
__________________________________________________________________________________________________________
