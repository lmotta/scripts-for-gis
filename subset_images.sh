#!/bin/bash
#
# ***************************************************************************
# Name                 : Subset Images from Harpia
# Description          : Create subset imagens from Harpia
#
# Arguments:           $1: WKT region
#
# Dependencies         : jq(https://stedolan.github.io/jq/), gdal,
#                        bbox-wkt.py
#
# ***************************************************************************
# begin                : 2016-08-28 (yyyy-mm-dd)
# copyright            : (C) 2016 by Luiz Motta
# email                : motta dot luiz at gmail.com
# ***************************************************************************
#
# Revisions
#
# 0000-00-00:
# - None
# 
# ***************************************************************************
#
# Example:
#   subset_images 'Polygon ((-42.3109 -4.3156, ..., -42.3109 -4.3156))'
#
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************
##
# Functions
#
set_enviroment_pg(){
  PGHOSTADDR="10.1.8.58"
  PGUSER="96328576749"
  PGPASSWORD="lmotta&2015"
  PGDATABASE="siscom"
  table_catalog=ibama.img_catalogo_landsat_a
  export PGUSER PGPASSWORD PGHOSTADDR PGDATABASE
}
reset_enviroment_pg(){
  PGHOSTADDR=""
  PGUSER=""
  PGPASSWORD=""
  PGDATABASE=""
  export PGUSER PGPASSWORD PGHOSTADDR PGDATABASE
}
set_sql(){
# External: wkt
#
# Precisa converter o GEOM p/ o SR da tabela.
# APENAS p/ LC8
#
local link_l8="/vsicurl/http://siscom.ibama.gov.br/harpia/media/L8/"
local dest="replace( image, '.tif', '_subset.tif')"
local wktInter="replace(ST_AsText( ST_Intersection( ST_GeomFromText( $wkt, 4674 ), t.geom) ), ' ', ';' )"
local fields="'$link_l8' || split_part( image, '_', 1) || '/' || image || '@' || $dest || '@' || $wktInter"
local filter_geom="ST_GeomFromText( $wkt, 4674) && t.geom AND ST_Intersects( ST_GeomFromText( $wkt, 4674), t.geom )"
local filter="strpos( image, 'LC8')  = 1 AND $filter_geom"
sql="SELECT $fields FROM $table_catalog AS t WHERE $filter"
}
set_projwin(){
  # External: wkt
  local vresult=$(echo "bbox-wkt.py $wkt" | bash -)
  local isok=$(echo $vresult | jq '.["isOk"]')
  if [ $isok -eq 0 ] ; then
    local msg=$(echo $vresult | jq '.["msg"]')
    printf "\rError: "
    echo $msg
    exit 1
  fi
  projwin=$(echo $vresult | jq '.["bbox"]')
  projwin=${projwin:1:-1}
}
msg_error(){
  local name_script=$(basename $0)
  echo "Total of arguments '"$entryargs"' wrong!"
  echo "Usage: $name_script <wkt>" >&2
  echo "<wkt> is the WKT of Geometry" >&2
  exit 1
}
#
totalargs=1
entryargs=$#
#
if [ $entryargs -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
wkt="'$1'"
#
# Check WKT
set_projwin
#
printf "\nSearch in DB..."
set_enviroment_pg
set_sql
src_dest_lst=$(mktemp)
psql --tuples-only "-c $sql" | head -n -1 > $src_dest_lst

printf "\rCreating subsets..."
for item in $(cat $src_dest_lst)
do
  src=$(echo $item | cut -d'@' -f1)
  dest=$(echo $item | cut -d'@' -f2)
  wkt="'$(echo $item | cut -d'@' -f3 | sed 's/;/ /g')'"
  set_projwin
  gdal_translate -q -projwin_srs "EPSG:4326" -projwin $projwin $src $dest &
done
wait
total=$(cat $src_dest_lst | wc -l)
reset_enviroment_pg
rm $src_dest_lst
printf "\rCreated '%d' subsets images.\n" $total
