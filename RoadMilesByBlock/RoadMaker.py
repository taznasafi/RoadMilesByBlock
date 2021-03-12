import arcpy
import os, sys
import pandas as pd
from RoadMilesByBlock import logger, get_path
import my_paths
from collections import defaultdict
from functools import reduce
import RoadMilesByBlock.__init__ as int_paths

class RoadMaker:

    base_input_folder, base_output_folder = int_paths.input_path, int_paths.output_path
    gdb_output_dic = defaultdict(list)

    def __init__(self, in_gdb_path=None, in_gdb_2_path=None, in_path=None,
                 output_folder=None, generic_out_path=None,
                 out_gdb_name=None, out_gdb=None):
        self.in_gdb_path = in_gdb_path
        self.in_gdb_2_path = in_gdb_2_path
        self.in_path = in_path
        self.output_folder = output_folder
        self.generic_out_path = generic_out_path
        self.out_gdb_name = out_gdb_name
        self.out_gdb = out_gdb

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def create_gdb(self):
        """
        creates ESRI GDB, given that you have provided Class properties correctly.
        """

        if not arcpy.Exists(self.out_gdb):

            arcpy.CreateFileGDB_management(out_folder_path=self.output_folder, out_name=self.out_gdb_name)
            # print(arcpy.GetMessages(0))
        else:
            print("GDB Exists")

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def extract_data_from_shapefiles(self, faces_path=my_paths.faces_zip_path):
        """
        :param faces_path: this the path to the root folder of the faces zipfile.

        Extracts the FID and Block GEOID from the faces shapefile, then save the csv to input folder.

        """

        shp_path_list = get_path.pathFinder.get_shapefile_path_walk_dict(path=faces_path)
        # print(shp_path_list)

        temp_data_frame_list = []
        for shp_path, shp_name in shp_path_list.items():
            # loop over the shapefile, extract the attribute table from faces id and put it pandas dataframe
            arr = arcpy.da.TableToNumPyArray(os.path.join(shp_path, shp_name[0]),
                                             ("TFID", "STATEFP10", "COUNTYFP10", "TRACTCE10", 'BLOCKCE10'))
            df = pd.DataFrame(arr)

            df['geoid10'] = df["STATEFP10"] + df["COUNTYFP10"] + df["TRACTCE10"] + df['BLOCKCE10']

            temp_data_frame_list.append(df)

        # concatenate the list of data1 frames into one master dataframe
        master_df = pd.concat(temp_data_frame_list)
        del temp_data_frame_list
        # export out the csv
        master_df.to_csv(os.path.join(self.base_input_folder, 'faces_by_block.csv'))
        del master_df

        # append the master csv's path to the class attribute for later access
        RoadMaker.gdb_output_dic['faces_by_block_csv'].append(
            os.path.join(self.base_input_folder, 'faces_by_block.csv'))


    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def add_field(self, in_fc, field_name, field_type):
        """

        :param in_fc: input featureclass
        :param field_name: the name of a field
        :param field_type: type of field [string, double, short, long, date]
        """
        # check if the field exits
        fields = len(arcpy.ListFields(dataset=in_fc, wild_card=field_name))
        try:

            if fields < 1:
                # if the length of the field is less than 1 then create a field with specified params
                arcpy.AddField_management(in_table=in_fc, field_name=field_name, field_type=field_type)
                # print(arcpy.GetMessages(0))
        except:
            raise '{} field exits'.format(field_name)

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def calculate_field(self, in_fc, in_field, expression):
        """
        Calculate field based on Python expression
        :param in_fc: input featureclass
        :param in_field: input field
        :param expression: python expression (i.e. !shape.geodesiclength@meters!)
        """
        # print('calculating field, please wait')
        arcpy.CalculateField_management(in_table=in_fc, field=in_field, expression=expression)
        # print(arcpy.GetMessages(0))

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def roads_from_edges(self, cal_fields=False, state=None, gdb_root_path=my_paths.faces_gdb_by_state_base_path):
        """

        :param cal_fields: this is a switch to turn on and off calculating fields.
        :param state: State wildcard passed for parallel processing.
        :param gdb_root_path: please provide path to gdb root folder.

        This process creates roads from edges from state gdb, make sure to provide gdb from census.
        """

        arcpy.Delete_management('temp_fc')

        # get a list of gdb
        gdb_path_list = get_path.pathFinder(env=gdb_root_path).gdb_path_grabber(
            wildcard="*_{}_*.gdb".format(state))

        # loop through gdb path
        for state_path in gdb_path_list:

            # get path from gdb and make sure tp put the feature type as Polyline since we are dealing with roads
            fc_list = get_path.pathFinder(env=state_path).get_path_for_all_feature_from_gdb(type='Polyline')

            # make a copy of the feature with where clause
            arcpy.MakeFeatureLayer_management(in_features=fc_list[0], out_layer="temp_fc",
                                              where_clause=""" MTFCC LIKE 'S%' """)

            # make a field called road_length, shared_block_roads
            if cal_fields:
                RoadMaker.add_field(self, in_fc='temp_fc', field_name='shared_block_roads', field_type='SHORT')
                RoadMaker.add_field(self, in_fc='temp_fc', field_name='road_length', field_type='DOUBLE')

                # calculate geodesic length
                RoadMaker.calculate_field(self, in_fc='temp_fc', in_field='road_length',
                                          expression="!shape.geodesicLength@METERS!")

                # select roads that are shared among blocks and put 1 as shared road mile
                arcpy.SelectLayerByLocation_management(in_layer='temp_fc', overlap_type="SHARE_A_LINE_SEGMENT_WITH",
                                                       select_features=my_paths.tl_2019_blocks,
                                                       selection_type='NEW_SELECTION')

                RoadMaker.calculate_field(self, in_fc='temp_fc', in_field='shared_block_roads',
                                          expression=1)

                arcpy.SelectLayerByAttribute_management(in_layer_or_view='temp_fc', selection_type="SWITCH_SELECTION")

                RoadMaker.calculate_field(self, in_fc='temp_fc', in_field='shared_block_roads',
                                          expression=0)

                arcpy.SelectLayerByAttribute_management('temp_fc', "CLEAR_SELECTION")

            output = os.path.join(self.out_gdb, 'shared_roadMiles_{}'.format(state))

            if not arcpy.Exists(output):
                arcpy.CopyFeatures_management(in_features='temp_fc', out_feature_class=output)
                arcpy.GetMessages(0)
                RoadMaker.gdb_output_dic['tl_2019_roads_from_edges'].append(output)
                arcpy.Delete_management('temp_fc')
            else:
                RoadMaker.gdb_output_dic['tl_2019_roads_from_edges'].append(output)
                arcpy.Delete_management('temp_fc')

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def make_table(self, in_fc, fields, shared):
        column_data = defaultdict(list)
        # print(in_fc)

        for field in fields:

            with arcpy.da.SearchCursor(in_table=in_fc,
                                       field_names=field,
                                       where_clause="""shared_block_roads = %s """ % shared) as cur:
                for row in cur:
                    column_data[field].append(row[0])

        return pd.DataFrame(column_data)

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def create_shared_road_mile(self, state=None):


        # read the attribute table from fc and put it in a data1 frame
        # left join LFID where shared_block_road ==1
        # left join RFID where shared_block_road ==1
        # left join Middle where shared_block_road ==0
        try:
            fc = get_path.pathFinder.filter_List_of_featureclass_paths_with_wildcard(
                path_link_list=RoadMaker.gdb_output_dic['tl_2019_roads_from_edges'],
                wildcard="*_{}".format(state))[0]
        except IndexError as error:
            print(error)
            print("Did not find State {}".format(state))

        else:


            L_fields = ['TFIDL', 'MTFCC', "shared_block_roads", 'road_length']
            R_fields = ['TFIDR', 'MTFCC', "shared_block_roads", 'road_length']
            M_fields = ['TFIDR', 'MTFCC', "shared_block_roads", 'road_length']

            L_df = RoadMaker.make_table(self, in_fc=fc, fields=L_fields, shared=1)
            R_df = RoadMaker.make_table(self, in_fc=fc, fields=R_fields, shared=1)
            M_df = RoadMaker.make_table(self, in_fc=fc, fields=M_fields, shared=0)

            # def prepare_df(in_df_list=[L_df, R_df, M_df], group_by_fields=None):
            #     procesed_df = {}
            #     for df in in_df_list:
            #         temp_df =  df.groupby(group_by_fields)[]

            faces_df = pd.read_csv(os.path.join(RoadMaker.base_input_folder, 'faces_by_block.csv'),
                                   dtype={'geoid10': object,
                                          'STATEFP10': object})

            fc_df_L_df = pd.merge(left=faces_df, left_on="TFID", right=L_df, right_on='TFIDL', how='inner')
            fc_df_R_df = pd.merge(left=faces_df, left_on="TFID", right=R_df, right_on='TFIDR', how='inner')
            fc_df_M_df = pd.merge(left=faces_df, left_on="TFID", right=M_df, right_on='TFIDR', how='inner')

            # delete faces_data frame
            del faces_df

            fc_df_L_df = fc_df_L_df[fc_df_L_df.STATEFP10 == "{}".format(state)]
            fc_df_R_df = fc_df_R_df[fc_df_R_df.STATEFP10 == "{}".format(state)]
            fc_df_M_df = fc_df_M_df[fc_df_M_df.STATEFP10 == "{}".format(state)]
            fc_df_M_df.rename(columns={"TFIDR": "TFIDM"})

            fc_df_L_df['shared_road_length_meters'] = fc_df_L_df['road_length'] / 2
            fc_df_R_df['shared_road_length_meters'] = fc_df_R_df['road_length'] / 2
            fc_df_M_df['shared_road_length_meters'] = fc_df_M_df['road_length']

            left = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
                                'faces_block_shared_roads_L_{}.csv'.format(state))
            right = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
                                 'faces_block_shared_roads_R_{}.csv'.format(state))
            middle = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
                                  'faces_block_shared_roads_M_{}.csv'.format(state))

            for file_path, df in {left: fc_df_L_df, right: fc_df_R_df, middle: fc_df_M_df}.items():


                p = os.path.split(file_path)
                if not os.path.exists(path=p[0]):
                    os.makedirs(p[0])
                df.to_csv(file_path, index=False)


            grouped_fc_df_L_df = fc_df_L_df.groupby(['STATEFP10', 'geoid10', 'MTFCC'])[
                'shared_road_length_meters'].sum().reset_index()
            grouped_fc_df_L_df.rename(columns={"shared_road_length_meters": "shared_road_length_meters_L"}, inplace=True)

            grouped_fc_df_R_df = fc_df_R_df.groupby(['STATEFP10', 'geoid10', 'MTFCC'])[
                'shared_road_length_meters'].sum().reset_index()
            grouped_fc_df_R_df.rename(columns={"shared_road_length_meters": "shared_road_length_meters_R"}, inplace=True)

            grouped_fc_df_M_df = fc_df_M_df.groupby(['STATEFP10', 'geoid10', 'MTFCC'])[
                'shared_road_length_meters'].sum().reset_index()
            grouped_fc_df_M_df.rename(columns={"shared_road_length_meters": "shared_road_length_meters_M"}, inplace=True)


            # join all of the grouped featureclass
            master_df = reduce(lambda left, right: pd.merge(left, right, on=["STATEFP10", 'geoid10', 'MTFCC'], how='outer'),
                               [grouped_fc_df_L_df, grouped_fc_df_M_df, grouped_fc_df_R_df])

            # delete from memory
            del fc_df_L_df, fc_df_R_df, fc_df_M_df, grouped_fc_df_L_df, grouped_fc_df_R_df, grouped_fc_df_M_df

            master_df.fillna(0, inplace=True)

            master_df['total_shared_meters'] = master_df["shared_road_length_meters_L"] + master_df[
                "shared_road_length_meters_M"] + master_df["shared_road_length_meters_R"]
            master_df['total_shared_miles'] = master_df['total_shared_meters'] / 1609.344

            del master_df["shared_road_length_meters_L"], master_df['shared_road_length_meters_M'], master_df['shared_road_length_meters_R']

            # print(master_df)

            out_dir = os.path.join(self.output_folder, 'shared_roadmiles', 'csv')
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            master_df.to_csv(os.path.join(out_dir, "shared_road_miles_{}.csv".format(state)))
            print(out_dir, "shared_road_miles_{}.csv".format(state))

            # delete from memory
            del master_df
