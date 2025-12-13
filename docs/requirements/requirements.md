# System Requirements

## Functional Requirements
1. The system must store heritage sites and their provinces.
2. Each heritage site must belong to one category.
3. Visitors must be able to book visits to heritage sites.
4. A visitor may have multiple bookings.
5. Visitors may leave a review after a booking.

## Business Rules
1. A booking is associated with exactly one visitor and one heritage site.
2. Reviews are optional.
3. A heritage site cannot exist without a province.
4. Ratings range from 1 to 5.

## Non-Functional Requirements
- Data integrity must be enforced using constraints.
- The schema must be normalized to 3NF.
