#!/bin/bash
#
#
#### Functions
#
msg_error(){
  local name_script=$(basename $0)
  echo "Total of arguments is $runargs"  >&2
  echo "Usage: $name_script <image_original> <gcp_bb>" >&2
  echo "<image_original> is the file of original image to warp" >&2
  echo "<gcp> is the file of GCP(RAW)" >&2
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
r_gcp=$2
#
if [ ! -f "$r_img" ] ; then
  printf "Not found file '%s'\n" $r_img
  msg_error
  exit 1
fi
if [ ! -f "$r_gcp" ] ; then
  printf "Not found file '%s'\n" $r_gcp
  msg_error
  exit 1
fi
#
w_img=$(dirname $r_img)"/"$(basename ${r_img%.*}"_warp.tif")
#
printf "Warpping..."
#
calc_params_image
gcp=$(cat $r_gcp)
# Cleanup Image and set GCP and Warp
gdal_edit.py -unsetgt $gcp $r_img
# Warp resample (-r ): cubic(useb byt CR) near(classification)
#gdalwarp -t_srs $srs_def -order 1 -tr $xres $yres -te $ulx $lry $lrx $uly -r cubic -multi -q -setci -overwrite  $r_img $w_img
gdalwarp -t_srs $srs_def -order 1 -ts 5000 5000 -te $ulx $lry $lrx $uly -r near -multi -q -setci -overwrite  $r_img $w_img
# Set original SRS
rm $r_img".aux.xml"
gdal_edit.py -unsetgt $r_img
gdal_edit.py -a_srs $srs_def -a_ullr $ulx $uly $lrx $lry $r_img
gdal_edit.py -tr $xres $yres $r_img
rm $srs_def
#
printf "\r%-100s\n" "'$w_img' created!"
