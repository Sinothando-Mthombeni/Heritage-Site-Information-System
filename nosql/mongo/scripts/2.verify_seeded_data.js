const db = db.getSiblingDB("heritage_phase3");

// List collections (JS-compatible)
db.getCollectionNames();

// Confirm record counts
db.heritage_sites.countDocuments();
db.bookings.countDocuments();

// Preview records
db.heritage_sites.find().limit(3).toArray();
db.bookings.find().limit(3).toArray();
