-- =========================================
-- Transactions Demonstration
-- Phase 2
-- =========================================

-- 1️⃣ Example: Rollback a transaction (simulate failure)
BEGIN;

INSERT INTO booking (site_id, visitor_id, booking_date, number_of_tickets)
VALUES (1, 1, CURRENT_DATE, 5);

-- Simulate an error
ROLLBACK;

-- 2️⃣ Example: Commit a successful transaction
BEGIN;

INSERT INTO booking (site_id, visitor_id, booking_date, number_of_tickets)
VALUES (1, 1, CURRENT_DATE, 3);

COMMIT;

-- 3️⃣ Example: Multiple operations in one transaction
BEGIN;

UPDATE heritage_site
SET entry_fee = entry_fee + 10
WHERE site_id = 2;

INSERT INTO review (visitor_id, site_id, rating, comment)
VALUES (2, 2, 5, 'Excellent site!');

COMMIT;
