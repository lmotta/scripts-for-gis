<!-- IBAMA logo -->
[ibama_logo]: http://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Logo_IBAMA.svg/150px-Logo_IBAMA.svg.png

![][ibama_logo]  
[Brazilian Institute of Environment and Renewable Natural Resources](http://www.ibama.gov.br)

# Scripts for GIS by Luiz Motta
* This package consists of a number of scripts utilities for use in conjunction with GDAL, tilers-tools and dans-gdal-scripts.  
* Started: 2015-03-05  
* Version: 0.1  

## Scripts

### 16b_2_8b_convert.sh
* Convert images of 16 to 8 bits  
* Dependeces: gdal 1.10.1 (gdal_translate, gdalinfo, gdalbuildvrt)  
* Example (using parallel):  
ls -1 *.tif | parallel 16b_2_8b_convert.sh {}  

### 16b_2_8b_convert_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: 16b_2_8b_convert.sh  

### footprint.sh
* Create GeoJson with border's polygon of image (limited with valid pixels)  
* Dependeces: gdal 1.10.1(gdal_calc.py, gdal_sieve.py, gdal_edit.py and gdal_polygonize.py)  
* Example (using parallel):  
ls -1 *.tif | parallel  footprint.sh {}  

### footprint_add_url_tms.sh
* Add URL of TMS in footprint(GeoJson)  
* Dependeces: None  
* Example (using parallel):  
ls -1 *.geojson | parallel  footprint_add_url_tms.sh {} http://10.1.8.20/test_lmotta  

### convexhull_geojson.py
* Create convexhul from Geojson (used to soften the footprint)
* Dependeces:  GDAL Python bindings 1.10.1
* Example (using parallel):  
ls -1 *.geojson | parallel convexhull_geojson.py {}  

### convexhull_geojson_kdialog.sh
* Using Kdialog (KDE)
* Dependeces: convexhull_geojson.py  

### footprint_append_shp.sh
* Adds the footprint (GeoJson) inside shapefile (if not exist it is created)  
* Dependeces: gdal 1.10.1(ogr2ogr)  
* Example (NOT USE parallel!):  
for item in $(ls -1 *.geojson); do footprint_append_shp.sh \$item LC8_footprint.shp; done

### thumbnail_gdal.sh
* Create thumbnail file(PNG) from image  
* Dependeces: gdal 1.10.1(gdal_translate)  
* Example (use parallel!):  
ls -1 *.tif | parallel thumbnail_gdal.sh {} 30  

### mk_tiles.sh
* Create TMS structure (directories and files) and XML for GDAL_WMS driver from image  
* Dependeces: gdal 1.10.1(gdalbuildvrt), dans-gdal-script 0.23-2(gdal_contrast_stretch), tilers-tools   3.2.0(gdal_tiler.py), thumbnail_gdal.sh  
* Example (use parallel!):  
ls -1 *.tif | parallel mk_tiles.sh {} 1 2 3 2 12 ./png ./tms http://10.1.8.20/test_lmotta  

## Packages used by script

### gdal
* Version:  1.10.1  
* Source: www.gdal.org  
* Ubuntu 14.04: installed by QGIS 2.8.1 or by Ubuntu GIS unstable  

### dans-gdal-script
* Version:  0.23-2  
* Source: https://github.com/gina-alaska/dans-gdal-scripts  
* Ubuntu 14.04: available in the Ubuntu repository  

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