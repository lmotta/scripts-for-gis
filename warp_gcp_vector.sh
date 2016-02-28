#!/bin/bash
#
#
#### Functions
#
msg_error(){
  local name_script=$(basename $0)
  echo "Total of arguments is $runargs"  >&2
  echo "Usage: $name_script <shp_original> <gcp>" >&2
  echo "<shp_original> is the file of original shapefile to warp" >&2
  echo "<gcp> is the file of GCP(Georef)" >&2
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
r_shp=$1
r_gcp=$2
#
if [ ! -f "$r_shp" ] ; then
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
w_shp=$(dirname $r_shp)"/"$(basename ${r_shp%.*}"_warp.shp")
#
gcp=$(cat $r_gcp)
#
printf "Warpping..."
#
ogr2ogr -overwrite $gcp -order 1 $w_shp $r_shp
#
printf "\r%-100s\n" "'$w_shp' created!"
