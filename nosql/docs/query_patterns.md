# MongoDB Query Patterns

## Common Queries
- Find heritage sites by province
- Aggregate total visitors per site
- Aggregate visitors per province
- Calculate average review ratings

---

## Why MongoDB?
These queries:
- Do not require strict joins
- Benefit from embedded documents
- Are read-heavy
- Benefit from aggregation pipelines

MongoDB handles these efficiently compared to relational joins.

---

## Examples
- `$group` for aggregations
- `$unwind` for embedded arrays
- Indexed filtering on province and site_id
