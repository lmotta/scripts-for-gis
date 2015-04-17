#!/bin/bash
#
# ***************************************************************************
# Name                 : 16bit 2 8bit
# Description          : Convert 16 to 8 bits. Change original image!
#
# Arguments: 
# $1: Image with 16bits
#
# Dependencies         : gdal 1.10.1 (gdal_translate, gdalinfo, gdalbuildvrt)
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
#   16b_2_8b_convert.sh LC8_229-066_20140724_LGN00_r6g5b4.tif
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
calc_min_max(){
# line_stats:
# Minimum=5145.000,Maximum=21668.000,Mean=6399.841,StdDev=871.059
  local line_stats=$1
  min=$(echo $line_stats | cut -d',' -f1 | cut -d'=' -f2)
  max=$(echo $line_stats | cut -d',' -f2 | cut -d'=' -f2)
}
#
calc_arrays(){
# calc_min_max: [ ]
  local img=$1
  local index=0
  for item in $(gdalinfo -stats $img | grep Minimum | sed 's/\s\+//g')
  do
    calc_min_max $item
    aryMin[$index]=$min
    aryMax[$index]=$max
    aryIndex[$index]=$index
    index=$(echo $index+1 | bc)
  done
}
#
calc_str_vrt_bands(){
  str_vrt_bands=""
  for item in ${aryIndex[@]}
  do
    numBand=$(echo $item+1 | bc)
    str_vrt_bands="$str_vrt_bands $temp_dir/$basename_img.B$numBand.temp"
  done
}
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <image>" >&2
  echo "<image> is the image of 16 bits (change this image for 8 bits)" >&2
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
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
#
temp_dir=$(mktemp -d)
basename_img=$(basename $in_img)
#
printf "Converting $basename_img to 8bits..."
#
calc_arrays $in_img
rm "$in_img.aux.xml"
#
# Single bands with 8bits
for item in ${aryIndex[@]}
do
 numBand=$(echo "$item+1" | bc)
 gdal_translate -q -ot Byte -b $numBand -scale ${aryMin[$item]} ${aryMax[$item]} $in_img "$temp_dir/$basename_img.B$numBand.temp"
done
# VRT
calc_str_vrt_bands
gdalbuildvrt -q -separate "$temp_dir/$basename_img.vrt" $str_vrt_bands
#
code=$?
if [ "$code" != 0 ]
then
  exit $code
fi
# Remove ORIGINAL AND Create image 8bits
gdal_translate -q -co COMPRESS=LZW "$temp_dir/$basename_img.vrt" "$temp_dir/$basename_img"
#
code=$?
if [ "$code" != 0 ]
then
  exit $code
fi
#
mv "$temp_dir/$basename_img" $in_img
# Clean
rm -r $temp_dir
#
printf "Finished.\n"
#
exit 0
