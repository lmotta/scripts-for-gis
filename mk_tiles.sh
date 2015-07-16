#!/bin/bash
#
# ***************************************************************************
# Name                 : mk_tiles
# Description          : Make TMS from image 
#
# Arguments: 
# $1: Image for tiles
# $2: Zoom min
# $3: Zoom max
# $4: Diretory TMS
# $5: Diretory PNG
# $6: URL for TMS
#
# Dependencies         : gdal 1.10.1, dans-gdal-script 0.23-2(gdal_contrast_stretch), tilers-tools 3.2.0(gdal_tiler.py), gdal_thumbnail.sh
#
# ***************************************************************************
# begin                : 2015-03-02 (yyyy-mm-dd)
# copyright            : (C) 2015 by Luiz Motta
# email                : motta dot luiz at gmail.com
# ***************************************************************************
#
# Revisions
#
# 2015-07-16
# - Added tag <TargetWindow> from image in GDAL_WMS
# 2015-04-25:
# - Remove input number of R G B bands
#
# ***************************************************************************
#
# Examples:
#   CBERS (bands 2, 3 and 4):
#   mk_tiles.sh 173-112_20080826_CBERS2B_CCD_B234_RET.tif 3 15 /public/tms /public/jpg http://10.1.8.20/tms
#
#   Rapid Eye (bands 4, 5 and 3)
#   mk_tiles.sh 2034016_2011-05-28T152704_RE1_3A-NAC_11056706_149189.tif 3 17 /public/tms /public/jpg
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
calc_extent_json(){
  local tmp_file=$(mktemp)
  gdalinfo -nogcp -nomd -norat -noct $in_img > $tmp_file
  local ul=$(cat $tmp_file | grep "Upper Left" | cut -d'(' -f2 | cut -d')' -f1 | sed  's/[[:blank:]]*//g')
  local lr=$(cat $tmp_file | grep "Lower Right" | cut -d'(' -f2 | cut -d')' -f1 | sed  's/[[:blank:]]*//g')
  local epsg=$(cat $tmp_file | grep EPSG | grep "]]$" | cut -d'[' -f2 | cut -d',' -f2 | cut -d']' -f1 | sed 's/"//g' )
  rm $tmp_file
  local ok_ul=$(expr length "$ul")
  local ok_lr=$(expr length "$lr")
  local ok_epsg=$(expr length "$epsg")
  if [ $ok_ul -eq 0 -o $ok_lr -eq 0 -o $ok_epsg -eq 0 ] ; then
    isok=0
    return
  fi
  extent_json="{
                \"type\": \"FeatureCollection\",
                \"crs\": { \"type\": \"name\", \"properties\": { \"name\": \"urn:ogc:def:crs:EPSG::"$epsg"\" } },
                \"features\": [
                   { \"type\": \"Feature\", 
                     \"properties\": { \"name\": \"UpperLeft\"}, 
                     \"geometry\": { 
                        \"type\": \"Point\", 
                        \"coordinates\": [ "$ul" ] 
                     } 
                   },
                   { \"type\": \"Feature\", 
                     \"properties\":{ \"name\": \"LowerRight\"}, 
                     \"geometry\": { 
                        \"type\": \"Point\", 
                        \"coordinates\": [ "$lr" ] 
                     } 
                   }
                ]
               }"
  isok=1
}
#
calc_target_window(){
  local tmp_file=$(mktemp)
  local extent_json3857="tmp.geojson"
  local tmp_dir=$(mktemp -d)
  echo $extent_json > $tmp_file
  ogr2ogr -t_srs EPSG:3857 -f GeoJSON $tmp_dir"/"$extent_json3857 $tmp_file
  #
  local ulx=$(cat $tmp_dir"/"$extent_json3857 | grep "UpperLeft" | cut -d':' -f7 | cut -d',' -f1 | cut -d'[' -f2 | sed  's/[[:blank:]]*//g')
  local uly=$(cat $tmp_dir"/"$extent_json3857 | grep "UpperLeft" | cut -d':' -f7 | cut -d',' -f2 | cut -d']' -f1 | sed  's/[[:blank:]]*//g')
  local lrx=$(cat $tmp_dir"/"$extent_json3857 | grep "LowerRight" | cut -d':' -f7 | cut -d',' -f1 | cut -d'[' -f2 | sed  's/[[:blank:]]*//g')
  local lry=$(cat $tmp_dir"/"$extent_json3857 | grep "LowerRight" | cut -d':' -f7 | cut -d',' -f2 | cut -d']' -f1 | sed  's/[[:blank:]]*//g')
  # clean
  rm -r $tmp_dir
  rm $tmp_file
  #
  local ul="<UpperLeftX>"$ulx"</UpperLeftX><UpperLeftY>"$uly"</UpperLeftY>"
  local lr="<LowerRightX>"$lrx"</LowerRightX><LowerRightY>"$lry"</LowerRightY>"
  target_window="<TargetWindow>"$ul" "$lr"</TargetWindow>"
}
#
calc_gdal_tms(){
gdal_tms="<GDAL_WMS>
    <Service name=\"TMS\">
        <ServerUrl>"$url"/"$name_img".tms/\${z}/\${x}/\${y}.png</ServerUrl>
        <SRS>EPSG:3857</SRS>
        <ImageFormat>image/png</ImageFormat>
    </Service>
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
    "$target_window"
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
  echo "Usage: $name_script <Image> <Zoom Min> <Zoom Max> <Dir TMS> <Dir PNG> <URL>" >&2
  echo "<Image> is the image for TMS" >&2
  echo "<Zoom Min> Zoom minimum of TMS" >&2
  echo "<Zoom Max> Zoom maximum of TMS" >&2
  echo "<Dir PNG> Directory for PNG" >&2
  echo "<Dir TMS> Directory for TMS" >&2
  echo "<URL> URL for TMS" >&2
}
#
totalargs=6
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
in_img=$1
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
zmin=$2
zmax=$3
dir_png=$4
if [ ! -d "$dir_png" ] ; then
  echo "The Directory '$dir_png' not exist" >&2
  exit 1
fi
dir_tms=$5
if [ ! -d "$dir_tms" ] ; then
  echo "The Directory '$dir_tms' not exist" >&2
  exit 1
fi
url=$6
#
dir_img=$(dirname $in_img)
basename_img=$(basename $in_img)
name_img=${basename_img%.*}
fgdal_tms_xml=$dir_tms"/"$name_img"_tms.xml"
fpng=$dir_png"/"$name_img".png"
#
nodata=0
mode='tms'
#
dateini=$(date +"%Y%m%d %H:%M:%S")
arg=$name_img"("$dateini")...1"
printf "%s" "$arg"
#
# Remove gdal_contrast_stretch
#
gdal_thumbnail.sh $in_img 30  > /dev/null
mv $dir_img"/"$name_img".png" $fpng
#
printf ".2"
gdal_tiler.py -q -p $mode --src-nodata $nodata,$nodata,$nodata --zoom $zmin:$zmax -t $dir_tms $in_img
#
calc_extent_json
if [[ $isok == 0 ]]; then
  msg_error
  exit 1
fi
calc_target_window
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
