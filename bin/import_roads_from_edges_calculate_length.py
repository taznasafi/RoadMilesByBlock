from RoadMilesByBlock import RoadMaker, os
from arcpy import Exists


def make_roads(run=False, calculate_fields=False, state_fips=None):
    roads = RoadMaker.RoadMaker()
    roads.out_gdb_name = "tl_2019_roads_from_edges"
    roads.output_folder = roads.base_input_folder
    roads.out_gdb = os.path.join(roads.output_folder, roads.out_gdb_name+".gdb")


    if run:
        roads.create_gdb()
        roads.roads_from_edges(state=state_fips, cal_fields=calculate_fields)
