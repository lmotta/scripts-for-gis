#!/bin/bash
#
# ***************************************************************************
# Name                 : Rename shapefile
# Description          : Rename shapefile (all files of shapefile)
# Arguments            : shapefile(with .shp) new_name
# Dependencies         : None
#
#                       -------------------
# begin                : 2014-03-01
# copyright            : (C) 2014 by Luiz Motta
# email                : motta dot luiz at gmail.com
# ***************************************************************************
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
name_script=$(basename $0)
if [ $# -ne 2 ] ; then
  echo "Usage: $name_script <new name>" >&2
  echo "<shapefile> is the shapefile(with .shp)" >&2
  echo "<new name> is the name for rename(without .shp)" >&2
  exit 1
fi
#
rename_shapefile(){
  local basename_shp=$(basename $shp)
  local name_shp=${basename_shp%.*}
  local pathn=$(dirname $shp)
  local vext=""
  local vbase=""
  local vfiles=$(echo $pathn"/"$name_shp".*")
  for f in $vfiles
  do
     vbase=$(basename $f)
     vext=${vbase##*.}
     mv "$pathn/$f" "$pathn/$newname.$vext"
  done
}
# Parameters for GDAL Utilities
shp=$1
newname=$2
#
rename_shapefile
