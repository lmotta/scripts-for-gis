#!/bin/bash
#
#
#### Functions
#
msg_error(){
  local name_script=$(basename $0)
  echo "Total of arguments is $runargs"  >&2
  echo "Usage: $name_script <image_original> <gcp_bb> <out_dir>" >&2
  echo "<image_original> is the file of original image to warp" >&2
  echo "<gcp> is the file of GCP(RAW)" >&2
  exit 1
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
w_edit_img=$(dirname $r_img)"/"$(basename  ${r_img%.*}"_edit.tif")
w_prj=$(dirname $r_img)"/"$(basename  ${r_img%.*}".prj")
#
printf "Warpping..."
cp $r_img $w_edit_img
gcp=$(cat $r_gcp)
gdal_edit.py -unsetgt $gcp $w_edit_img
#
wkt=$(gdalsrsinfo -o wkt $r_img)
echo $wkt > $w_prj
#
gdalwarp -multi -q -overwrite -t_srs $w_prj -order 1 -r cubic $w_edit_img $w_img
printf "\r%-100s\n" "'$w_img' created!"
rm $w_edit_img $w_prj
