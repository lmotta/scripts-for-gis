#!/bin/bash
#
# ***************************************************************************
# Name                 : 16bit 2 8bit Kdialog
# Description          : Convert 16 to 8 bits. Using Kdialog Change original image!
#
# Arguments: 
# $1: Image with 16bits
#
# Dependencies         : KDE and 16_2_8b_convert.sh
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
title="16b_to_8b_convert"
img=$(kdialog --title $title --getopenfilename $HOME "*.* |Images type")
if [ -f "$img" ]
then
  kdialog --title $title --passivepopup "Processing:\n$img" 5
  if msg=$(16b_2_8b_convert.sh $img)
    then
      kdialog --title $title --msgbox "Finished.\n\n$img"
    else
      kdialog --title $title --sorry "Error!.\n\n$img\n\n$msg"
  fi
else
  kdialog --title $title  --sorry "Not selected file."
fi
