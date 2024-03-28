# -*- coding: utf-8 -*-
"""
Created on Mon Jun 21 11:55:10 2021

@author: irajames
"""


import pandas as pd
import geopandas as gpd
import fiona
import os

#setwd
os.chdir("Z:/Historical BC")


#load data

#Read Hydrology file with lat and long
#I doubt this is in albers lat long. 
stn = pd.read_csv("Coding/Python/Hydrology/stations10yearsplus_nonreg.csv")
stn.columns


#Load freshwater atlas shapefile #very large watersheds 
fwa = gpd.read_file("Hydrology/BC Freshwater atlas/FWA_NAMED_WATERSHEDS_POLY/FWNMDWTRSH_polygon.shp")
fwa.head
fwa.columns
fwa.FWWTRSHDCD

#------------------------
#Prepare data 

#Prepare stn geometry
#Convert lat long columns into geometry column and into a geodataframe object 
stn_gdf = gpd.GeoDataFrame(stn, geometry = gpd.points_from_xy(stn.x, stn.y))

#Assign a projection (set.crs) to the gdf of NAD83, the system the Hydata were collected
#NOT SURE IF THIS IS NECESSARY? Seemed to have been when I brought it into Arc
stn_gdf.crs #none
stn_gdf = stn_gdf.set_crs("EPSG:4269") #NAD83
stn_gdf.crs
stn_gdf.plot

#Reproject (to.crs) the geometry to match BC ALbers 
stn_gdf = stn_gdf.to_crs("EPSG:3005") #BC_albers

#-----------------------
#Spatial join points to fwa 
stn_fwa = gpd.sjoin(stn_gdf, fwa, how="left", op='within')
#2674 polgons overlap the points. This are teh broad watershed polygons. 
#Because the watershed codes overlay eachother, this already grabs all upstream from point (as I understand anyway)
#this has watershed codes and stn num. #it just does not have the watershed geometry. 

#Right join
stn_fwa_right = gpd.sjoin(stn_gdf, fwa, how="right", op='within')

#then filter 
stn_fwa_right.columns
stn_fwa_clean = stn_fwa_right[stn_fwa_right.STATION_NUMBER.notnull()]

#Dissolve polygons by station
stn_dissolved = stn_fwa_clean.dissolve(by = 'STATION_NUMBER')

#Maybe also need to do a dissolve without attribute? 

#Write to file
stn_dissolved.to_file("Station basins coarse.shp")


#I think all delete below - but might be handy later
#Now merge the stn_num back onto the fwa, then filter fwa with stn num !na
fwa_wstnname = pd.merge(fwa, stn_fwa, how = 'left', on = 'FWWTRSHDCD')


#Then we dont need to do this. 
#Split watershed code
#stn_fwa[['fwa_base', 'B']] = stn_fwa['FWWTRSHDCD'].str.split('-00', 1, expand=True)

#But is this grapping a single code per row or multiple *Its grabbing multiple. 
#stn_fwa['fwa_base'][3]

#Grab all FWA polygons that start with the base, and put them in a list in same 
fwa

stn_fwa['fwa_base']

test = fwa['FWWTRSHDCD'].str.contains('000')

#Left off with trying to get the str. function and isin function to work together. 
#https://pandas.pydata.org/docs/reference/api/pandas.Series.str.contains.html
test = fwa[fwa['FWWTRSHDCD'].isin(stn_fwa['FWWTRSHDCD'])]
test = fwa['FWWTRSHDCD'].str.startswith(stn_fwa['fwa_base'][3])
fwa[fwa['FWWTRSHDCD'].str.contains(stn_fwa['fwa_base'])]
stn_fwa['fwa_base']
