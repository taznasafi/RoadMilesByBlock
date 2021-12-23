from RoadMilesByBlock import RoadMaker, get_path, os


def create_shared_road_miles(run=False, state_fips=None):
    shared_roads = RoadMaker.RoadMaker()
    shared_roads.in_gdb_path = shared_roads.gdb_output_dic['tl_roads_from_edges']
    shared_roads.output_folder = shared_roads.base_output_folder

    if run:
        shared_roads.create_shared_road_mile(state=state_fips)
