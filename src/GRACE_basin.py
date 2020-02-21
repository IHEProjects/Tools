# -*- coding: utf-8 -*-
"""
Created on Wed Jan 10 16:51:44 2018

Need to download global GRACE GFSC product from
https://ssed.gsfc.nasa.gov/grace/products.html
GSFC.glb.200301_201607_v02.3b-ICE6G - ASCII

@author: cmi001 

gdalsrsinfo.exe "EPSG:4326"

cd "D:\IHEProjects\20200218-Philippines\Code"
python GRACE_basin.py
"""
import os
root = os.path.dirname(os.path.abspath(__file__))
os.chdir(root)


import csv
from osgeo import ogr
import shapefile
import pandas as pd
import numpy as  np
import grace_functions as gf
from matplotlib import pyplot as plt


def plot_shp(shp):
    sf = shapefile.Reader(shp)
    plt.figure()
    for shape in sf.shapeRecords():
        x = [i[0] for i in shape.shape.points[:]]
        y = [i[1] for i in shape.shape.points[:]]
        plt.plot(x,y)
    plt.show()

case_name = 'Mindanao'
pathIn  = os.path.join(root, '..', 'Data')
pathOut = os.path.join(root, '..', 'Data', 'Output')
BUFFER_DIST = .71
# BUFFER_DIST = 0.0

BASIN_SHP  = os.path.join(pathIn, 'Shapefile', "{cn}.shp".format(cn=case_name))
OUT_CSV = os.path.join(pathOut , "{cn}.csv".format(cn=case_name))

BUFFER_SHP = os.path.join(pathOut, "{cn}_buffer.shp".format(cn=case_name))
MASCON_SHP = os.path.join(pathOut, "{cn}_mascons.shp".format(cn=case_name))
print('BASIN_SHP    : "{}"'.format(BASIN_SHP))
print('OUT_CSV      : "{}"'.format(OUT_CSV))
print('BUFFER_SHP   : "{}"'.format(BUFFER_SHP))
print('MASCON_SHP   : "{}"'.format(MASCON_SHP))

MASCON_DATA_FOLDER = os.path.join(pathIn, 'GRACE', 'Mascons', "GSFC.glb.200301_201607_v02.4-ICE6G")
MASCON_INFOR = os.path.join(MASCON_DATA_FOLDER, 'mascon.txt')
MASCON_SOLUT = os.path.join(MASCON_DATA_FOLDER, 'solution.txt')
MASCON_DATES = os.path.join(MASCON_DATA_FOLDER, 'time.txt')
print('MASCON_INFOR : "{}"'.format(MASCON_INFOR))
print('MASCON_SOLUT : "{}"'.format(MASCON_SOLUT))
print('MASCON_DATES : "{}"'.format(MASCON_DATES))

print('GRACE, create_buffer')
# gf.create_buffer(BASIN_SHP, BUFFER_SHP, BUFFER_DIST)

print('read_csv, MASCON_INFOR')
df_info = pd.read_csv(MASCON_INFOR, sep=r"\s+", header=None, skiprows=14,engine='python')
mascon_coords = zip(df_info[1], df_info[0])

print('read_csv, MASCON_DATES')
df_dates = pd.read_csv(MASCON_DATES, sep=r"\s+", header=None, skiprows=13,engine='python')
fract_dates = df_dates[2]
mascon_dates = [str(gf.convert_partial_year(fdate)) for fdate in fract_dates]

print('GRACE, points_in_polygon')
# Return null geometry sometimes?
# Shell is not a LinearRing
index_mascons_of_interest = gf.points_in_polygon(BUFFER_SHP, mascon_coords, pathOut)
print(index_mascons_of_interest)

print('open, MASCON_SOLUT')
data_lines = []
with open(MASCON_SOLUT) as fp:
    for i, line in enumerate(fp):
        # >>> print(i, line[0:10])
        # 41173 13.08760 2
        # 41174 12.42396 2
        if i in np.array(index_mascons_of_interest) + 7:
            data_lines.append(np.array(line.rstrip('\n').rstrip().split(' ')).astype(float))

print('create, MASCON_SHP of mascon areas')
# Adapeted from bec's SortGRACE.py
w = shapefile.Writer(MASCON_SHP, shapeType=shapefile.POLYGON)
w.field('MASCON_ID', 'C', '40')

for mascon_index in index_mascons_of_interest:
    ID = mascon_index+1
    lon_center = df_info[1][mascon_index]
    lat_center = df_info[0][mascon_index]
    lon_span = df_info[3][mascon_index]
    lat_span = df_info[2][mascon_index]
    w.poly([
            [[lon_center + .5 * lon_span, lat_center + .5 * lat_span],
             [lon_center - .5 * lon_span, lat_center + .5 * lat_span],
             [lon_center - .5 * lon_span, lat_center - .5 * lat_span],
             [lon_center + .5 * lon_span, lat_center - .5 * lat_span],
             [lon_center + .5 * lon_span, lat_center + .5 * lat_span]]
            ])
    w.record(ID,'Polygon')
w.close()

print('Get weights from relative intersection area')
basin_poly  = ogr.Open(BASIN_SHP)
mascon_poly = ogr.Open(MASCON_SHP)

basin_lyr  = basin_poly.GetLayer()
mascon_lyr = mascon_poly.GetLayer()

print('loop BASIN_SHP basin_lyr, MASCON_SHP mascon_lyr')
i_b_feature = 0
for b_feature in basin_lyr:
    i_b_feature += 1
    b_geom = b_feature.GetGeometryRef()
    print('basin', i_b_feature, '/', basin_lyr.GetFeatureCount(), b_geom.GetGeometryName(), b_geom.Centroid().ExportToWkt())
    
    ids = []
    int_area = []
    total_area = 0

    i_m_feature = 0
    for m_feature in mascon_lyr:
        i_m_feature += 1
        
        m_geom = m_feature.GetGeometryRef()
        test = b_geom.Intersection(m_geom)
        
        ids.append(m_feature.GetField(0))
        int_area.append(test.GetArea())
        total_area += test.GetArea()
        
        if i_m_feature % 100 == 0:
            print('\t', 'mascon', i_m_feature, '/', mascon_lyr.GetFeatureCount(), m_geom.GetGeometryName(), m_geom.Centroid().ExportToWkt())
            print('\t', '\ttotal_area: ', total_area)
        
    mascon_lyr.ResetReading()  # reset the read position to the start
    print('\ttotal_area: ', total_area)
        
print('calculate weights')
# TODO-END, 20200221, QPan, is it correct? Yes
weights = np.array(int_area)/total_area

print('calculate weighted mascon')
weighted_line = [data_lines[i] * weights[i] for i in range(len(data_lines))]
# print('weighted_line: ', weighted_line)
weighted_average = np.sum(weighted_line, 0)
print('weighted_average max: ', np.max(weighted_average), 'min: ', np.min(weighted_average))

print('write OUT_CSV')
with open(OUT_CSV, 'w',newline='') as csvfile:
    spamwriter = csv.writer(csvfile, delimiter=',')
    
    spamwriter.writerow(['date', 'Equivalent Water Height [mm]'])
    
    for date, value in zip(mascon_dates, weighted_average):
        spamwriter.writerow([date, value*10])

