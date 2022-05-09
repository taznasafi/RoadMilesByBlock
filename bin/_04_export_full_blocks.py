from RoadMilesByBlock import RoadMaker, os


def export_full_blocks(run=False, state_fips=None):
    roads = RoadMaker.RoadMaker()
    roads.output_folder = roads.base_output_folder
    roads.in_path = os.path.join(roads.output_folder, "road_miles", 'csv')

    if run:
        roads.make_blocks_with_road_miles_fc(state=state_fips)
