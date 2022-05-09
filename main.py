from bin import _01A_unzip_census_edges, \
    _01B_unzip_census_faces, _01C_make_faces_table, \
    _02_import_roads_from_edges_calculate_length, _03_make_shared_road_mile, _04_export_full_blocks

from RoadMilesByBlock import get_path, logger

import time


def make_initial_data(unzip_edges=False, unzip_faces=False, make_faces=False):
    if unzip_edges:
        # unzip edges
        _01A_unzip_census_edges.unzip_edges(run=True)

        # unzip faces
    if unzip_faces:
        _01B_unzip_census_faces.unzip_faces(run=True)

    if make_faces:
        # import data1 from faces shapefiles
        _01C_make_faces_table.import_table_from_faces(run=True)




if __name__ == '__main__':
    print("hi")
    print("\n****************************** making initial Faces & Edges **************************\n")
    start = time.time()
    make_initial_data(unzip_edges=False, unzip_faces=False)
    make_initial_data(make_faces=False)
    logger.timer(start, time.time())

    print("\n****************************** making shared road miles by state **************************\n")

    for state in get_path.pathFinder.make_fips_list():
        start = time.time()
        print("\n********************************** State {} ***************************************\n".format(state))
        print('creating roads for state {}\n'.format(state))
        _02_import_roads_from_edges_calculate_length.make_roads(run=False, calculate_fields=True, state_fips=state,
                                                                gdb_name="tl_roads_from_edges")
        print("calculating shared miles for state {}\n".format(state))
        _03_make_shared_road_mile.create_shared_road_miles(run=False, state_fips=state)

        print("exporting blocks for state {}\n".format(state))
        _04_export_full_blocks.export_full_blocks(run=True, state_fips=state)

        end = time.time()

        logger.timer(start, end, state)
