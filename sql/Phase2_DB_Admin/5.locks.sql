-- =========================================
-- Locks Demonstration
-- Phase 2
-- =========================================

-- 1️⃣ Row-level lock example
BEGIN;

UPDATE heritage_site
SET entry_fee = entry_fee + 20
WHERE site_id = 3;

-- Do not commit immediately (simulate lock)
-- Open another session to test concurrent access

COMMIT;

-- 2️⃣ Another lock example
BEGIN;

SELECT * FROM booking
WHERE site_id = 3
FOR UPDATE;

COMMIT;
