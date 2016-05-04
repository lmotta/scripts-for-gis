#!/bin/bash
#
# ***************************************************************************
# Name                 : Stack CBERS
# Description          : Stack 3 Bands for Create RGB tif for all imagens in current directory
#
# Arguments: 
# $1: Number of band R
# $2: Number of band G
# $3: Number of band B
#
# Dependencies         : gdal 1.10.1 (gdal_merge.py)
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
#   stack_cbers.sh 7 8 6
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
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <R> <G> <B>" >&2
  echo "<R> Number of Band for Red" >&2
  echo "<G> Number of Band for Green" >&2
  echo "<B> Number of Band for Blue" >&2
  echo ""
  echo "Example: stack_cbers.sh 7 8 6"
  exit 1
}
#
totalargs=3
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
##
r=$1
g=$2
b=$3
#
imgs=$(ls *BAND*.tif | cut -d'_' -f-7 | sort | uniq)
l_bands="_BAND$r.tif _BAND$g.tif _BAND$b.tif"
l_xmls="_BAND$r.xml _BAND$g.xml _BAND$b.xml"
suffix="_R"$r"G"$g"B"$b".tif"
#
mkdir band_tif 2>> /dev/null
#
total=$(echo $imgs | wc -w)
num=0
for img in $imgs
do
  num=$(echo "$num+1" | bc)
  s_bands=""
  for item in $l_bands; do s_bands=$s_bands" "$img$item; done
  s_xmls=""
  for item in $l_xmls; do s_xmls=$s_xmls" "$img$item; done
  error=$img"_error.log"
  ls $s_bands  > /dev/null 2>> $error
  if [ $? -eq 0 ];then
    rm -f $error
    printf "\rCreating %s (%s of %s)..." $img$suffix $num $total
    gdal_merge.py -q -separate -o $img$suffix $s_bands
    mv $s_bands band_tif
    mv $s_xmls band_tif
  else
    log=$(cat $error)
    echo $img":" > $error
    echo $log >> $error
  fi
done
# 
ls *_error.log  > /dev/null 2>> /dev/null
if [ $? -eq 0 ];then
  printf "\r%-100s\n" "Error creating TIF's (see log error)"
else
  printf "\r%-100s\n" "Success created TIF's("$total")"
fi
#
