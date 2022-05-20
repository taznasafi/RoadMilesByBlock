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
    def shp_to_gdb(self):

        shp_path_dict = get_path.pathFinder.get_shapefile_path_walk_dict(self.in_path)

        for shp_path, shp_name_list in shp_path_dict.items():

            if not arcpy.Exists(os.path.join(self.out_gdb, shp_name_list[0].strip(".zip"))):
                print(shp_name_list[0])
                arcpy.FeatureClassToFeatureClass_conversion(in_features=os.path.join(shp_path, shp_name_list[0]), out_path=self.out_gdb, out_name= shp_name_list[0].stri(".zip"))



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
                                             ("TFID", "STATEFP", "COUNTYFP", "TRACTCE", 'BLOCKCE'))
            df = pd.DataFrame(arr)

            df['geoid'] = df["STATEFP"] + df["COUNTYFP"] + df["TRACTCE"] + df['BLOCKCE']

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
    def shared_roads_from_edges(self, cal_road_miles=False, state=None,
                                gdb_root_path=my_paths.edges_gdb_by_state_base_path):
        """

        :param cal_road_miles: this is a switch to turn on and off calculating fields.
        :param state: State wildcard passed for parallel processing.
        :param gdb_root_path: please provide path to shapefiles root folder.

        This process creates roads from edges from state gdb, make sure to provide gdb from census.
        """
        # print(gdb_root_path)

        arcpy.Delete_management('in_memory/merged_edges')
        arcpy.Delete_management("temp")

        # get a list of shapefiles by county
        county_shapefile_path = get_path.pathFinder.get_shapefile_path_walk_dict(my_paths.edges_zip_path)

        # print(county_shapefile_path)

        master_county_list = []

        for folder, basename in county_shapefile_path.items():
            master_county_list.append(os.path.join(folder, basename[0]))

        filtered_state_county_list = get_path.pathFinder.filter_List_of_shapefiles_paths_with_wildcard(
            master_county_list, wildcard="tl_*_{}*_edges".format(state))

        output = os.path.join(self.out_gdb, 'road_miles_{}'.format(state))

        if not arcpy.Exists(output):
            # create a temp merged featureclass from county fcs
            print('merging all of {} counties into one fc'.format(len(filtered_state_county_list)))
            temp_name = arcpy.Merge_management(inputs=filtered_state_county_list, output="in_memory/merged_edges")

            # Replace a layer/table view name with a path to a dataset (which can be a layer file) or create the layer/table view within the script
            # The following inputs are layers or table views: "road_miles_12"

            # since we extract the edges from counties, there exits identical roads on the edges. to account for that we have to delete identical features
            print("********* Deleting Identical roads on the county line ****************************")
            arcpy.DeleteIdentical_management(in_dataset=temp_name,
                                             fields=["TLID", "TFIDL", "TFIDR", "MTFCC", "FULLNAME", 'Shape'],
                                             xy_tolerance="", z_tolerance="0")

            a = arcpy.FeatureClassToFeatureClass_conversion(in_features=temp_name,
                                                            out_name='road_miles_{}'.format(state),
                                                            out_path=self.out_gdb,
                                                            where_clause="""  MTFCC = 'S1100' OR 
                                                                        MTFCC = 'S1200' OR 
                                                                        MTFCC = 'S1400' OR
                                                                        MTFCC = 'S1500' OR
                                                                        MTFCC = 'S1630' OR
                                                                        MTFCC = 'S1640' OR
                                                                        MTFCC = 'S1710' OR
                                                                        MTFCC = 'S1720' OR
                                                                        MTFCC = 'S1730' OR
                                                                        MTFCC = 'S1740' OR
                                                                        MTFCC = 'S1780' OR
                                                                        MTFCC = 'S1820' OR
                                                                        MTFCC = 'S1830' """)
            arcpy.GetMessages(0)
            RoadMaker.gdb_output_dic['roads_from_edges'].append(output)

            RoadMaker.add_field(self, in_fc=output, field_name='shared_block_roads', field_type='SHORT')
            RoadMaker.add_field(self, in_fc=output, field_name='road_length', field_type='DOUBLE')

            arcpy.MakeFeatureLayer_management(in_features=output, out_layer="temp")

            # select roads that are shared among blocks and put 1 as shared road mile
            arcpy.SelectLayerByLocation_management(in_layer='temp', overlap_type="SHARE_A_LINE_SEGMENT_WITH",
                                                   select_features=my_paths.tl_2020_blocks,
                                                   selection_type='NEW_SELECTION')

            RoadMaker.calculate_field(self, in_fc='temp', in_field='shared_block_roads',
                                      expression=1)

            arcpy.SelectLayerByAttribute_management(in_layer_or_view='temp', selection_type="SWITCH_SELECTION")

            RoadMaker.calculate_field(self, in_fc='temp', in_field='shared_block_roads',
                                      expression=0)

            arcpy.SelectLayerByAttribute_management('temp', "CLEAR_SELECTION")

            # calculate geodesic length
            RoadMaker.calculate_field(self, in_fc=output, in_field='road_length',
                                      expression="!shape.geodesicLength@METERS!")
            arcpy.Delete_management('in_memory/merged_edges')
            arcpy.Delete_management("temp")

        else:
            RoadMaker.gdb_output_dic['roads_from_edges'].append(output)

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def make_df_from_fc(self, in_fc, fields=None):
        column_data = defaultdict(list)
        # print(in_fc)

        if fields == "*":
            field_list = [x.name for x in arcpy.ListFields(in_fc) if x.name != "SHAPE"]
        else:
            field_list = fields

        for field in field_list:

            with arcpy.da.SearchCursor(in_table=in_fc,
                                       field_names=field) as cur:
                for row in cur:
                    column_data[field].append(row[0])

        return pd.DataFrame(column_data)

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def make_shared_road_table(self, in_fc, fields, shared):
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
                path_link_list=RoadMaker.gdb_output_dic['roads_from_edges'],
                wildcard="*_{}".format(state))[0]
        except IndexError as error:
            print(error)
            print("Did not find State {}".format(state))

        else:

            L_fields = ['TFIDL', 'MTFCC', "shared_block_roads", 'road_length']
            R_fields = ['TFIDR', 'MTFCC', "shared_block_roads", 'road_length']
            M_fields = ['TFIDR', 'MTFCC', "shared_block_roads", 'road_length']

            # 50/50 method
            s_L_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=L_fields, shared=1)
            s_R_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=R_fields, shared=1)
            s_M_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=M_fields, shared=0)

            # independent method
            L_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=L_fields, shared=1)
            R_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=R_fields, shared=1)
            M_df = RoadMaker.make_shared_road_table(self, in_fc=fc, fields=M_fields, shared=0)

            # def prepare_df(in_df_list=[L_df, R_df, M_df], group_by_fields=None):
            #     procesed_df = {}
            #     for df in in_df_list:
            #         temp_df =  df.groupby(group_by_fields)[]

            # save the csv for later reference
            faces_df = pd.read_csv(os.path.join(RoadMaker.base_input_folder, 'faces_by_block.csv'),
                                   dtype={'geoid': object,
                                          'STATEFP': object})

            # merge the faces with edges independent
            fc_df_L_df = pd.merge(left=faces_df, left_on="TFID", right=L_df, right_on='TFIDL', how='inner')
            fc_df_R_df = pd.merge(left=faces_df, left_on="TFID", right=R_df, right_on='TFIDR', how='inner')
            fc_df_M_df = pd.merge(left=faces_df, left_on="TFID", right=M_df, right_on='TFIDR', how='inner')

            # merge the faces with edges 50/50
            s_fc_df_L_df = pd.merge(left=faces_df, left_on="TFID", right=s_L_df, right_on='TFIDL', how='inner')
            s_fc_df_R_df = pd.merge(left=faces_df, left_on="TFID", right=s_R_df, right_on='TFIDR', how='inner')
            s_fc_df_M_df = pd.merge(left=faces_df, left_on="TFID", right=s_M_df, right_on='TFIDR', how='inner')

            # delete faces_data frame from memory
            del faces_df

            # just makeing sure that we filter only the selected state
            fc_df_L_df = fc_df_L_df[fc_df_L_df.STATEFP == "{}".format(state)]
            fc_df_R_df = fc_df_R_df[fc_df_R_df.STATEFP == "{}".format(state)]
            fc_df_M_df = fc_df_M_df[fc_df_M_df.STATEFP == "{}".format(state)]
            fc_df_M_df.rename(columns={"TFIDR": "TFIDM"})

            s_fc_df_L_df = s_fc_df_L_df[s_fc_df_L_df.STATEFP == "{}".format(state)]
            s_fc_df_R_df = s_fc_df_R_df[s_fc_df_R_df.STATEFP == "{}".format(state)]
            s_fc_df_M_df = s_fc_df_M_df[s_fc_df_M_df.STATEFP == "{}".format(state)]
            s_fc_df_M_df.rename(columns={"TFIDR": "TFIDM"})

            # calculate the two columns in df
            fc_df_L_df[['method', 'road_length_meters']] = ["independent", fc_df_L_df['road_length']]
            fc_df_R_df[['method', 'road_length_meters']] = ["independent", fc_df_R_df['road_length']]
            fc_df_M_df[['method', 'road_length_meters']] = ["independent", fc_df_M_df['road_length']]

            # calculate two columns in df using the 50/50 method
            s_fc_df_L_df[['method', 'road_length_meters']] = ["50/50", s_fc_df_L_df['road_length'] / 2]
            s_fc_df_R_df[['method', 'road_length_meters']] = ["50/50", s_fc_df_R_df['road_length'] / 2]
            s_fc_df_M_df[['method', 'road_length_meters']] = ["50/50", s_fc_df_M_df['road_length']]

            # append the 50/50 edges/faces to independent df
            fc_df_L_df = fc_df_L_df.append(s_fc_df_L_df)
            fc_df_R_df = fc_df_R_df.append(s_fc_df_R_df)
            fc_df_M_df = fc_df_M_df.append(s_fc_df_M_df)

            # print(fc_df_L_df)

            # #saving outfile.
            # left = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
            #                     'faces_block_shared_roads_L_{}.csv'.format(state))
            # right = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
            #                      'faces_block_shared_roads_R_{}.csv'.format(state))
            # middle = os.path.join(RoadMaker.base_input_folder, "face_block_road", 'state_{}'.format(state),
            #                       'faces_block_shared_roads_M_{}.csv'.format(state))

            # #save the joined faces and road tables to csv
            # for file_path, df in {left: fc_df_L_df, right: fc_df_R_df, middle: fc_df_M_df}.items():
            #
            #
            #     p = os.path.split(file_path)
            #     if not os.path.exists(path=p[0]):
            #         os.makedirs(p[0])
            #     df.to_csv(file_path, index=False)

            # group the faces/roads by state, block id and MTFC categories and method
            grouped_fc_df_L_df = fc_df_L_df.groupby(['STATEFP', 'geoid', 'MTFCC', 'method'])[
                'road_length_meters'].sum().reset_index()

            # rename the columms
            grouped_fc_df_L_df.rename(columns={"road_length_meters": "road_length_meters_L"}, inplace=True)

            grouped_fc_df_R_df = fc_df_R_df.groupby(['STATEFP', 'geoid', 'method', 'MTFCC'])[
                'road_length_meters'].sum().reset_index()
            grouped_fc_df_R_df.rename(columns={"road_length_meters": "road_length_meters_R"}, inplace=True)

            grouped_fc_df_M_df = fc_df_M_df.groupby(['STATEFP', 'geoid', 'method', 'MTFCC'])[
                'road_length_meters'].sum().reset_index()
            grouped_fc_df_M_df.rename(columns={"road_length_meters": "road_length_meters_M"}, inplace=True)

            # join the left, middle, and right grouped dataframes into one dataframe
            master_df = reduce(
                lambda left, right: pd.merge(left, right, on=["STATEFP", 'geoid', 'method', 'MTFCC'], how='outer'),
                [grouped_fc_df_L_df, grouped_fc_df_M_df, grouped_fc_df_R_df])

            # delete not necessary df from memory
            del fc_df_L_df, fc_df_R_df, fc_df_M_df, grouped_fc_df_L_df, grouped_fc_df_R_df, grouped_fc_df_M_df

            master_df.fillna(0, inplace=True)

            # convert meters to miles
            master_df['total_meters'] = master_df["road_length_meters_L"] + master_df[
                "road_length_meters_M"] + master_df["road_length_meters_R"]
            master_df['total_miles'] = master_df['total_meters'] / 1609.344

            master_df.sort_values(by=["STATEFP", 'geoid', 'method', 'MTFCC'], inplace=True)

            # delete the meter colums?
            del master_df["road_length_meters_L"], master_df['road_length_meters_M'], master_df['road_length_meters_R']

            # print(master_df)

            out_dir = os.path.join(self.output_folder, 'road_miles', 'csv')
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            master_df.to_csv(os.path.join(out_dir, "road_miles_{}.csv".format(state)))
            print(out_dir, "road_miles_{}.csv".format(state))

            # delete from memory
            del master_df

    @logger.arcpy_exception(logger.create_error_logger())
    @logger.event_logger(logger.create_logger())
    def make_blocks_with_road_miles_fc(self, state):

        block_fc_list = get_path.pathFinder(env=my_paths.tl_2020_blocks_by_state).get_file_path_with_wildcard_from_gdb(
            "T{}".format(state))

        csv = os.path.join(self.in_path, "road_miles_{}.csv".format(state))

        print(csv)
        try:

            csv_df = pd.read_csv(csv, dtype={'geoid': object})
        except:
            print("there is an error in reading csv: {}".format(csv))
            return

        del csv_df['Unnamed: 0']

        print(csv_df.columns)

        for fc in block_fc_list:

            block_df = RoadMaker.make_df_from_fc(self, in_fc=fc, fields=["GEOID"])

            df_merge = pd.merge(left=block_df, left_on="GEOID", right=csv_df, right_on='geoid', how="outer")

            del df_merge['geoid']

            df_merge['STATEFP'] = "{}".format(state)

            df_merge['MTFCC'].fillna("no road", inplace=True)
            df_merge['method'].fillna("no road", inplace=True)
            df_merge['total_miles'].fillna(0, inplace=True)
            df_merge['total_meters'].fillna(0, inplace=True)

            df_merge = df_merge[["STATEFP", "GEOID", 'MTFCC', 'method', 'total_meters', 'total_miles']]

            df_merge.columns = [c.lower() for c in df_merge.columns]

            out_dir = os.path.join(self.output_folder, 'all_blocks_with_road_miles', 'csv')
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            df_merge.to_csv(os.path.join(out_dir, "all_blocks_with_road_miles_{}.csv".format(state)), index=False)
            print(out_dir, "road_miles_{}.csv".format(state))
