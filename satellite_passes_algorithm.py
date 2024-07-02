# -*- coding: utf-8 -*-

"""
/***************************************************************************
 Satellite_passes
                                 A QGIS plugin
 Return next 10 day satellite passes. 
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-06-11
        copyright            : (C) 2024 by Ching Yin Kwok
        email                : ching.yin-kwok@ifgt.tu-freiberg.de
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

__author__ = 'Ching Yin Kwok'
__date__ = '2024-06-11'
__copyright__ = '(C) 2024 by Ching Yin Kwok'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


# check libraries: pyogrio, bs4
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFolderDestination)
import geopandas as gpd
import pandas
import numpy as np
import csv
import urllib.request
from bs4 import BeautifulSoup
import os
from shapely.geometry import Polygon


class Satellite_passesAlgorithm(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    OUTPUT = 'OUTPUT'
    INPUT = 'INPUT'
    INPUT2 = 'SATELLITE'

    def initAlgorithm(self, config):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. 
        
        satellite_list = ['Aqua', 'Aura', 'CALIPSO', 'CBERS-4', 'CloudSAT', 'GPM', 
                   'Jason-3', 'Landsat-7', 'Landsat-8', 'NOAA-20', 'NOAA-18', 
                   'NOAA-19', 'Proba-V', 'Sentinel-1A', 'Sentinel-1B', 
                   'Sentinel-2A', 'Sentinel-2B', 'Sentinel-3A', 'Sentinel-3B', 
                   'Suomi NPP','Terra']
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPolygon]
            )
        )
     
        # we add a field for satellite input
                
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT2,
                self.tr('Satellite'),
                options = satellite_list
            )
        )


        # We add a output folder
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                self.tr('Output Folder')
            )
        )
        
# =============================================================================
#         # We add a feature sink in which to store our processed features (this
#         # usually takes the form of a newly created vector layer when the
#         # algorithm is run in QGIS).
#         self.addParameter(
#             QgsProcessingParameterFeatureSink(
#                 self.OUTPUT,
#                 self.tr('Output layers')
#             )
# =============================================================================
        

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.

        satellite_list = ['Aqua', 'Aura', 'CALIPSO', 'CBERS-4', 'CloudSAT', 'GPM', 
                   'Jason-3', 'Landsat-7', 'Landsat-8', 'NOAA-20', 'NOAA-18', 
                   'NOAA-19', 'Proba-V', 'Sentinel-1A', 'Sentinel-1B', 
                   'Sentinel-2A', 'Sentinel-2B', 'Sentinel-3A', 'Sentinel-3B', 
                   'Suomi NPP','Terra']

        
        source = self.parameterAsSource(parameters, self.INPUT, context)
        layer = self.parameterAsVectorLayer(parameters, self.INPUT,context)
        satellite_enum = self.parameterAsEnum(parameters, self.INPUT2,context)
        directory = self.parameterAsFileOutput (parameters, self.OUTPUT, context)
        
        satellite_name = satellite_list[satellite_enum]
        
        # get vertices
        feat = layer.getFeatures()
        vertices_list = []
        for feature in feat:
            geometry = feature.geometry()
            vertices = geometry.vertices()
        for vertix in vertices:
            xytuple = [vertix.x(), vertix.y()]
            vertices_list.append(xytuple)
        
        vertices_list = vertices_list[:-1]

        # Read our saved satellite csv file 
        metadataurl = 'http://raw.githubusercontent.com/glorkcy/satellite_pass/main/sat_metadata.csv'
        a = pandas.read_csv(metadataurl)
        a = a.set_index(['Satellite'])
        satellite_id = a['Satellite ID'][satellite_name]   
        
        # create a folder of the satelite
        newpath =  directory +'/' + satellite_name
        if not os.path.exists(newpath):
            os.makedirs(newpath)
        os.chdir(newpath)

        # Prepare two new csv files for result
       # f= open ('precise_info.csv', 'w', newline='', encoding="utf-8") 
        f2 = open ('schedule.csv', 'w', newline='', encoding="utf-8")
     #   f_writer = csv.writer (f)
     #   f_writer.writerow(['satellite','sensor', 'maximum_angle', 'lat', 'lng', 'date','time', 'altitude', 'azimuth', 'daynight']) 
        f2_writer = csv.writer (f2)
        f2_writer.writerow(['satellite','sensor', 'date','time','coverage']) 

        #%% To store info we got from heavensabove.com into dictionaries for later manipulation

        # for each instrument in satellite
        for i in range(1,5):
            if pandas.isnull(a['Instrument ' + str(i)][satellite_name]) == False: # to ignore 'nan' cell
                instrument_name = a['Instrument ' + str(i)][satellite_name]
                print ('We are getting information for ' + satellite_name + ' ' + instrument_name)
                
                # Make three blank dictionaries and one blank list
                satellite_details =[]  # for saving information from heavensabove.com
                pass_satellite_dict = {} # for storing vertex order (value) with passing date as (key)
                altitude_dict ={}   # for storing altitude (value) with passing date and vertex order as (key) 
                time_dict ={}  # for storing satellite passing time (value) with passing date as (key)

                # get the boundary angle of satellite instrument
                maximum_angle = a['Converted Angle ' + str(i)] [satellite_name]
                
                # test each vertex
                for vertex in vertices_list:
                    lng = vertex[0]    
                    lat = vertex[1]
                    vertex_order = vertices_list.index([lng,lat]) # get the order of the particular index
                    overfly_count = 1
                    # scrap 
                    req=urllib.request.urlopen('https://www.heavens-above.com/PassSummary.aspx?satid='+ str(satellite_id) + '&lat=' + str(lat) + '&lng='+ str (lng) +'&loc=Unspecified&alt=0&tz=UCT&showall=t')
                    # example url: https://www.heavens-above.com/PassSummary.aspx?satid=40697&lat=53.07196562835662&lng=13.8689581095596&loc=Unspecified&alt=0&tz=UCT&showall=t
                    article = req.read().decode('utf-8')
                    soup = BeautifulSoup(article, 'html.parser')
                    table = soup.find("table",{"class": "standardTable"})
                    tabletext=table.getText()
                    trs = table.find_all ("tr",{"class": "clickableRow"})
                    for tr in trs:
                        tds = tr.find_all ("td")
                        satellite_info=[]
                        for td in tds:
                            satellite_info.append(td.getText())

                        passdate = satellite_info[0]
                        passtime = satellite_info[5]
                        altitude = satellite_info[6][:-1]
                        azimuth = satellite_info[7]

                        # if satellite altitude in heavensabove.com is greater than the boundary angle of the swath, then vertex is inside swath
                        if satellite_info[11] =='daylight':
                            if float (altitude) >float(maximum_angle):
                                if passdate + ' ' + passtime[:2] not in pass_satellite_dict:  # surrounding time
                                    if passdate + ' ' + str(int(passtime[:2])+1) in pass_satellite_dict: 
                                        passtime = str(int(passtime[:2])+1)
    
                                    elif passdate + ' ' + str(int(passtime[:2])-1) in pass_satellite_dict:
                                        passtime = str(int(passtime[:2])-1)
                                        
                                    else:     # if it is a new pass time
                                        overfly_count = overfly_count + 1   # have a new series of overfly
                                        pass_satellite_dict[passdate + ' ' + passtime[:2]] = []  # construct a new date as key                
    #                                    boundarybox['overfly_date_'+ str(overfly_count)]= passdate +' '+ passtime   #  add date to the attribute table of shp file (only record the first vertex that gives a new date) 
                                
    #                            f_writer.writerow([satellite_name,instrument_name, maximum_angle, lat, lng, passdate,passtime, altitude, azimuth, daynight])                        
                                # fill out all the three dictionaries
                                pass_satellite_dict.setdefault(passdate+ ' ' + passtime[:2], []).append(vertex_order)     
                                altitude_dict[passdate+ ' ' + passtime[:2] + '_' + str(vertex_order)] = float(altitude)                
                                time_dict[passdate+ ' ' + passtime[:2]] = passtime
              
                            # include also the marginal satellite altitudes which are just slightly out of swath, so that we can measure the proportion and update the vertex later
                            elif float (altitude) <= float(maximum_angle) and float (altitude) > float(float(maximum_angle)*0.8):
                                if passdate + ' ' + passtime[:2] not in pass_satellite_dict:  # surrounding time #%%
                                    if passdate + ' ' + str(int(passtime[:2])+1) in pass_satellite_dict:  #%%
                                        passtime = str(int(passtime[:2])+1)
                                    elif passdate + ' ' + str(int(passtime[:2])-1) in pass_satellite_dict:
                                        passtime = str(int(passtime[:2])-1)
                                    else:
                                        passtime = passtime             
                                altitude_dict[passdate + ' ' + passtime[:2] + '_' + str(vertex_order)] = float(altitude)
    
                            else:
                                continue
                        
        #%% Check which points are inside satellite dependent threshold              
                
                # 1: no passes
                if pass_satellite_dict == {}:
                    f2_writer.writerow([satellite_name,instrument_name, '-','-','No pass within next 10 days']) 
        #            print('No overfly of satellite '+ satellite_name +' within next 10 days')    
                    #!! return shp file as None      
                    
                else:
                    for k,v in pass_satellite_dict.items():
                 #       pass_datestr = k[:-2] + str(
                 #           datetime.datetime.utcnow().year) + time_dict[k]
                 #       pass_datetime = datetime.datetime.strptime(pass_datestr, '%d %b %Y%H:%M:%S')
                 #       pass_date = pass_datetime.strftime("%Y-%m-%d %H:%M")
                        
                        v = list(dict.fromkeys(v))
                        # 2: all passes: create a new ROI Shape with same extention as original 
                        if len(v) == len(vertices_list): 
                            f2_writer.writerow([satellite_name,instrument_name, k[:-2],time_dict[k],'Whole']) 
        #                    print('The whole area is covered under '+ satellite_name + ' ' + instrument_name + ' on ' + k[:-2] + '' + time_dict[k]) 
                            #!! return shp file as the same shp file
                        
                        # 3: partial overfly: create new geometry
                        else:       
                            # get the missing vertices that just out of the swath
                            missing_vertices_order =[]
                            missing_vertices = []
                            for i in range (v[0],len(vertices_list)):
                                if i not in v:
                                    missing_vertices_order.append(i)
                                    missing_vertices.append(vertices_list[i])              
                            for i in range (0,v[0]):
                                if i not in v:
                                    missing_vertices_order.append(i)  
                                    missing_vertices.append(vertices_list[i])  
                                    
                            mp1 = missing_vertices_order[0]
                            mp2 = missing_vertices_order[-1]                   

        #%% For the third case, we need two formulaes to update out-of-swath vertices to new boundary vertices
        #   If number of outlying vertices is more than 1, which is a more common case, get_new_coordinate1() would be used
        #   If number of outlying vertices is just 1, get_new_coordinate2() would be used
                            
                            def get_new_coordinate1 (miss_pos): # out-of-swath vertices >1                                             
                                # get vertex order and altitude of the just out-of-swath vertex
                                miss_vertex = vt[miss_pos] 
                                miss_altitude = altitude_dict[k + '_' + str(miss_pos)]                                
                                
                                # check if vertex order is 0 or max to prevent 'list out of range'
                                check_pos = miss_pos - 1  
                                if check_pos == -1: 
                                    check_pos = len(vt)-1  
                                check_pos2 = miss_pos + 1
                                if check_pos2 == len(vt):
                                    check_pos2 = 0
                                
                                # for direction purpose, so to make sure nearby vertex for comparison is the one in swath, not not the one that out of swath 
                                if altitude_dict[k + '_' + str(check_pos)] > float (maximum_angle):  # make sure minus the correct order
                                    nearby_vertex = vt[check_pos]
                                    nearby_altitude = altitude_dict[k + '_' + str(check_pos)]
                                else:
                                    nearby_vertex = vt[check_pos2]
                                    nearby_altitude = altitude_dict[k + '_' + str(check_pos2)]    
                                    
                                # update the new vertex by 'altitude proportion formulae'
                                new_vertex =['','']
                                proportion = (float(maximum_angle) - miss_altitude)/ (nearby_altitude - miss_altitude)                     
                                for i in range (2):
                                    new_vertex[i] = miss_vertex[i] + (nearby_vertex[i]-miss_vertex[i])*proportion
                                return new_vertex 
                            
                            def get_new_coordinate2(miss_pos):   # only one out-of-swath vertex  
                                # get vertex order and altitude of the just out-of-swath vertex
                                miss_vertex = vt[miss_pos] 
                                miss_altitude = altitude_dict[k + '_' + str(miss_pos)]                                      
                                
                                ## first vertex
                                # for direction purpose, so to make sure nearby vertex for comparison is the one in swath, not not the one that out of swath 
                                nearby_vertex1 = vt[miss_pos - 1 ] 
                                nearby_altitude1 = altitude_dict[k + '_' + str(miss_pos - 1)]                         
                                        
                                # get the new vertex by 'altitude proportion formulae' 
                                new_vertex1 =['','']
                                proportion = (float(maximum_angle) - miss_altitude)/ (nearby_altitude1 - miss_altitude)
                                for i in range (2):
                                    new_vertex1[i] = miss_vertex[i] + (nearby_vertex1[i]-miss_vertex[i])*proportion
                                
                                ## second vertex
                                # for direction purpose, so to make sure nearby vertex for comparison is the one in swath, not not the one that out of swath 
                                if miss_pos == len(vt)-1:  # if order of outlying index is the last, make nearby index as 0
                                    nearby_vertex2 = vt[0]
                                    nearby_altitude2 = altitude_dict[k + '_0']  
                                else:
                                    nearby_vertex2 = vt[miss_pos + 1 ]
                                    nearby_altitude2 = altitude_dict[k + '_' + str(miss_pos + 1)]    
                                
                                # get the new vertex by 'altitude proportion formulae' 
                                new_vertex2 =['','']     
                                proportion = (float(maximum_angle) - miss_altitude)/ (nearby_altitude2 - miss_altitude)
                                for i in range (2):
                                    new_vertex2[i] = miss_vertex[i] + (nearby_vertex2[i]-miss_vertex[i])*proportion 
                                return new_vertex2, new_vertex1
                            
        #%% We put the out-of-swath vertices into the above formulae, and then turn the updated vertice list into numpy array
                                
                            vt = vertices_list.copy()
                            if mp1 == mp2: # if number of outlying vertices is equal to 1
                                get = get_new_coordinate2 (mp1) # new vertices
                                vt[mp1] = get[0]  
                                
                                check_pt =mp1+1
                                if len(vt) == check_pt:
                                    check_pt = 0
                                if vt[mp1][0] > vt[check_pt][0] and vt[check_pt][0] > get[1][0] is True:
                                    vt.insert(check_pt, get[1]) # insert one more item
                                elif  vt[mp1][0] < vt[check_pt][0] and vt[check_pt][0] < get[1][0] is True:
                                    vt.insert(check_pt, get[1]) 
                                else:
                                    vt.insert(mp1, get[1])

                                # make sure the last item is equal to the first item
                                first_vertex = vt[0]
                                vt.append(first_vertex)  
                                           
                            else:  # if number of outlying vertices is more than 1                            
                                get1 = get_new_coordinate1 (mp1) # new vertix 1
                                get2 = get_new_coordinate1 (mp2) # new vertix 2
                                vt[mp1] =get1
                                vt[mp2] =get2
                                # to remove the remaining out of swath vertices
                                for mv in missing_vertices:
                                    if mv in vt is True:
                                        vt = vt.remove(mv)
                                # make sure the last item is equal to the first item
                                first_vertex = vt[0]
                                vt.append(first_vertex)            
                            
                            vt_array = np.array(vt)
                            f2_writer.writerow([satellite_name,instrument_name, k[:-2], time_dict[k],'Partial']) 
  
                            # generate polygons of partial passes (geopandas method)
                            polygon_geom = Polygon(vt)
                            polygon = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon_geom])       
                            polygon.to_file(filename='./' + instrument_name + ' ' + k[:-2] + time_dict[k].replace(':', '') + '.shp', driver="ESRI Shapefile")

  
        # (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT,
        #         context, source.fields(), source.wkbType(), source.sourceCrs())

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            # Add a feature in the sink
         #   sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT: newpath}

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'Visiting time in the next 10 days'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr(self.name())

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr(self.groupId())

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return ''

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Satellite_passesAlgorithm()
