# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 10:18:07 2018

@author: cmi001


https://pcjericks.github.io/py-gdalogr-cookbook/index.html
https://pcjericks.github.io/py-gdalogr-cookbook/geometry.html
https://gis.stackexchange.com/questions/301729/get-a-bounding-box-of-a-geometry-that-crosses-the-antimeridian-using-ogr


https://trac.osgeo.org/gdal/browser/trunk/gdal/data
https://github.com/Toblerity/Fiona/issues/656
https://github.com/conda-forge/gdal-feedstock/blob/bc867e5b7ce459dd29a418e1d83c5b2f922b8d13/recipe/scripts/activate.bat#L4-L7
gdalsrsinfo.exe "EPSG:4326"

ERROR 6: EPSG PCS/GCS code 4326 not found in EPSG support files.  Is this a valid EPSG coordinate system?
"""
import os
import datetime
import calendar

import numpy as np
import matplotlib.pyplot as plt

import ogr
import pprint
# pprint.pprint(list(map(lambda f: (f, getattr(ogr, f)), list(filter(lambda x: x.startswith('wkb'), dir(ogr))))))


# from ogr cookbook https://pcjericks.github.io/py-gdalogr-cookbook/layers.html
def create_buffer(inputfn, output_bufferfn, buffer_dist):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inputds = driver.Open(inputfn, 0)
    if inputds is None:
        raise  RuntimeError('Could not open %s' % (inputfn))    
    inputlyr = inputds.GetLayer()
    featureCount = inputlyr.GetFeatureCount()
    print('\tNumber of features in %s: %d' % (os.path.basename(inputfn), featureCount))
    inputdef = inputlyr.GetLayerDefn()
    for i in range(inputdef.GetFieldCount()):
        inputfName =  inputdef.GetFieldDefn(i).GetName()
        inputfTypeCode = inputdef.GetFieldDefn(i).GetType()
        inputfTypeName = inputdef.GetFieldDefn(i).GetFieldTypeName(inputfTypeCode)
        inputfWidth = inputdef.GetFieldDefn(i).GetWidth()
        inputfPrecision = inputdef.GetFieldDefn(i).GetPrecision()
        print('\t', i, inputfName, inputfTypeCode, inputfTypeName, inputfWidth, inputfPrecision)

    # prepare environment
    shpdriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(output_bufferfn):
        # os.remove(output_bufferfn)
        shpdriver.DeleteDataSource(output_bufferfn)
    
    # create file
    outputBufferds = shpdriver.CreateDataSource(output_bufferfn)

    # create layer
    bufferlyr = outputBufferds.CreateLayer(output_bufferfn, geom_type=ogr.wkbPolygon)

    # access layer
    featureDefn = bufferlyr.GetLayerDefn()

    # load features in all layers
    outFeature = None
    for feature in inputlyr:
        print('\t{}'.format(feature.GetField("ADM1_EN")))
        ingeom = feature.GetGeometryRef()

        # buffer features
        geomBuffer = ingeom.Buffer(buffer_dist)

        # create features
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(geomBuffer)
        bufferlyr.CreateFeature(outFeature)

        # deallocated features
        outFeature = None

def points_in_polygon(inputfn, pointcoords, pathOut):
    # load features
    # 0 means read-only. 1 means writeable.
    driver = ogr.GetDriverByName('ESRI Shapefile')
    inputds = driver.Open(inputfn, 0)

    if inputds is None:
        raise  RuntimeError('Could not open %s' % (inputfn))    
    inputlyr = inputds.GetLayer()
    
    featureCount = inputlyr.GetFeatureCount()
    print('\tNumber of features in %s: %d' % (os.path.basename(inputfn), featureCount))

    inputdef = inputlyr.GetLayerDefn()
    for i in range(inputdef.GetFieldCount()):
        inputfName =  inputdef.GetFieldDefn(i).GetName()
        inputfTypeCode = inputdef.GetFieldDefn(i).GetType()
        inputfTypeName = inputdef.GetFieldDefn(i).GetFieldTypeName(inputfTypeCode)
        inputfWidth = inputdef.GetFieldDefn(i).GetWidth()
        inputfPrecision = inputdef.GetFieldDefn(i).GetPrecision()
        print('\t', i, inputfName, inputfTypeCode, inputfTypeName, inputfWidth, inputfPrecision)

    minX, maxX, minY, maxY = float("infinity"), -float("infinity"), float("infinity"), -float("infinity")
    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        (tmp_minX, tmp_maxX, tmp_minY, tmp_maxY) = ingeom.GetEnvelope()
        if tmp_minX < minX:
            minX = tmp_minX
        if tmp_maxX > maxX:
            maxX = tmp_maxX
        if tmp_minY < minY:
            minY = tmp_minY
        if tmp_maxY > maxY:
            maxY = tmp_maxY
    inputlyr.ResetReading()

    # load points
    # check if polygon contains point
    icoord = 0
    in_poly = []
    in_bbox = {
        'id': [],
        'x': [],
        'y': []
    }
    for coord in pointcoords:
        # print('\t', icoord)
        is_contain = False
        
        if np.logical_and(minX <= coord[0] <= maxX,
                          minY <= coord[1] <= maxY):
            print('\tMascon id={}, xy={}'.format(icoord, coord))
            in_bbox['id'].append(icoord)
            in_bbox['x'].append(coord[0])
            in_bbox['y'].append(coord[1])
            
            for feature in inputlyr:
                ingeom = feature.GetGeometryRef()
                (tmp_minX, tmp_maxX, tmp_minY, tmp_maxY) = ingeom.GetEnvelope()
                
                if np.logical_and(tmp_minX <= coord[0] <= tmp_maxX,
                                  tmp_minY <= coord[1] <= tmp_maxY):
                    point = ogr.Geometry(ogr.wkbPoint)
                    point.AddPoint(coord[0], coord[1])
                                  
                    ingeomTypeName = ingeom.GetGeometryName()
                    # print('\t{}'.format(feature.GetFID()), ingeomTypeName)
                    # print('\t{}'.format(feature.GetFID()), feature.keys())
                    # print('\t{}'.format(feature.GetFID()), feature.items())
                    # print('\t{}'.format(feature.GetFID()), feature.geometry())
                    
                    ipoly = 0
                    data = {
                        'x': [],
                        'y': [],
                        'c': [],
                        'd': []
                    }
                    if ingeomTypeName == 'MULTIPOLYGON':
                        for polygon in ingeom:
                            is_contain = polygon.Contains(point)                                    

                            fig, ax = plt.subplots(1)
                            if is_contain:
                                title = 'Mascon id={} xy={}, Poly id={} FID={}'.format(icoord, coord, ipoly, feature.GetFID())
                                print(title)

                                plt.title(title)
                                for ring in polygon:
                                    # print('\t', ipoly, ingeomTypeName, polygon.GetGeometryName(), ring.GetGeometryName())
                                    # if int(feature.GetFID()) > 0:
                                    #     title = 'Mascon id={}, xy={}; Area id={}, FID={}'.format(icoord, coord, ipoly, feature.GetFID())
                                    #     print(title)
                                    data['x'] = [ring.GetPoint(ipt)[0] for ipt in range(0, ring.GetPointCount())]
                                    data['y'] = [ring.GetPoint(ipt)[1] for ipt in range(0, ring.GetPointCount())]
                                    data['c'] = [ipt for ipt in range(0, ring.GetPointCount())]
                                    data['d'] = [1 for ipt in range(0, ring.GetPointCount())]
                                    
                                    plt.scatter(coord[0], coord[1], marker='o')
                                    plt.scatter('x', 'y', c='c', s='d', marker='.', data=data)
                                plt.axis("auto")
                                # plt.show()
                                plt.savefig('{}.jpg'.format(os.path.join(pathOut, 'fig', title)))
                                plt.cla()
                                
                                in_poly.append(icoord)
                                
                            plt.close(fig)
                            ipoly += 1
                    elif ingeomTypeName == 'POLYGON':
                        is_contain = ingeom.Contains(point)
                        
                        fig, ax = plt.subplots(1)
                        if is_contain:
                            title = 'Mascon id={} xy={}, Poly id={} FID={}'.format(icoord, coord, ipoly, feature.GetFID())
                            print(title)
                                
                            plt.title(title)
                            for ring in ingeom:
                                # print('\t', ipoly, ingeomTypeName, ring.GetGeometryName())
                                data['x'] = [ring.GetPoint(ipt)[0] for ipt in range(0, ring.GetPointCount())]
                                data['y'] = [ring.GetPoint(ipt)[1] for ipt in range(0, ring.GetPointCount())]
                                data['c'] = [ipt for ipt in range(0, ring.GetPointCount())]
                                data['d'] = [1 for ipt in range(0, ring.GetPointCount())]

                                plt.scatter(coord[0], coord[1], marker='o')
                                plt.scatter('x', 'y', c='c', s='d', marker='.', data=data)
                            plt.axis("auto")
                            # plt.show()
                            plt.savefig('{}.jpg'.format(os.path.join(pathOut, 'fig', title)))
                            plt.cla()
                            
                            in_poly.append(icoord)
                            
                        plt.close(fig)
                        ipoly += 1
                    else:
                        # print('\t', ipoly, ingeomTypeName)
                        # ipoly += 1
                        pass
            
            # reset the read position to the start
            inputlyr.ResetReading()
                
        icoord += 1

    fig, ax = plt.subplots(1)
    title = 'Mascon_points_bbox'
    plt.title(title)

    for feature in inputlyr:
        ingeom = feature.GetGeometryRef()
        data = {
            'x': [],
            'y': [],
            'c': [],
            'd': []
        }
        if ingeomTypeName == 'MULTIPOLYGON':
            for polygon in ingeom:
                for ring in polygon:
                    data['x'] = [ring.GetPoint(ipt)[0] for ipt in range(0, ring.GetPointCount())]
                    data['y'] = [ring.GetPoint(ipt)[1] for ipt in range(0, ring.GetPointCount())]
                    data['c'] = [ipt for ipt in range(0, ring.GetPointCount())]
                    data['d'] = [1 for ipt in range(0, ring.GetPointCount())]
                    plt.scatter('x', 'y', c='c', s='d', marker='.', data=data)
    inputlyr.ResetReading()

    plt.scatter('x', 'y', marker='o', data=in_bbox)
    # plt.axis("auto")
    plt.xlim(minX, maxX)
    plt.ylim(minY, maxY)
    # plt.show()
    plt.savefig('{}.jpg'.format(os.path.join(pathOut, 'fig', title)))
    plt.cla()
    plt.close(fig)

    return np.unique(np.array(in_poly))

### from bert
def convert_partial_year(number):
    year = int(number)
    
    d = datetime.timedelta(days=(number - year)*(365 + calendar.isleap(year)))
    day_one = datetime.date(year, 1, 1)
    
    date = d + day_one
    return date
