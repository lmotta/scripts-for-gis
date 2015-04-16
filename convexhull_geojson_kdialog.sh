#!/bin/bash
#
# ***************************************************************************
# Name                 : convexhull_geojson Kdialog
# Description          : Create convex hull. Using Kdialog
#
# Arguments: 
# $1: Shapefile
#
# Dependencies         : KDE and convexhull_geojson.py
#
# ***************************************************************************
# begin                : 2015-04-15 (yyyy-mm-dd)
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
#   16b_2_8b_convert_Kdialog.sh
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
title="Convexhull_geojson"
fileOgr=$(kdialog --title $title --getopenfilename $HOME "*.geojson |Geojson")
if [ -f "$fileOgr" ]
then
  kdialog --title $title --passivepopup "Processing:\n$fileOgr" 5
  if msg=$(convexhull_geojson.py $fileOgr)
    then
      kdialog --title $title --msgbox "Finished.\n$msg"
    else
      kdialog --title $title --sorry "Error!.\n\n$fileOgr\n\n$msg"
  fi
else
  kdialog --title $title  --sorry "Not selected file."
fi
