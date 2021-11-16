-- Average number of persons per household per TAZ
SELECT locations.taz_id,
    avg(sq.num_people)
FROM locations
    JOIN (
        SELECT locations.id AS location_id,
            households.id AS household_id,
            count(persons.id) AS num_people
        FROM persons
            LEFT JOIN households ON persons.household_id = households.id
            LEFT JOIN locations ON households.location_id = locations.id
        GROUP BY 1,
            2
    ) as sq ON locations.id = sq.location_id
GROUP BY locations.taz_id