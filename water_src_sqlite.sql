-- Verify the name of Geometry field (Ex.: geom or geometry)
SELECT b.id, Centroid( b.geometry ) as geometry
FROM
(
  SELECT  id, Buffer( StartPoint( geometry ),  0.001 ) as geometry
  FROM HIDRO_100000_DOCE
  --
  UNION
  --
  SELECT  id, Buffer( EndPoint( geometry ),  0.001 ) as geometry
  FROM HIDRO_100000_DOCE
)b
INNER JOIN HIDRO_100000_DOCE l
ON MbrIntersects( b.geometry, l.geometry ) AND Intersects( b.geometry, l.geometry)
GROUP BY b.id, b.geometry
HAVING Count(1) = 1;
