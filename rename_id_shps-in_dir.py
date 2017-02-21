#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/***************************************************************************
Name                 : rename_id_shps-in_dir
Description          : Rename shapefiles files by the ID of root directory
Arguments            : Diretory for scan shapefiles

                       -------------------
begin                : 2017-02-20
copyright            : (C) 2017 by Luiz Motta
email                : motta dot luiz at gmail.com
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
import os, sys, fnmatch, argparse


def run(rootDir):
  def renameFiles(root, filenames, idDir, idFile):
    vwildcard3 = "{0}.*".format( os.path.splitext( filename )[0] )
    filter2 = fnmatch.filter( filenames, vwildcard3 ) # names start with idFile         
    for name in filter2:
      newname = name.replace(idFile, idDir)
      vold = os.path.join(root, name )
      vnew = os.path.join(root, newname )
      try:
        os.rename( vold, vnew)
      except OSError as e:
        sys.stdout.write(" - Error '{0}'".format( name ) )
    
  if not os.path.isdir( rootDir ):
    msg = "'{0}' is not valid directory\n.".format( rootDir )
    sys.stderr.write( msg )
    return 1

  vext= 'shp'
  vwildcard1 = "*.{0}".format( vext )
  vwildcard2 = vwildcard1.upper()
  totalRename = 0
  for root, dirnames, filenames in os.walk( rootDir ):
    l_filter1 = fnmatch.filter( filenames, vwildcard1 ) + fnmatch.filter( filenames, vwildcard2 )
    idDir = root.split(os.path.sep)[-1].split('_')[0]
    for filename in l_filter1:
      idFile = filename.split('_')[0]
      if idDir == idFile:
        continue
      totalRename += 1
      sys.stdout.write( "\r{0:100s}".format( '' ) ) # Clean
      msg = "\rRename '{0}' with id '{1}'".format( filename, idDir )
      sys.stdout.write( msg )
      renameFiles( root, filenames, idDir, idFile )
  if totalRename == 0:
    msg = "Not need rename shapefiles"
  else:
    msg = "Finished (total = {0})".format(totalRename)
  sys.stdout.write( "\r{0:100s}\n".format( msg ) )
  return 0

def main():
  d = "Rename shapefiles files by the ID of root directory."
  parser = argparse.ArgumentParser(description=d )

  d = "Root of directories"
  parser.add_argument('vroot', metavar='vroot', type=str, help=d )

  args = parser.parse_args()
  return run( args.vroot )

if __name__ == "__main__":
    sys.exit( main() )
