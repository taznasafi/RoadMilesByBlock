from RoadMilesByBlock import RoadMaker, os
from arcpy import Exists


def make_roads(run=False, calculate_fields=False, state_fips=None, gdb_name=None):
    roads = RoadMaker.RoadMaker()
    roads.out_gdb_name = gdb_name
    roads.output_folder = roads.base_input_folder
    roads.out_gdb = os.path.join(roads.output_folder, roads.out_gdb_name+".gdb")

    roads.create_gdb()
    if run:

        roads.shared_roads_from_edges(state=state_fips, cal_shared_road_miles=calculate_fields)
