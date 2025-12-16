-- =========================================
-- Indexes for Query Performance
-- =========================================

-- Speeds up booking lookups per site
CREATE INDEX idx_booking_site_id
ON booking(site_id);

-- Speeds up visitor booking history queries
CREATE INDEX idx_booking_visitor_id
ON booking(visitor_id);

-- Speeds up rating aggregations per site
CREATE INDEX idx_review_site_id
ON review(site_id);
