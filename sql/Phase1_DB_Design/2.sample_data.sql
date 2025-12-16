-- =========================================
-- Sample Data: South African Heritage Sites
-- =========================================

-- Provinces
INSERT INTO province (name) VALUES
('Gauteng'),
('Western Cape'),
('KwaZulu-Natal'),
('Eastern Cape'),
('Free State'),
('Limpopo'),
('Mpumalanga'),
('North West'),
('Northern Cape');

-- Categories
INSERT INTO category (name) VALUES
('Historical'),
('Cultural'),
('Archaeological'),
('Natural'),
('Memorial');

-- Heritage Sites
INSERT INTO heritage_site (name, description, province_id, category_id, established_year, entry_fee) VALUES
('Robben Island', 'Former prison and World Heritage Site', 2, 5, 1961, 600.00),
('Cradle of Humankind', 'Archaeological fossil site', 1, 3, 1999, 250.00),
('Voortrekker Monument', 'Afrikaner heritage monument', 1, 5, 1949, 100.00),
('Isandlwana Battlefield', 'Historic Anglo-Zulu war site', 3, 1, 1879, 80.00),
('Mapungubwe', 'Ancient African kingdom ruins', 6, 3, 900, 150.00),
('Freedom Park', 'Post-apartheid memorial', 1, 5, 2004, 120.00),
('Castle of Good Hope', 'Oldest colonial building', 2, 1, 1666, 50.00),
('Tswaing Crater', 'Meteorite impact site', 1, 4, NULL, 30.00),
('Sterkfontein Caves', 'Hominid fossil caves', 1, 3, NULL, 100.00),
('Nelson Mandela Capture Site', 'Apartheid history landmark', 3, 5, 1962, 90.00),
('uKhahlamba-Drakensberg Park', 'Mountain range and rock art', 3, 4, NULL, 120.00),
('Golden Gate Highlands', 'Sandstone rock formations', 5, 4, NULL, 80.00),
('Augrabies Falls', 'Waterfall and national park', 9, 4, NULL, 100.00),
('Pilgrim’s Rest', 'Historic gold mining town', 7, 1, 1873, 60.00),
('Blood River', 'Historic battle memorial', 3, 5, 1838, 70.00);

-- Visitors
INSERT INTO visitor (first_name, last_name, email) VALUES
('Sipho', 'Dlamini', 'sipho.dlamini@email.com'),
('Thandi', 'Mokoena', 'thandi.m@email.com'),
('John', 'Smith', 'john.smith@email.com'),
('Ayesha', 'Khan', 'ayesha.k@email.com'),
('Michael', 'Brown', 'michael.b@email.com'),
('Lerato', 'Nkosi', 'lerato.n@email.com'),
('David', 'Johnson', 'david.j@email.com'),
('Nomsa', 'Zulu', 'nomsa.z@email.com'),
('Peter', 'Botha', 'peter.b@email.com'),
('Zanele', 'Khumalo', 'zanele.k@email.com'),
('Emma', 'Williams', 'emma.w@email.com'),
('Chris', 'Taylor', 'chris.t@email.com'),
('Kagiso', 'Molefe', 'kagiso.m@email.com'),
('Fatima', 'Abrahams', 'fatima.a@email.com'),
('Jacob', 'van Wyk', 'jacob.vw@email.com'),
('Nokuthula', 'Mabaso', 'noku.m@email.com'),
('Brian', 'Miller', 'brian.m@email.com'),
('Sibongile', 'Nene', 'sibo.n@email.com'),
('Andre', 'Fourie', 'andre.f@email.com'),
('Linda', 'Peters', 'linda.p@email.com');

-- Bookings
INSERT INTO booking (visitor_id, site_id, booking_date, visit_date, number_of_tickets) VALUES
(1, 1, '2024-01-10', '2024-02-01', 2),
(2, 2, '2024-01-12', '2024-02-05', 4),
(3, 1, '2024-01-15', '2024-02-10', 1),
(4, 3, '2024-01-18', '2024-02-12', 3),
(5, 4, '2024-01-20', '2024-02-15', 2),
(6, 5, '2024-01-25', '2024-02-20', 5),
(7, 6, '2024-01-28', '2024-02-22', 2),
(8, 7, '2024-02-01', '2024-02-25', 1),
(9, 8, '2024-02-02', '2024-02-26', 4),
(10, 9, '2024-02-03', '2024-02-28', 2),
(11, 10, '2024-02-05', '2024-03-01', 3),
(12, 11, '2024-02-06', '2024-03-02', 2),
(13, 12, '2024-02-08', '2024-03-05', 1),
(14, 13, '2024-02-10', '2024-03-07', 4),
(15, 14, '2024-02-12', '2024-03-09', 2),
(16, 15, '2024-02-14', '2024-03-10', 3);

-- Reviews
INSERT INTO review (visitor_id, site_id, rating, comment) VALUES
(1, 1, 5, 'Very moving experience'),
(2, 2, 4, 'Educational and fascinating'),
(3, 1, 5, 'A must-visit'),
(4, 3, 3, 'Interesting but crowded'),
(5, 4, 4, 'Well preserved site'),
(6, 5, 5, 'Rich cultural history'),
(7, 6, 4, 'Peaceful and reflective'),
(8, 7, 3, 'Small but historic'),
(9, 8, 4, 'Unique natural site'),
(10, 9, 5, 'Amazing archaeological site');
