#!/bin/bash
#
# ***************************************************************************
# Name                 : Footprint Kdialog
# Description          : Create footprint of image with GeoJSON format. Using Kdialog.
#
# Arguments: 
# $1: Image
#
# Dependencies         : KDE and footprint.sh
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
#   footprint_kdialog.sh
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
title="Footprint_of_image"
img=$(kdialog --title $title --getopenfilename $HOME "*.* |Images type")
if [ -f "$img" ]
then
  kdialog --title $title --passivepopup "Processing:\n$img" 5
  if msg=$(footprint.sh $img)
    then
      kdialog --title $title --msgbox "Finished.\n$msg"
    else
      kdialog --title $title --sorry "Error!.\n$msg"
  fi
else
  kdialog --title $title --passivepopup "Not Select File!" 5
fi
