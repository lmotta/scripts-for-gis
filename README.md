<!-- IBAMA logo -->
[ibama_logo]: http://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Logo_IBAMA.svg/150px-Logo_IBAMA.svg.png

![][ibama_logo]  
[Brazilian Institute of Environment and Renewable Natural Resources](http://www.ibama.gov.br)

# Scripts for GIS by Luiz Motta
* This package consists of a number of scripts utilities for use in conjunction with GDAL and tilers-tools.  
* Started: 2015-03-05  
* Version: 0.1  

## Scripts

### 2_rgb.sh
* Create RGB image (Ex.: image_r3g4b5.tif) 
* Dependeces: gdal 1.10.1 (gdal_translate)  
* Example (using parallel):  
nohup parallel 2_rgb.sh {} 2 4 5 < LIST_OF_IMAGES  

### 16b_2_8b_convert.sh
* Convert images of 16 to 8 bits (overwrite original file)  
* Dependeces: gdal 1.10.1 (gdal_translate, gdalinfo, gdalbuildvrt)  
* Example (using parallel):  
ls -1 *.tif | parallel 16b_2_8b_convert.sh {}  
nohup parallel 16b_2_8b_convert.sh {} < LIST_OF_IMAGES  

### 16b_2_8b_convert_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: 16b_2_8b_convert.sh  

### check_error_img.sh
* Check error for read image(print ERROR if exist error)  
* Dependeces: gdal 1.10.1 (gdalinfo)  
* Example (using parallel):  
nohup parallel check_error_img.sh {} < LIST_OF_IMAGES  

### create_gdal_tms_target_window.sh
* Create GDAL_WMS file (XML) from image with no standard TAG <TargetWindows>  
* Dependeces: gdal 1.10.1 (gdalinfo, ogr2ogr)  
* Example:  
create_gdal_tms_target_window.sh [IMAGE] MAX_ZOOM


### footprint.sh
* Create GeoJson with border's polygon of image (limited with valid pixels)  
* Dependeces: gdal 1.10.1(gdal_calc.py, gdal_sieve.py, gdal_edit.py and gdal_polygonize.py)  
* Example (using parallel):  
nohup parallel footprint.sh {} < LIST_OF_IMAGES  

### footprint_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: footprint.py  

### footprint_add_url_tms.sh
* Add URL of TMS in footprint(GeoJson) * NOT USE for others Geojson  
* Dependeces: None  
* Example (using parallel):  
nohup parallel footprint_add_url_tms.sh {} http://10.1.8.20/test_lmotta < LIST_OF_IMAGES  

### footprint_convexhull.py
* Create convexhull from Geojson (used to soften the footprint)
* Dependece: GDAL Python bindings 1.10.1
* Example (using parallel):  
nohup parallel footprint_convexhull.sh {}  < LIST_OF_IMAGES  

### footprint_convexhull_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: footprint_convexhull.py

### footprint_extent.py
* Create extent of image16b_2_8b_convert
* Dependece: GDAL Python bindings 1.10.1
* Example (using parallel):  
nohup parallel footprint_extent.sh {}  < LIST_OF_IMAGES  

### footprint_extent_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: footprint_extent.py  

### footprint_append_shp.sh
* Adds the footprint (GeoJson), all Geojson, inside shapefile (if not exist it is created)  
* Dependeces: gdal 1.10.1(ogr2ogr)  
* Example (NOT USE parallel!):  
for item in $(ls -1 *.geojson); do footprint_append_shp.sh $item LC8_footprint.shp; done

### gdal_thumbnail.sh
* Create thumbnail file(PNG) from image  
* Dependeces: gdal 1.10.1(gdal_translate)  
* Example (use parallel!):  
nohup parallel gdal_thumbnail.sh {} 30 < LIST_OF_IMAGES  

### mk_tiles.sh
* Create TMS structure (directories and files) and XML for GDAL_WMS driver from image  
* Dependeces: dans-gdal-script 0.23-2(gdal_contrast_stretch), tilers-tools   3.2.0(gdal_tiler.py), gdal_thumbnail.sh  
* Example (use parallel!):  
nohup parallel mk_tiles.sh {} 2 17 ./png ./tms http://10.1.8.20/test_lmotta < LIST_OF_IMAGES  

### ls_img_lst.sh
* Count the number of items in lists in current directory
* Dependeces: None
* Example:  
ls_img_lst.sh

## Packages used by script

### gdal
* Version:  1.10.1  
* Source: www.gdal.org  
* Ubuntu 14.04: installed by QGIS 2.8.1 or by Ubuntu GIS unstable  

### tilers-tools
* Version:  3.2.0  
* Source: https://code.google.com/p/tilers-tools/  
* Ubuntu 14.04: download  by source  

### Parallel
* Version: 20130922-1  
* Source: https://www.gnu.org/software/parallel/  
* Ubuntu 14.04: available in the Ubuntu repository  

## Credits
These programs were written by Luiz Motta.  
Send questions or comments to [motta.luiz@gmail.com](motta.luiz@gmail.com).  
 
This software is provided "AS IS."
