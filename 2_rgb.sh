#!/bin/bash
#
# ***************************************************************************
# Name                 : 2 RGB
# Description          : Create file RGB (3 bands)
#
# Arguments: 
# $1: Image R G B
#
# Dependencies         : gdal 1.10.1 (gdal_translate)
#
# ***************************************************************************
# begin                : 2015-04-24 (yyyy-mm-dd)
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
#   2_rgb.sh LC8_229-066_20140724_LGN00.tif 6 5 4
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
calc_rbgname_img(){
local dirname=$(dirname $in_img)
local filename=$(basename $in_img)
local extension="${filename##*.}"
filename="${filename%.*}"
rbgname_img=$dirname"/"$filename"_r"$in_r"g"$in_g"b"$in_b"."$extension
}
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <image> <r> <g> <b>" >&2
  echo "<image> is the image" >&2
  echo "<r> Number of band for R" >&2
  echo "<g> Number of band for G" >&2
  echo "<b> Number of band for B" >&2
  exit 1
}
#
totalargs=4
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
in_img=$1
in_r=$2
in_g=$3
in_b=$4
#
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
#
calc_rbgname_img
#
printf "Creating "$rbgname_img"..."
#
gdal_translate -q -co COMPRESS=LZW -b $in_r -b $in_g -b $in_b $in_img $rbgname_img
#
code=$?
if [ "$code" != 0 ]
then
  exit $code
fi
#
printf "Finished.\n"
#
exit 0
