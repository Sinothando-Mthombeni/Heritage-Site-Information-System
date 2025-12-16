-- =========================================
-- Isolation Levels Demonstration
-- Phase 2
-- =========================================

-- READ COMMITTED (default)
BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED;

SELECT * FROM booking WHERE site_id = 1;

COMMIT;

-- SERIALIZABLE
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;

SELECT COUNT(*) FROM booking;

COMMIT;
