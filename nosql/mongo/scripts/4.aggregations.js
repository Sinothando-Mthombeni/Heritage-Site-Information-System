const db = db.getSiblingDB("heritage_phase3");

// -----------------------------
// Total visitors per site
// -----------------------------
db.bookings.aggregate([
  {
    $group: {
      _id: "$site_name",
      total_visitors: { $sum: "$visitors" }
    }
  }
]);

// -----------------------------
// Average review rating per site
// -----------------------------
db.heritage_sites.aggregate([
  { $unwind: "$reviews" },
  {
    $group: {
      _id: "$name",
      average_rating: { $avg: "$reviews.stars" }
    }
  }
]);

// -----------------------------
// Visitors per province
// -----------------------------
db.bookings.aggregate([
  {
    $group: {
      _id: "$province",
      visitors: { $sum: "$visitors" }
    }
  }
]);
