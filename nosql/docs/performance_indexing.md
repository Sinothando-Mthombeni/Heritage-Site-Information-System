# Performance & Indexing

## Indexing Strategy
Indexes are created based on query frequency and access patterns.

### heritage_sites
- province
- site_id

### bookings
- booking_date
- site_id

---

## Performance Considerations
- Indexes improve read performance
- Write performance impact is acceptable due to read-heavy usage
- Indexes align with aggregation and filter operations

---

## Verification
Indexes can be listed using:
