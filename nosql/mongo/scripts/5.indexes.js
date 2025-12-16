const db = db.getSiblingDB("heritage_phase3");

// Frequently filtered fields
db.heritage_sites.createIndex({ province: 1 });
db.heritage_sites.createIndex({ site_id: 1 });

// Analytics performance
db.bookings.createIndex({ booking_date: 1 });
db.bookings.createIndex({ site_id: 1 });
