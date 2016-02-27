#!/bin/bash
#
# *** 1) Shapefile of example:
# http://hidroweb.ana.gov.br/baixar/mapa/Bacia8.zip
#
# *** 2) Dialect SQLITE
#
# SELECT b.id, Centroid( b.geometry ) as geometry
# FROM
# ( 
#   SELECT COTRECHO as id, Buffer( StartPoint( geometry ), 0.001 ) as geometry
#   FROM hidrocotrecho
#   --
#   UNION
#   --
#   SELECT COTRECHO as id, Buffer( EndPoint( geometry ), 0.001 ) as geometry
#   FROM hidrocotrecho
# )b
# INNER JOIN hidrocotrecho l
# ON
#  MbrIntersects( b.geometry, l.geometry ) AND
#  Intersects( b.geometry, l.geometry)
# GROUP BY b.id, b.geometry
# HAVING Count(1) = 1;
#
#
# *** 3) Create file without space and only field COTRECHO
ogr2ogr -overwrite -select COTRECHO hidrocotrecho.shp "Hidrografia 1000000.shp"
#
#
printf "Creating water source from river..."
# *** 4) Creating water source
ogr2ogr \
-overwrite \
-dialect SQLITE -sql \
"SELECT b.id, Centroid( b.geometry ) as geometry FROM ( SELECT COTRECHO as id, Buffer( StartPoint( geometry ), 0.001 ) as geometry FROM hidrocotrecho UNION SELECT COTRECHO as id, Buffer( EndPoint( geometry ), 0.001 ) as geometry FROM hidrocotrecho )b INNER JOIN hidrocotrecho l ON MbrIntersects( b.geometry, l.geometry ) AND Intersects( b.geometry, l.geometry) GROUP BY b.id, b.geometry HAVING Count(1) = 1" \
water_src.shp hidrocotrecho.shp
#
# *** 5) Cleanup
rm hidrocotrecho.*
#
printf "\r%-100s\n" "Created water source from river!"
