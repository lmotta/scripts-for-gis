#!/bin/bash
#
# ***************************************************************************
# Name                 : Footprint Gina
# Description          : Create footprint of image with GeoJSON format using GINA Tools(http://www.gina.alaska.edu/projects/gina-tools/)
#
# Arguments: 
# $1: Image
#
# Dependencies         : gdal 1.10.1(ogr2ogr) and dans-gdal-scripts(gdal_trace_outline)
#
# ***************************************************************************
# begin                : 2016-04-03 (yyyy-mm-dd)
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
#   footprint_gina.sh LC8_229-066_20140724_LGN00_r6g5b4.tif
#
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# ***************************************************************************
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <image>" >&2
  echo "<image> is the image for calculate footprint" >&2
  exit 1
}
#
totalargs=1
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
in_img=$1
#
if [ ! -f "$in_img" ]; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
#
dir_img=$(dirname $in_img)
basename_img=$(basename $in_img)
name_img=${basename_img%.*}
#
footprint_geojson=$dir_img"/"$name_img".geojson"
footprint_error=$dir_img"/"$name_img"_error.log"
#
if [ -f $footprint_geojson ]; then
 rm $footprint_geojson
fi
# Processing
printf "'$name_img'..."
gdal_trace_outline -ndv 0 -b 1 -min-ring-area 3 -erosion -out-cs ll -ogr-fmt "GeoJSON" -ogr-out $footprint_geojson $in_img >/dev/null 2>$footprint_error
#
code=$?
if [ "$code" != 0 ]
then
  echo $(cat $footprint_error)
  exit $code
fi
#
rm $footprint_error
#
tmp_file=$footprint_geojson".tmp"
ogr2ogr -dialect SQLITE -sql "SELECT 'value' as path_image, ST_NumGeometries( geometry ) as total_part, geometry FROM OGRGeoJSON" -f "GeoJSON" $tmp_file $footprint_geojson
ssed="s|{ \"path_image\": \"value\"|{ \"path\": \"$dir_img\", \"image\": \"$basename_img\"|g"
sed -i "$ssed" "$tmp_file"
mv -f $tmp_file $footprint_geojson
#
printf "\rCreated: $footprint_geojson\n"
#
exit 0
