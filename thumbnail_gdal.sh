#!/bin/bash
#
# ***************************************************************************
# Name                 : Thumbnail_gdal
# Description          : Create thumbnail from image 
#
# Arguments: 
# $1: Image
#
# Dependencies         : gdal 1.10.1 (gdal_translate)
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
#   thumbnail_gdal.sh LC8_229-066_20140724_LGN00_r6g5b4.tif
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
  local name_script=$(basename_img $0)
  echo "Usage: $name_script <image> <outsize>" >&2
  echo "<image> is the image thumbnail" >&2
  echo "<outsize> is the % of original size" >&2
}
#
totalargs=2
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
in_img=$1
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
outsize=$2
#
dir_img=$(dirname $in_img)
basename_img=$(basename $in_img)
name_img=${basename_img%.*}
#
thumbnail=$dir_img"/"$name_img".png"
#
export GDAL_PAM_ENABLED=NO
gdal_translate -ot byte -of PNG -outsize $outsize"%" $outsize"%" -a_nodata 0 -q $in_img $thumbnail
echo "Finished $name_img."
#
