-- =========================================
-- SQL Queries: Heritage Sites Database
-- PostgreSQL | Phase 2
-- =========================================


-- =========================================================
-- SECTION 1: BASIC SELECTS & JOINS
-- =========================================================

-- 1. List all heritage sites with their province and category
SELECT
    hs.name AS site_name,
    p.name  AS province,
    c.name  AS category
FROM heritage_site hs
JOIN province p ON hs.province_id = p.province_id
JOIN category c ON hs.category_id = c.category_id;


-- 2. List all bookings with visitor and site details
SELECT
    b.booking_id,
    v.first_name || ' ' || v.last_name AS visitor,
    hs.name AS site,
    b.visit_date,
    b.number_of_tickets
FROM booking b
JOIN visitor v ON b.visitor_id = v.visitor_id
JOIN heritage_site hs ON b.site_id = hs.site_id;


-- =========================================================
-- SECTION 2: AGGREGATIONS & GROUPING
-- =========================================================

-- 3. Total bookings per heritage site
SELECT
    hs.name,
    COUNT(b.booking_id) AS total_bookings
FROM heritage_site hs
LEFT JOIN booking b ON hs.site_id = b.site_id
GROUP BY hs.name
ORDER BY total_bookings DESC;


-- 4. Average rating per heritage site
SELECT
    hs.name,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM heritage_site hs
JOIN review r ON hs.site_id = r.site_id
GROUP BY hs.name;


-- 5. Total tickets sold per province
SELECT
    p.name AS province,
    SUM(b.number_of_tickets) AS tickets_sold
FROM booking b
JOIN heritage_site hs ON b.site_id = hs.site_id
JOIN province p ON hs.province_id = p.province_id
GROUP BY p.name
ORDER BY tickets_sold DESC;


-- =========================================================
-- SECTION 3: SUBQUERIES & FILTERING
-- =========================================================

-- 6. Heritage sites with no bookings
SELECT name
FROM heritage_site
WHERE site_id NOT IN (
    SELECT DISTINCT site_id FROM booking
);


-- 7. Visitors who have made more than one booking
SELECT first_name, last_name
FROM visitor
WHERE visitor_id IN (
    SELECT visitor_id
    FROM booking
    GROUP BY visitor_id
    HAVING COUNT(*) > 1
);


-- =========================================================
-- SECTION 4: COMMON TABLE EXPRESSIONS (CTEs)
-- =========================================================

-- 8. Booking count per site using CTE
WITH site_bookings AS (
    SELECT
        site_id,
        COUNT(*) AS booking_count
    FROM booking
    GROUP BY site_id
)
SELECT
    hs.name,
    sb.booking_count
FROM site_bookings sb
JOIN heritage_site hs ON sb.site_id = hs.site_id
ORDER BY sb.booking_count DESC;


-- 9. Top booked heritage site per province
WITH province_site_counts AS (
    SELECT
        p.name AS province,
        hs.name AS site,
        COUNT(b.booking_id) AS bookings
    FROM province p
    JOIN heritage_site hs ON p.province_id = hs.province_id
    LEFT JOIN booking b ON hs.site_id = b.site_id
    GROUP BY p.name, hs.name
)
SELECT *
FROM province_site_counts
WHERE bookings = (
    SELECT MAX(bookings)
    FROM province_site_counts p2
    WHERE p2.province = province_site_counts.province
);


-- =========================================================
-- SECTION 5: WINDOW FUNCTIONS
-- =========================================================

-- 10. Rank heritage sites by number of bookings
SELECT
    hs.name,
    COUNT(b.booking_id) AS bookings,
    RANK() OVER (ORDER BY COUNT(b.booking_id) DESC) AS popularity_rank
FROM heritage_site hs
LEFT JOIN booking b ON hs.site_id = b.site_id
GROUP BY hs.name;


-- 11. Running total of tickets sold (by booking date)
SELECT
    booking_date,
    SUM(number_of_tickets) AS daily_tickets,
    SUM(SUM(number_of_tickets)) OVER (ORDER BY booking_date) AS running_total
FROM booking
GROUP BY booking_date
ORDER BY booking_date;


-- =========================================================
-- SECTION 6: DATA QUALITY & INTEGRITY CHECKS
-- =========================================================

-- 12. Find reviews without corresponding bookings
SELECT r.review_id, r.visitor_id, r.site_id
FROM review r
LEFT JOIN booking b
    ON r.visitor_id = b.visitor_id
   AND r.site_id = b.site_id
WHERE b.booking_id IS NULL;
