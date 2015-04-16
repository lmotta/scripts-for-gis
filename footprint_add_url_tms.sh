#!/bin/bash
#
# ***************************************************************************
# Name                 : Footprint Add URL of TMS
# Description          : Add URL od TMS in GeoJson
#
# Arguments: 
# $1: GeoJSON
#
# Dependencies         : None
#
# ***************************************************************************
# begin                : 2015-03-02 (yyyy-mm-dd)
# copyright            : (C) 2015 by Luiz Motta
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
#   footprint_add_url_tms.sh LC8_229-066_20140724_LGN00_r6g5b4.geoJSON http://catalog/lc8
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
  echo "Usage: $name_script <footprint_geojson> <url>" >&2
  echo "<footprint_geojson> is the footprint geoJson" >&2
  echo "<url> is the URL of server" >&2
}
#
totalargs=2
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
footprint_geojson=$1
url=$2
#
if [ ! -f "$footprint_geojson" ] ; then
  echo "The file '$footprint_geojson' not exist" >&2
  exit 1
fi
#
basename_footprint_geojson=$(basename $footprint_geojson)
name_footprint_geojson=${basename_footprint_geojson%.geojson}
#
#{ "image": "LC8_229-066_20141113_LGN00_r6g5b4" }
# Separator  = @
sed -i 's@{ "image": "'$name_footprint_geojson'" }@{ "image": "'$name_footprint_geojson'" , "url_tms": "'$url'/'$name_footprint_geojson'_tms.xml" }@g' $footprint_geojson
