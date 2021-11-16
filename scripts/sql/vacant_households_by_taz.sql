-- Calculate the number of vacant households
SELECT locations.taz_id,
    count(*) as total,
    avg(vac.vacant) as total_vacant,
    avg(vac.vacant) / count(*) as vacant_pct
FROM locations
    LEFT JOIN (
        SELECT locations.taz_id,
            count(*) as vacant
        FROM locations
        WHERE locations.residential = true
            AND locations.use ilike '%vac%'
        GROUP BY 1
    ) as vac ON vac.taz_id = locations.taz_id
WHERE locations.residential = true
GROUP BY locations.taz_id
ORDER BY vacant_pct DESC;