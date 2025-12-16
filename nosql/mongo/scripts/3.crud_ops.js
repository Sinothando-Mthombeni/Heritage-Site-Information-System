const db = db.getSiblingDB("heritage_phase3");

// ---------------------
// CREATE (Mongo-only data)
// ---------------------
db.heritage_sites.updateOne(
  { site_id: "HS001" },
  {
    $push: {
      reviews: {
        user: "Naledi",
        comment: "Very informative tour",
        stars: 5
      }
    }
  }
);

// ---------------------
// READ
// ---------------------
db.heritage_sites.find({ province: "Western Cape" });

// ---------------------
// UPDATE
// ---------------------
db.heritage_sites.updateOne(
  { site_id: "HS002" },
  { $set: { ticket_price: 300 } }
);

// ---------------------
// DELETE
// ---------------------
db.bookings.deleteOne({ booking_id: "B999" });
