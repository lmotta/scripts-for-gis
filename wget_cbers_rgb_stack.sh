#!/bin/bash
#
# ***************************************************************************
# Name                 : Wget CBERS RGB Stack
# Description          : Download Zip from url(user order from email) with only Bands R G B, unzip them and create stack RGB
#
# Arguments: 
# $1: user order
# $2: R band number
# $3: G band number
# $4: B band number
#
# Dependencies         : wget, unzip, gdal_merge.py
#
# ***************************************************************************
# begin                : 2016-05-04 (yyyy-mm-dd)
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
#   wget_cbers_rgb_stack.sh motta.luiz3241 7 8 6
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
download_cbers(){
  local url="http://imagens.dgi.inpe.br/cdsr/"$userorder
  #
  local tmp_html=$userorder"_tmp.html"
  wget -q -O $tmp_html -r -np -A "BAND" $url
  local cmd_grep="grep -e BAND$r\.zip -e BAND$g\.zip -e BAND$b\.zip"
  local total=$(cat $tmp_html | $(echo $cmd_grep) | wc -l)
  rm $tmp_html
  printf "Downloading %s ZIP's..." $total
  #
  wget -q -r -np -A "*_BAND$r\.zip" -A "*_BAND$g\.zip" -A "*_BAND$b\.zip" $url
  #
  for item in $(find . -type f -name "*.zip"); do mv $item .; done
  rm -r imagens.dgi.inpe.br
}
unzip_cbers(){
  local l_zip=$(ls *.zip)
  local total=$(echo $l_zip | wc -w)
  local name=""
  local num=0
  for item in $l_zip
  do 
    num=$(echo "$num+1" | bc)
    printf "\rUnzip %s (%s of %s)..." $item $num $total
    unzip $item > /dev/null
    rm $item
    rm $(echo $item | sed 's/.zip/.xml/g')
  done
}
stack_cbers(){
  local imgs=$(ls *BAND*.tif | cut -d'_' -f-7 | sort | uniq)
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
      printf "\rCreating %s (%s of %s)..." $img$suffix $num $total
      gdal_merge.py -q -separate -o $img$suffix $s_bands
      rm $s_bands
    else
      log=$(cat $error)
      echo $img":" > $error
      echo $log >> $error
    fi
  done
  # 
  ls *_error.log  > /dev/null 2>> /dev/null
  if [ $? -eq 0 ];then
    printf "\r%-100s\n" "Error creating RGB TIF's (see log error)"
    rm *_BAND*.tif
  else
    printf "\r%-100s\n" "Success created RGB TIF's( total "$total")"
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
download_cbers
unzip_cbers
stack_cbers
