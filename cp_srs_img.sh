#!/bin/bash
#
#
#### Functions
#
msg_error(){
  local name_script=$(basename $0)
  echo "Total of arguments is $runargs"  >&2
  echo "Usage: $name_script <image_source> <image_target>" >&2
  echo "<image_source> is the file of image with spatial reference systems(SRS)" >&2
  echo "<image_target> is the file of image will be set with SRS" >&2
  exit 1
}
#
calc_params_image(){
  # Spatial Reference System - By file
  srs_def=$(dirname $r_img)"/"$(basename  ${r_img%.*}".wkt")
  echo $(gdalsrsinfo -o wkt $r_img) > $srs_def
  #
  local tmpinfo=$(mktemp)
  gdalinfo $r_img > $tmpinfo
  # 
  local origin=$(cat $tmpinfo | grep "Upper Left" | cut -d'(' -f2 | cut -d')' -f1)
  ulx=$(echo $origin | cut -d',' -f1)
  uly=$(echo $origin | cut -d',' -f2)
  #  
  origin=$(cat $tmpinfo | grep "Lower Right" | cut -d'(' -f2 | cut -d')' -f1)
  lrx=$(echo $origin | cut -d',' -f1)
  lry=$(echo $origin | cut -d',' -f2)
  #
  # Resolution
  local res_xy=$(cat $tmpinfo | grep "Pixel Size" | cut -d'(' -f2 | cut -d')' -f1)
  xres=$(echo $res_xy | cut -d',' -f1)
  yres=$(echo $res_xy | cut -d',' -f2)
  #
  rm $tmpinfo
}
#
runargs=$#
totalargs=2
#
if [ $runargs -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
r_img=$1
w_img=$2
#
if [ ! -f "$r_img" ] ; then
  printf "Not found file '%s'\n" $r_img
  msg_error
  exit 1
fi
if [ ! -f "$w_img" ] ; then
  printf "Not found file '%s'\n" $w_img
  msg_error
  exit 1
fi
#
printf "Setting Spatial Reference Systems in "$w_img"..."
#
calc_params_image
# Set  SRS
gdal_edit.py -unsetgt $w_img
gdal_edit.py -a_srs $srs_def -a_ullr $ulx $uly $lrx $lry $w_img
gdal_edit.py -tr $xres $yres $w_img
rm $srs_def
#
printf "\r%-100s\n" "'$w_img' with Spatial Reference Systems!"
