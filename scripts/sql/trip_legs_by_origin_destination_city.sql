SELECT person_id,
    departure,
    origins.coordinates as origin,
    destinations.coordinates as destination,
    origins.city as origin_city,
    destinations.city as destination_city,
    ST_MakeLine(origins.coordinates, destinations.coordinates) as leg,
    trip_leg as leg_id
FROM trips
    JOIN locations AS origins ON trips.origin_location_id = origins.id
    JOIN locations AS destinations ON trips.destination_location_id = destinations.id