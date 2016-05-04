#!/bin/bash
#
# ***************************************************************************
# Name                 : Wget CBERS images
# Description          : Download Zip from url(user order from email) and unzip select RGB bands
#
# Arguments: 
# $1: user order
# $2: R band number
# $3: G band number
# $4: B band number
#
# Dependencies         : wget, unzip
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
#   wget_cbers_images.sh motta.luiz3241 7 8 6
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
##

userorder=$1
r=$2
g=$3
b=$4
#
search_string="BAND"$r"\|BAND"$g"\|BAND"$b
url="http://imagens.dgi.inpe.br/cdsr/"$userorder
#
printf "Download ZIP's..."
wget -q -r -np --no-parent -A.zip $url > /dev/null
l_zip=$(find . -type f -name "*.zip" | grep $search_string | sort)
total=$(echo $l_zip | wc -w)
num=0
for item in $l_zip
do 
  mv $item .
  name=$(basename $item)
  num=$(echo "$num+1" | bc)
  printf "\rUnzip %s (%s of %s)..." $name $num $total
  unzip $name > /dev/null 
done
rm -r imagens.dgi.inpe.br
mkdir zip 2>> /dev/null
mv *.zip zip 2>> /dev/null
printf "\r%-100s\n" "Finished "$total" downloads!"
