// ================================
// Phase 3 - MongoDB Setup
// Database: heritage_phase3
// ================================

const db = db.getSiblingDB("heritage_phase3");

db.createCollection("heritage_sites");
db.createCollection("bookings");
