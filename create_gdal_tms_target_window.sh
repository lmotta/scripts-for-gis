#!/bin/bash
#
# ***************************************************************************
# Name                 : GDAL TMS with TargetWindow
# Description          : Create GDAL TMS with tag <TargetWindow> from image.
#                        Use for input in GDAL_WMS driver and use by QGIS for zoom to image in TMS format
# Arguments: 
# $1: Image
# $2: url
# $3: zmax
#
# Dependencies         : gdal 1.10.1 (gdalinfo, ogr2ogr)
#
# ***************************************************************************
# begin                : 2015-10-10 (yyyy-mm-dd)
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
#   get_target_win.sh LC8_229-066_20140724_LGN00_r6g5b4.tif
#
# ***************************************************************************
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or     *
# *   (at your option) any later version.                                   *
# *                                                                         *
# *************gdal_tms**************************************************************
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
  echo "Usage: $name_script <image> <url> <zmax>" >&2
  echo "<image> is the image" >&2
  echo "* NEED keys: Lower Right, Upper Left and EPSG by output: gdalinfo image" >&2
  echo "<url> URL for TMS" >&2
  echo "<zmax> Maximum zoom level" >&2
  exit 1
}
#
totalargs=3
#
if [ $# -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
in_img=$1
url=$2
zmax=$3
#
if [ ! -f "$in_img" ] ; then
  echo "The file '$in_img' not exist" >&2
  exit 1
fi
#
basename_img=$(basename $in_img)
name_img=${basename_img%.*}
fgdal_tms_xml=$name_img"_tms.xml"
#
calc_extent_json
if [[ $isok == 0 ]]; then
  msg_error
  exit 1
fi
calc_target_window
calc_gdal_tms
echo $gdal_tms > $fgdal_tms_xml
