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

#Read any point file with lat and long
#REPLACE WITH YOUR DATA. "stn", because this was originally done on hydrological monitoring stations
stn = pd.read_csv("Coding/Python/Hydrology/stations10yearsplus_nonreg.csv")
stn.columns


#Load freshwater atlas geodatabase (DOWNLOAD FROM DATABC)
gdb_file = "Hydrology/BC Freshwater atlas/FWA_WATERSHEDS_POLY/FWA_WATERSHEDS_POLY.gdb"

#Load freshwater atlas with fine scale polygons - 245 layers, one for each large river system/area
   
#Approach to list each layer, then read layer by layer using loop
listlayers = fiona.listlayers(gdb_file)

#Remove last three rows of layers (which are irrelevant tables)
n=4
del listlayers[-n:]
len(listlayers)

#Now read each layer (large drainge) as a df stored inside a list. Then append dfs into a single df
#layers = listlayers[0:5] #a subset of first 
layers = listlayers #the full dataset
for l in range(0, len(layers)):
    layers[l] = gpd.read_file(gdb_file, layer=l)
    #Each layer is the fwa for a large basin, now stored inside list

#combine each basin layer using append into single df # This takes some hours / overnight!
fwa_core = layers[0] #layer one is core, to which others are appended
for i in range(1, len(layers)): #start at 1 because 0 already included as core
   fwa_core = fwa_core.append(layers[i])
   #fwa_core is a huge df


#------------------------
#Prepare data 

#Prepare stn geometry
#Convert lat long columns into geometry column and into a geodataframe object 
stn_gdf = gpd.GeoDataFrame(stn, geometry = gpd.points_from_xy(stn.x, stn.y))

#Assign a projection (set.crs) to the gdf of NAD83, the system the Hydata were collected in
#MAY NOT BE NECESSARY WITH YOUR POINT DATA
stn_gdf.crs #none? if so, have to assign the correct coordinate system for your data. 
#if it has, make sure it matches the FWA dataset of EPSG:3005, or transform it to match. 
stn_gdf = stn_gdf.set_crs("EPSG:4269") #NAD83
stn_gdf.crs
stn_gdf.plot

#Reproject (to.crs) the geometry to match BC ALbers 
stn_gdf = stn_gdf.to_crs("EPSG:3005") #BC_albers

stn_gdf.plot()

#-----------------------
#Spatial join points to fwa (freshwater atlas) 

#left join option - preserves point geometry, grabs watershed code but not geometry. Fine for making a dictionary
stn_fwa_left = gpd.sjoin(stn_gdf, fwa_core, how="left", op='within')
stn_check_left = stn_fwa_left.head()

stn_fwa_left_clean = stn_fwa_left[stn_fwa_left['LOCAL_WATERSHED_CODE'].notna()]

#Right join - preserves watershed geometry and station number at locations where stn intersected fwa
stn_fwa_right = gpd.sjoin(stn_gdf, fwa_core, how="right", op='within')
stn_fwa_right_clean = stn_fwa_right[stn_fwa_right['STATION_NUMBER'].notna()]
stn_check_right = stn_fwa_right.head()
 
#left join option based on buffered point. This is needed to ensure we don't miss the river and only take side catchments
stn_gdf_buffer = stn_gdf.copy()
stn_gdf_buffer = stn_gdf_buffer.geometry.buffer(40)
stn_fwa_buffer_left = gpd.sjoin(stn_gdf, fwa_core, how="left", op='intersects')
stn_fwa_buffer_left_check = stn_fwa_buffer_left.head()

#Choose which join to use
#Use either for making a data dictionary. 
#Maybe use right to populate with others 
#use left with station number and local watershed code 
stn_fwa = stn_fwa_left_clean #only this works to extract using str.contains
#stn_fwa = stn_fwa_right_clean

#Use right for making a data dictionary

#-------------------
#Split watershed code down to base - we will select any polgons with this base as upstream
stn_fwa[['fwaBase', 'B']] = stn_fwa['LOCAL_WATERSHED_CODE'].str.split('-00', 1, expand=True)


#Use left, select nucleus columns into df
stn_fwa_select = stn_fwa[["STATION_NUMBER", "fwaBase"]]


#---------------
#Convert nucleaus columns into list...? or dictionary
#stn_list = stn_fwa_select.values.tolist() #both watershed code and station #
stn_list = stn_fwa_select.fwaBase.tolist() #only watershed code

# into dictionary - maybe not needed
stn_dict = dict(zip(stn_fwa_select.STATION_NUMBER, stn_fwa_select.fwaBase))

#stn_df = pd.DataFrame({'station':stn_list})

#------------------
#Read 
#First read each station name into df's within a list. Then append dfs into a single df
#read all layers at once (or a subset)
stn_list #only watershed codes **some local watershed codes are dupllicated: 2 stations within local watershed@! Maybe name changed over time? 
stn_list[1]
stn_list_codes = stn_list.copy()
placeholder = stn_list_codes.copy()

#run list of single codes into list of dataframes - one for each station
for i in range(0, len(stn_list_codes)):
    stn_list_codes[i] = fwa_core.loc[fwa_core['LOCAL_WATERSHED_CODE'].str.contains(stn_list[i])]
    
#first assign a dissolve field to each station in list
for i in range(0, len(stn_list_codes)):
    stn_list_codes[i]['dissolvefield'] = i #assign a dissolve by field
    
#Append list into single df
basin_core = stn_list_codes[0] #Start with 0 as core
for i in range(1, len(stn_list_codes)): #append 1 onwards
   basin_core = basin_core.append(stn_list_codes[i])
   
#-------------
#Dissolve each item in list
basins_dissolved = basin_core.dissolve(by = 'dissolvefield')


#This is not producing the unique files desired. 
basins_unique = basins_dissolved.drop_duplicates()

#basins_unique.head().plot()
#basins_unique.tail().plot()

#This is not producing the unique files desired. 

basins_dissolved.plot()


#----------------------------
#Merge station number back in with geometry

#Right join - preserves watershed geometry and station number at locations where stn intersected fwa
stn_final_geom = gpd.sjoin(stn_gdf, basins_unique, how="right", op='within')
#stations become replicated but were not before, possibly because the basins dissolved polygons are replicated? 


#-----------------------------
#Select final rows and write to csv.  

basin_data = stn_final_geom[["STATION_NUMBER", "AREA_HA", "geometry"]]
basin_data.loc[:,"AREA_KM"] = basin_data.area /1000000

#take the minimum area for each station, because many stations also joined with larger drainages
#sort by area, then drop duplicates of station only taking the first (should be the smallest)
#I output the data keeping first. Now In Dec 2022, I revist this idea. Maybe I should take the bigger one. Otherwise, we capture many tiny polygons. 
basin_lowest = basin_data.sort_values('AREA_KM', ascending=True).drop_duplicates('STATION_NUMBER', keep= 'first').sort_index()
basin_highest = basin_data.sort_values('AREA_KM', ascending=True).drop_duplicates('STATION_NUMBER', keep= 'last').sort_index()
basin_lowest.head(30)
#https://stackoverflow.com/questions/12497402/python-pandas-remove-duplicates-by-columns-a-keeping-the-row-with-the-highest

#** THere are still some duplicates of area. I beleive this is because the stations almost overlap eachother
#maybe when one was discontinued and then another set up. 

#Inspect 
basin_lowest.plot()
basin_highest.plot()

#First delete dissolve field 577, which resulted in a chaotic polygon. somehow messed up. 
basin_clean = basin_lowest[basin_lowest['dissolvefield'] != 577]
#basin_clean = basin_highest[basin_lowest['dissolvefield'] != 577]
basin_clean.plot()

basin_clean.to_file("Coding/Python/Hydrology/Catchment fwa from all stations.shp")


#Explore distribution of different watershed sizes
#I observed in GIS that:
#-few stations if <25km2 in Prince Rupert Interior
#few stations if <60km in Prince George. 
#Prince George has quite a few around 300

#How about 20-200 and 200-10000? 
#-10 simply as a minimum size so not too many tiny catchments get in. 
#-200 meets cut off proposed in the BC Hydrology textbook saying that forest management is typically concerned with catchments of 100-200km
#-10000 because it excludes only a few very large catchments which have smaller monitored watersheds nested within them

basin_clean_10to200 = basin_clean[(basin_clean['AREA_KM'] >= 10) & (basin_clean['AREA_KM'] <= 200)]
basin_clean_10to200.plot() #That looks pretty good for local scale

basin_clean_200to10000 = basin_clean[(basin_clean['AREA_KM'] >= 200.01) & (basin_clean['AREA_KM'] <= 10000)]
basin_clean_200to10000.plot() #That looks pretty good




#Some others for reference
basin_clean_200to2000 = basin_clean[(basin_clean['AREA_KM'] >= 200) & (basin_clean['AREA_KM'] <= 2000)]
basin_clean_200to2000.plot() #That looks pretty good

basin_clean_over300.plot() #sparse in Prince George

basin_clean_over300 = basin_clean[basin_clean['AREA_KM'] >= 300]
basin_clean_over300.plot() #sparse in Prince George

basin_clean_over1000under10000 = basin_clean[(basin_clean['AREA_KM'] >= 1000) & (basin_clean['AREA_KM'] <= 10000)]
basin_clean_over1000under10000.plot() #nothin in Prince George over 1000

basin_clean_over300under2000 = basin_clean[(basin_clean['AREA_KM'] >= 300) & (basin_clean['AREA_KM'] <= 2000)]
basin_clean_over300under2000.plot()

basin_clean_under300 = basin_clean[(basin_clean['AREA_KM'] >= 2) & (basin_clean['AREA_KM'] <= 300)]
basin_clean_under300.plot()

#Alternative way - use groupby, grab min, then re-merge with geometry. 
#Set a unique ID, which I will use to remerge the geometry.  
#basin_data = basin_data.reset_index()
#basin_data['uniqueID'] = basin_data.index
#basin_data.head()

#Grab the min of each station number - note: this will drop geometry so we will re-merge it later
#basin_lowest = basin_data.groupby(['STATION_NUMBER'], as_index=False).min('AREA_KM') #we lose geometry

#Merge geometry back in
#basin_lowest_geo = basin_lowest.merge(basin_data, how = 'left', on = 'uniqueID')
#test = basin_lowest_geo.head()

#basin_single.plot()
#basin_data.crs
#basin_data.to_file("Coding/Python/Hydrology/Catchment fwa from all stations.shp")
#basin_single.to_file("Coding/Python/Hydrology/Catchment fwa from all stations.shp")
#basin_lowest_geo.plot()
#basin_lowest_geo.to_file("Coding/Python/Hydrology/Catchment fwa from all stations.shp")




#Load from memory 
#basin_lowest = gpd.read_file("Coding/Python/Hydrology/Catchment fwa from all stations.shp")

#THere are still some duplicates of station name, but not km....
#We need to remove duplicated of station name .,
#basin_lowest.groupby('STATION_NU', as_index=False).min('AREA_KM')

#Identify final stations to use 
#basin_lowest.columns

#remove super large station by name 
#basin_clean = basin_lowest[basin_lowest['STATION_NU'].str.contains('08GA061')]

#remove super large station by size (better, because there are two of these stations. )
basin_clean = basin_lowest[basin_lowest['STATION_NU'].str.contains('08GA061')]