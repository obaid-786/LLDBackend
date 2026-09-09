INSERT INTO problems (title, description, constraints, difficulty) VALUES
('Parking Lot System',
 'Design a parking lot that can handle multiple vehicle types (car, bike, truck), has multiple floors, and provides features like finding available spots, parking, and unparking. The system should keep track of occupancy and generate revenue reports.',
 'Assume a fixed number of floors and spots per floor. Vehicles have different sizes.',
 'Medium'),

('Vending Machine',
 'Design a vending machine that accepts coins and notes, dispenses items, gives change, and handles inventory. The machine should support multiple product types and provide a user interface (via buttons).',
 'Assume a fixed set of products with prices. Coins denominations: 1, 5, 10, 25 cents; notes: 1, 5, 10 dollars.',
 'Easy'),

('Elevator System',
 'Design an elevator control system for a building with multiple elevators. The system should handle passenger requests, dispatch the nearest elevator, and move elevators efficiently. Include features like direction, floor selection, and emergency stop.',
 'Assume a building with N floors and M elevators. Each elevator has a capacity limit.',
 'Hard');