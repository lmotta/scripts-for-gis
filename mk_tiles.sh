#!/bin/bash
#
# ***************************************************************************
# Name                 : mk_tiles
# Description          : Make TMS from image 
#
# Arguments: 
# $1: Image for tiles
# $2: Number of Band R
# $3: Number of Band G
# $4: Number of Band B
# $5: Zoom min
# $6: Zoom max
# $7: Diretory TMS
# $8: Diretory PNG
# $9: URL for TMS
#
# Dependencies         : gdal 1.10.1(gdalbuildvrt), dans-gdal-script 0.23-2(gdal_contrast_stretch), tilers-tools 3.2.0(gdal_tiler.py), thumbnail_gdal.sh
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
# Examples:
#   CBERS (bands 2, 3 and 4):
#   mk_tiles.sh 173-112_20080826_CBERS2B_CCD_B234_RET.tif 0 2 3 4 3 15 /public/tms /public/jpg http://10.1.8.20/tms
#
#   Rapid Eye (bands 4, 5 and 3)
#   mk_tiles.sh 2034016_2011-05-28T152704_RE1_3A-NAC_11056706_149189.tif  4 5 3 3 17 /public/tms /public/jpg
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
calc_gdal_tms(){
gdal_tms="<GDAL_WMS>
    <Service name=\"TMS\">
        <ServerUrl>"$url"/"$name_img".tms/\${z}/\${x}/\${y}.png</ServerUrl>
        <SRS>EPSG:3857</SRS>#https://launchpad.net/ubuntu/trusty/amd64/dans-gdal-scripts
        <ImageFormat>image/png</ImageFormat>
    </Service>fpng
    <DataWindow>
        <UpperLeftX>-20037508.34</UpperLeftX>
        <UpperLeftY>20037508.34</UpperLeftY>
        <LowerRightX>20037508.34</LowerRightX>
        <LowerRightY>-20037508.34</LowerRightY>
        <TileLevel>"$zmax"</TileLevel>
        <TileCountX>1</TileCountX>
        <TileCountY>1</TileCountY>
        <YOrigin>bottom</YOrigin>
    </DataWindow>
    <Projection>EPSG:3857</Projection>
    <BlockSizeX>256</BlockSizeX>
    <BlockSizeY>256</BlockSizeY>
    <BandsCount>4</BandsCount>
    <ZeroBlockHttpCodes>204,303,400,404,500,501</ZeroBlockHttpCodes>
    <ZeroBlockOnServerException>true</ZeroBlockOnServerException>
    <Cache>
        <Path>/tmp/cache_"$name_img".tms</Path>
    </Cache>
</GDAL_WMS>"
}
#
msg_error(){
  local name_script=$(basename $0)
  echo "Usage: $name_script <Image> <Band R> <Band G> <Band B> <Zoom Min> <Zoom Max> <Dir TMS> <Dir PNG> <URL>" >&2
  echo "<Image> is the image for TMS" >&2
  echo "<Band R> Number of Band R" >&2
  echo "<Band G> Number of Band G" >&2
  echo "<Band B> Number of Band B" >&2
  echo "<Zoom Min> Zoom minimum of TMS" >&2
  echo "<Zoom Max> Zoom maximum of TMS" >&2
  echo "<Dir PNG> Directory for PNG" >&2
  echo "<Dir TMS> Directory for TMS" >&2
  echo "<URL> URL for TMS" >&2
}
#
totalargs=9
#
if [ $# -ne $totalargs ] ; then
  msg_errorls -1 *.tif | parallel mk_tiles.sh {} 1 2 3 3 14 ./tms ./png http://10.1.8.20/teste_lmotta
  exit 1
fi
in_img=$1
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
r=$2
g=$3
b=$4
zmin=$5
zmax=$6
dir_png=$7
if [ ! -d "$dir_png" ] ; then
  echo "The Directory '$dir_png' not exist" >&2
  exit 1
fi
dir_tms=$8
if [ ! -d "$dir_tms" ] ; then
  echo "The Directory '$dir_tms' not exist" >&2
  exit 1
fi
url=$9
#
dir_img=$(dirname $in_img)
basename_img=$(basename $in_img)
name_img=${basename_img%.*}
#
nodata=0
mode='tms'
#
fvrt=$dir_img"/"$name_img".vrt"
fcontrast=$dir_img"/"$name_img"_b"$r$g$b"_contrast.tif"
fpng=$dir_png"/"$name_img".png"
fintms=$dir_img"/"$name_img
fgdal_tms_xml=$dir_tms"/"$name_img"_tms.xml"
#
dateini=$(date +"%Y%m%d %H:%M:%S")
arg=$name_img"("$dateini")...1"
printf "%s" "$arg"
#
gdalbuildvrt -q -b $r -b $g -b $b  $fvrt $in_img
gdal_contrast_stretch -ndv 0 -outndv 0 -percentile-range 0.02 0.98  $fvrt $fcontrast  > /dev/null
#
printf ".2"
thumbnail_gdal.sh $fcontrast 30  > /dev/null
mv $dir_img"/"$name_img"_b"$r$g$b"_contrast.png" $fpng
#
printf ".3"
mv  $fcontrast $fintms
gdal_tiler.py -q -p $mode --src-nodata $nodata,$nodata,$nodata --zoom $zmin:$zmax -t $dir_tms $fintms
rm $fvrt $fintms
calc_gdal_tms
echo $gdal_tms > $fgdal_tms_xml
#
dateend=$(date +"%Y%m%d %H:%M:%S")
arg=".("$dateend")"
printf "%s" "$arg"
echo ""
#
# Log
echo "$name_img;$dateini;$dateend" >> mk_tiles.sh.log
