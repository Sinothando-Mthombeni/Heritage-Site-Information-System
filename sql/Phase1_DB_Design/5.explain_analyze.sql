-- =========================================
-- EXPLAIN ANALYZE: Performance Demonstrations
-- =========================================

-- Booking lookup by site (uses index)
EXPLAIN ANALYZE
SELECT *
FROM booking
WHERE site_id = 1;


-- Aggregation performance on bookings per site
EXPLAIN ANALYZE
SELECT
    hs.name,
    COUNT(b.booking_id)
FROM heritage_site hs
LEFT JOIN booking b ON hs.site_id = b.site_id
GROUP BY hs.name;


-- Review aggregation performance
EXPLAIN ANALYZE
SELECT
    site_id,
    AVG(rating)
FROM review
GROUP BY site_id;
