import arcpy
import pandas as pd
import fnmatch
import os

arcpy.env.parallelProcessingFactor = "90%"

def make_state_fips_name_dict():
    Fips_table_path = r"D:\FCC_GIS_Projects\MFII\csv\state FiPS.txt"
    data = pd.read_csv(Fips_table_path, sep='|', dtype=object)
    return data.to_dict(orient="records")

def get_file_path_with_wildcard_from_gdb(env, wildcard=None, type="Polygon"):
    gdbPath = []

    if wildcard is not None:

        for dirpath, dirnames, filenames in arcpy.da.Walk(env, datatype="FeatureClass", type=type):
            for filename in fnmatch.filter(filenames, wildcard):
                gdbPath.append(os.path.join(dirpath, filename))
        print("\nfound {} many file(s)".format(len(gdbPath)))

    return list(gdbPath)

hex_8_path = r"D:\FCC_GIS_Projects\BDC\scripts\HexyGrid\data\input\extracted_zipfiles\US Hex 9s\Level_9_h3_hex.gdb"
roads_path = r"D:\Census_Data\census_related_projects\RoadMilesByBlock\data\input\tl_2019_roads_from_edges.gdb"

states_dict = make_state_fips_name_dict()

try:

    for states in states_dict:
        print(states["STATE_NAME"].replace(" ", "_"), states['STATE'])

        hex_fc_list = get_file_path_with_wildcard_from_gdb(env=hex_8_path, wildcard="{}_hex9s".format(states['STATE_NAME'].replace(" ", "_")))

        road_fc = get_file_path_with_wildcard_from_gdb(env=roads_path, wildcard="*_{}".format(states['STATE'].replace(" ", "_")), type="Polyline")

        if len(hex_fc_list)==1 and len(road_fc)==1:
            print("making hex fc in memory")
            arcpy.MakeFeatureLayer_management(in_features=hex_fc_list[0],out_layer="memory/hex")
            print("adding new field")
            arcpy.AddField_management(in_table="memory/hex", field_name="road", field_type="SHORT")
            print("adding default value")
            with arcpy.da.UpdateCursor('memory/hex', 'road') as cur:
                for row in cur:
                    row[0]= 0
                    cur.updateRow(row)
            # arcpy.CalculateField_management(in_table="memory/hex", field='road', expression=0,expression_type="PYTHON3")
            print("making road features")
            arcpy.MakeFeatureLayer_management(in_features=road_fc[0], out_layer="memory/road")
            print("selecting by location")
            arcpy.SelectLayerByLocation_management(in_layer='memory/hex',
                                                   overlap_type="INTERSECT",
                                                   select_features="memory/road")

            arcpy.CalculateField_management(in_table="memory/hex", field='road', expression=1,expression_type="PYTHON3")

            arcpy.Delete_management("memory/hex")
            arcpy.Delete_management("memory/road")

except arcpy.ExecuteError:

    msgs = "\n*************\n{}\n*************\n".format(arcpy.GetMessages(2))


    print(msgs)
    print("something went wrong")
    arcpy.Delete_management("memory/hex")
    arcpy.Delete_management("memory/road")


