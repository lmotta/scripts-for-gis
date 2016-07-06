#!/bin/bash
#
# ***************************************************************************
# Name                 : Wget images from INPE catalog site and create RGB Stack
# Description          : Download Zip from url(user order from email) with only Bands R G B, unzip them and create stack RGB
#                        Testing: ResourceSatLISS3
# Arguments: 
# $1: user order
# $2: R band number
# $3: G band number
# $4: B band number
#
# Dependencies         : wget, unzip, gdal_merge.py
#
# ***************************************************************************
# begin                : 2016-06-30 (yyyy-mm-dd)
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
#   wget_inpe_rgb_stack.sh mottaluiz1115611 3 4 2
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
###
download_inpe(){
  local url="http://imagens.dgi.inpe.br/cdsr/"$userorder"/"
  #
  local mask=".+BAND[2,3,4].+zip"
  local total=$(wget -q -O - $url | egrep $mask | cut -d'"' -f2  | wc -l)
  local dir_download=$userorder"_download"
  printf "Downloading %d images in '%s'...\r" $total $dir_download
  wget -q -r -np -P $dir_download --accept-regex $mask $url
  for item in $(find $dir_download -type f -name "*.zip"); do mv $item .; done
  rm -r $dir_download
}
unzip_inpe(){
  local l_zip=$(ls *.zip)
  local total=$(echo $l_zip | wc -w)
  local name=""
  local num=0
  for item in $l_zip
  do 
    num=$(echo "$num+1" | bc)
    printf "Unzip '%s' (%d of %d)...\r" $item $num $total
    unzip $item > /dev/null
    rm $item
    rm $(echo $item | sed 's/.zip/.xml/g') 2> /dev/null
  done
}
stack_inpe(){
  local imgs=$(ls *BAND*.tif | rev | cut -d'_' -f2- | rev | sort | uniq)
  local l_bands="_BAND$r.tif _BAND$g.tif _BAND$b.tif"
  local suffix="_R"$r"G"$g"B"$b".tif"
  local total=$(echo $imgs | wc -w)
  local num=0
  for img in $imgs
  do
    num=$(echo "$num+1" | bc)
    s_bands=""
    for item in $l_bands; do s_bands=$s_bands" "$img$item; done
    error=$img"_error.log"
    ls $s_bands  > /dev/null 2>> $error
    if [ $? -eq 0 ];then
      rm -f $error
      printf "Creating '%s' (%d of %d)...\r" $img$suffix $num $total
      gdal_merge.py -q -separate -o $img$suffix $s_bands 2> /dev/null
      rm $s_bands> /dev/null
    else
      log=$(cat $error)
      echo $img":" > $error
      echo $log >> $error
    fi
  done
  # 
  ls *_error.log  > /dev/null 2>> /dev/null
  if [ $? -eq 0 ];then
    printf "%-100s\n" "Error creating RGB TIF's (see log error)"
    rm *_BAND*.tif
  else
    printf "%-100s\n" "Success created RGB TIF's( total "$total")"
  fi
}
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <userorder> <R> <G> <B>" >&2
  echo "<userorder> User order from INPE email"
  echo "<R> Number of Band for Red" >&2
  echo "<G> Number of Band for Green" >&2
  echo "<B> Number of Band for Blue" >&2
  echo ""
  echo "Example: wget_cbers_images.sh motta.luiz3241 7 8 6"
  exit 1
}
#
totalargs=4
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
###
userorder=$1
r=$2
g=$3
b=$4
#
download_inpe
unzip_inpe
stack_inpe
