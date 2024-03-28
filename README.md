# link_points_to_BC_FWA_watersheds
a (currently unverified) python method to identify the upstream basin(s) from BC freshwater atlas for any geographic point location(s). Was designed in Ira Sutherland's PhD work to delineate each upstream area of several hundred hydrological monitoring stations across BC. Those point locations were extraceted from the Hydat database (Tidyhydat package in R), but could be any point location from any file. 

There are two spatial join scripts: 
Spatial join stations to freshwater atlas complete.py - this is with the finest scale hydro data
Spatial join stations to freshwater atlas to get basins.py - this is with large watersheds only. 

***However*** the method does not work as intended. It was realized Nov 2022 that the catchments are not correctly identified because some station point locations are inaccurate and end up falling into tiny little side catchments. For example, imagine a canyon where one basin is represented 

THose cannot be used. 

Solutions could include:
1) redo that analysis after manually editing points to make sure they fall into intended polygons
2) simply manually find the catchments of those points. Eg, selection
3) buffer the station point and include any upstream polygons it intersects. (this is a simple approach that would be the lesser evil of doing nothing). 
