#!/bin/bash
#
# ***************************************************************************
# Name                 : Check image
# Description          : If image have error, print ERROR
#
# Arguments: 
# $1: Image
#
# Dependencies         : gdal 1.10.1 (gdalinfo)
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
#   check_img.sh LC8_229-066_20140724_LGN00_r6g5b4.tif
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
clean(){
  if [ -f "$in_img.error.txt" ] ; then
    rm "$in_img.error.txt"
  fi
  if [ -f "$in_img.aux.xml" ] ; then
    rm "$in_img.aux.xml"
  fi
}
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <image>" >&2
  echo "<image> is the image" >&2
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
gdalinfo -mm -stats $in_img 2> "$in_img.error.txt" >/dev/null;
error=$(cat "$in_img.error.txt" | grep ERROR | head -1 | cut -d':' -f1);
if [ "$error" == "" ]; then
  clean
  exit 0
fi
echo "$in_img:$error"
clean
exit 0
