from osgeo import gdal, osr

def shiftNorth2South(ds):
    gt = list( ds.GetGeoTransform() )
    gt[3] += 10000000
    ds.SetGeoTransform( tuple( gt ) )
    ds.FlushCache() # Save in disk

def setProjectionNorth2South(ds):
    sr = osr.SpatialReference( ds.GetProjection() )
    epsg = int(sr.GetAttrValue('AUTHORITY',1))
    epsg += 100 # South
    sr = None
    sr = osr.SpatialReference()
    sr.ImportFromEPSG( epsg )
    ds.SetProjection( sr.ExportToWkt() )
    ds.FlushCache() # Save in disk

def warptoWgs84(pathfile):
    pathfileWgs84 = "{}_wgs84.tif".format( pathfile[:-4] )
    ds = gdal.Open( pathfile )
    dsWgs84 = gdal.Warp( pathfileWgs84, ds, dstSRS='EPSG:4326')
    ds = None
    dsWgs84 = None
    driver = gdal.GetDriverByName('GTiff')
    driver.Delete( pathfile )

def utm_North2South(pathfile):
    ds = gdal.Open( pathfile , gdal.GA_Update)
    shiftNorth2South( ds )
    setProjectionNorth2South( ds)
    ds = None
    warptoWgs84( pathfile )
    
pfs = [
    '/home/lmotta/Documentos/casa/2019/Giovana/2019-01-30/imagens_work/MT_10_230067_20151022.tif',
    '/home/lmotta/Documentos/casa/2019/Giovana/2019-01-30/imagens_work/MT_20_229070_20150727.tif',
    '/home/lmotta/Documentos/casa/2019/Giovana/2019-01-30/imagens_work/MT_65_228070_20150821.tif'
]
for pf in pfs:
    utm_North2South( pf )
