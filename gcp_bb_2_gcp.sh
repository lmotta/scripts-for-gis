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
  echo "<gcp_bb> is the file of GCP" >&2
  exit 1
}
#
calc_params_image(){
  local tmpinfo=$(mktemp)
  #
  gdalinfo $1 > $tmpinfo
  # Origin
  local origin=$(cat $tmpinfo | grep "Upper Left" | cut -d'(' -f2 | cut -d')' -f1)
  x0=$(echo $origin | cut -d',' -f1)
  y0=$(echo $origin | cut -d',' -f2)
  # Resolution
  local res_xy=$(cat $tmpinfo | grep "Pixel Size" | cut -d'(' -f2 | cut -d')' -f1)
  res_x=$(echo $res_xy | cut -d',' -f1)
  res_y=$(echo $res_xy | cut -d',' -f2)
  #
  rm $tmpinfo
}
#
calc_georef_xy(){
  local pixel_x=$1
  local pixel_y=$2
  georef_x=$(echo "$x0 + $res_x * $pixel_x" | bc )
  georef_y=$(echo "$y0 + $res_y * $pixel_y" | bc )
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
w_gcp_tmp=$(mktemp)
w_gcp_georef=$(dirname $r_gcp)"/"$(basename ${r_gcp%.*}"_georef.gcp")
w_gcp_raw=$(dirname $r_gcp)"/"$(basename ${r_gcp%.*}"_raw.gcp")
#
printf "Creating GCP's..."
#
touch $w_gcp_georef
touch $w_gcp_raw
tail -n +2  $r_gcp | awk '{printf("%s;%s;%s;%s\n", $2,$3,$4,$5)}' > $w_gcp_tmp
#
calc_params_image $r_img
for item in $(cat $w_gcp_tmp)
  do 
    pixel_x=$(echo $item | cut -d';' -f1)
    pixel_y=$(echo $item | cut -d';' -f2)
    ref_x=$(echo $item | cut -d';' -f3)
    ref_y=$(echo $item | cut -d';' -f4)
    calc_georef_xy $pixel_x $pixel_y
    georef_cr=$(echo $item | cut -d';' -f34)
    echo "-gcp $pixel_x $pixel_y $ref_x $ref_y"   >> $w_gcp_raw
    echo "-gcp $georef_x $georef_y $ref_x $ref_y" >> $w_gcp_georef
  done
rm $w_gcp_tmp
#
printf "\r%-100s\n" "'$w_gcp_georef' and '$w_gcp_raw' created!"
