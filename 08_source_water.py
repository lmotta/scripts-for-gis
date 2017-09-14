# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : Examples of Python PyQGIS course IBAMA
Description          : Examples of Python PyQGIS course IBAMA
Date                 : September, 2017
copyright            : (C) 2017 by Luiz Motta
email                : motta.luiz@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
##Curso PyQGIS=group
##Nascentes=name

##Rios=vector line
##Nascentes=output vector

from PyQt4 import QtCore
from qgis import core as QgsCore
from processing.tools.vector import VectorWriter
from qgis.utils import iface

def existNodeCheckFid(node, l_fid_node, fid):
    for fn in l_fid_node:
        if not fid == fn['fid'] and node == fn['node']:
            fn['exists'] = True
            return True
    return False

def existNode(node, l_fid_node, fid):
    for fn in l_fid_node:
        if node == fn['node']:
            fn['exists'] = True
            return True
    return False


def populateListFidNode(fid, line, l_fid_node, funcExist):
    node1, node2 = line[0], line[-1]
    if not funcExist( node1, l_fid_node, fid ):
       l_fid_node.append( {'fid': fid, 'node': node1, 'exists': False } )
    if not funcExist( node2, l_fid_node, fid ):
       l_fid_node.append( {'fid': fid, 'node': node2, 'exists': False } )

# Input
lyrRiver = processing.getObject( Rios )

# Processing
l_fid_node = [] # [ {fid, node, exists}, ...]
totFeats = lyrRiver.featureCount()
c = 0.0
for feat in lyrRiver.getFeatures():
    c += 1
    perc = c / totFeats * 100
    progress.setPercentage( perc )

    fid = feat.id()
    geom = feat.geometry()
    if geom.isMultipart():
        lines = geom.asMultiPolyline()
        funcExist = existNode
        for line in lines:
            populateListFidNode(-1, line, l_fid_node, funcExist )
    else:
        line = geom.asPolyline()
        funcExist = existNodeCheckFid
        populateListFidNode(fid, line, l_fid_node, funcExist )

# Remove Exists nodes
for id in reversed( xrange( len( l_fid_node ) ) ):
    if l_fid_node[ id ]['exists']:
        l_fid_node.pop( id )

# Remove nodes with same FID line
ids_remove = []
for id in xrange( len( l_fid_node )-1 ):
    fid1, fid2 = l_fid_node[ id ]['fid'], l_fid_node[ id+1 ]['fid']
    if fid1 == fid2:
        ids_remove.append( id )
        ids_remove.append( id+1 )
ids_remove.reverse()
for id in ids_remove:
    l_fid_node.pop( id )

# Output
fields = [ QgsCore.QgsField("fid_line", QtCore.QVariant.Int ) ]
lyrSource = VectorWriter( Nascentes, None, fields, QgsCore.QGis.WKBPoint, lyrRiver.crs() )
for fn in l_fid_node:
    feat = QgsCore.QgsFeature()
    feat.setAttributes( [ fn['fid'] ])
    feat.setGeometry( QgsCore.QgsGeometry.fromPoint( fn['node']) )
    lyrSource.addFeature( feat )
    del feat
del lyrSource
