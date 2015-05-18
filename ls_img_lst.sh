#!/bin/bash
#
# ***************************************************************************
# Name                 : ls_img_lst
# Description          : Count the number of items in lists in current directory
#
# Arguments            : None
#
# Dependencies         : None
#
# ***************************************************************************
# begin                : 2015-05-18 (yyyy-mm-dd)
# copyright            : (C) 2015 by Luiz Motta
# email                : motta dot luiz at gmail.com
# ***************************************************************************
#
# Revisions
#
# 2015-05-18
# - Start
#
# ***************************************************************************
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
for item in $(ls -1 *.lst); do lst=$(echo $item | cut -d'.' -f1); total=$(cat $item | wc -l); echo "$lst = $total"; done 
