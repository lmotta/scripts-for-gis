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
  echo "<gcp_bb> is the file of GCP" >&2
  echo "<out_dir> is the directy for write news imagens" >&2
  exit 1
}
#
runargs=$#
totalargs=3
#
if [ $runargs -ne $totalargs ] ; then
  msg_error
  exit 1
fi
#
r_img=$1
cr_gcp=$2
out_dir=$3
#
#
if [ ! -f "$r_img" ] ; then
  printf "Not found file '%s'\n" $r_img
  msg_error
  exit 1
fi
if [ ! -f "$cr_gcp" ] ; then
  printf "Not found file '%s'\n" $cr_gcp
  msg_error
  exit 1
fi
if [ ! -d "$out_dir" ] ; then
  printf "Not found directory '%s'\n" $out_dir
  msg_error
  exit 1
fi
#
#
wkt=$(gdalsrsinfo -o wkt $r_img)
gcp=$(tail -n +2  $cr_gcp | awk '{printf("%s %s %s %s %s\n", "-gcp",$2,$3,$4,$5)}')
#
#
w_img=$out_dir"/"$(basename  ${r_img%.*}"_cr.tif")
edit_img=$out_dir"/"$(basename ${r_img%.*})"_edit.${r_img##*.}"
prj_img=$out_dir"/"$(basename  ${r_img%.*}".prj")
#
cp $r_img $edit_img
gdal_edit.py -unsetgt $gcp $edit_img
echo $wkt > $prj_img
#
printf "Warpping..."
#
gdalwarp -multi -q -overwrite -t_srs $prj_img -order 1 -r cubic $edit_img $w_img
rm $edit_img
#
printf "\r%-100s\n" "$w_img created!
