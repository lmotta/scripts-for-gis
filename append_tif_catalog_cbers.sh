#!/bin/bash
#
# ***************************************************************************
# Name                 : Append footprint's images to catalog
# Description          : Create footprint from images in current directory and add to catalog(shapefile)
#
# Arguments: 
# $1: Path/Name of shapefile
#
# Dependencies         : footprint_gina.sh, footprint_append_shp.sh
#
# ***************************************************************************
# begin                : 2016-05-04 (yyyy-mm-dd)
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
#   append_tif_catalog_cbers.sh cbers4.shp
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
#
## Functions
format_time(){
  # deltatime=$1
  minutes=$(echo "$1/60" | bc)
  seconds=$(echo "$1%60" | bc)
  ftime="$minutes:$seconds"
}
#
print_status_process(){
  if [ ! "$step" -eq "0" ]; then
    local timenow=$(date -u +"%s")
    local perc=$(echo "scale=4;$step/$total*100" | bc)
    local ftime=""
    local deltatime=$(echo "$timenow-$timeini" | bc)
    local lefttime=$(echo "scale=4;($deltatime/$step)*($total-$step)" | bc)
    format_time $deltatime
    local fdeltatime=$ftime
    format_time $lefttime
    local flefttime=$ftime
    printf "\r%-100s" "$step/$total($perc %) - times(minutes:seconds): $fdeltatime(elapsed) $flefttime(left)"
  fi
}
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <shapefile>" >&2
  echo "<shapefile> is the name of shapefile(with extension 'shp')" >&2
  echo ""
  echo "Example: append_tif_catalog_cbers.sh cbers4.shp"
  exit 1
}
#
totalargs=1
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
##
shp=$1
#
## Process variable
title="Populating footprint '"$shp"'"
lst=$(ls *.tif)
##
dateini=$(date +"%Y%m%d %H:%M:%S")
echo
echo $title" - Started "$dateini
#
total=$(echo $lst | wc -w)
step='0'
timeini=$(date -u +"%s")
for item in $lst
do
 print_status_process
 #
 footprint_gina.sh $item > /dev/null 
 geojson=$(echo $item | sed 's/.tif/.geojson/g')
 footprint_append_shp.sh $geojson $shp >/dev/null
 rm $geojson
 #
 step=$(echo "$step+1" | bc)
done
#
dateend=$(date +"%Y%m%d %H:%M:%S")
echo
echo "Finished "$dateend
