-- Geometry field need be a LINESTRING - http://postgis.net/docs/manual-1.4/ST_StartPoint.html
SELECT b.id, ST_Centroid( b.geom ) as geom
FROM
(
  SELECT  id, ST_Buffer( ST_StartPoint( geom ),  0.001 ) as geom
  FROM "public"."HIDRO_100000_DOCE"
  --
  UNION
  --
  SELECT  id, ST_Buffer( ST_EndPoint( geom ),  0.001 ) as geom
  FROM "public"."HIDRO_100000_DOCE"
)b
INNER JOIN "public"."HIDRO_100000_DOCE" l
ON b.geom && l.geom AND ST_Intersects( b.geom, l.geom)
GROUP BY b.id, b.geom
HAVING Count(1) = 1;
