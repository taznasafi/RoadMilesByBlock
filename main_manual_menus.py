from bin import unzip_census_edges, \
    unzip_census_faces, _01_make_faces_table, \
    import_roads_from_edges_calculate_length, make_shared_road_mile

from RoadMilesByBlock import get_path, logger
# multiprocessor
import multiprocessing as mp
import time


def make_initial_data(unzip_eges=False, unzip_faces=False, make_faces=False):
    if unzip_eges:
        # unzip edges
        unzip_census_edges.unzip_edges(run=False)

        # unzip faces
    if unzip_faces:
        unzip_census_faces.unzip_faces(run=False)

    if make_faces:
        # import data1 from faces shapefiles
        _01_make_faces_table.import_table_from_faces(run=True)


def worker(state):
    start = time.time()
    print("\n********************************** State {} ***************************************\n".format(state))
    print('creating roads for state {}\n'.format(state))
    import_roads_from_edges_calculate_length.make_roads(run=True, calculate_fields=False, state_fips=state)
    print("calculating shared miles for state {}\n".format(state))
    make_shared_road_mile.create_shared_road_miles(run=True, state_fips=state)

    end = time.time()

    logger.timer(start, end, state)


if __name__ == '__main__':
    print("hi")
    print("\n****************************** making initial Faces **************************\n")
    start = time.time()
    make_initial_data(make_faces=False)
    logger.timer(start, time.time())

    print("\n****************************** making shared road miles by state **************************\n")


    num_process = 5
    pool = mp.Pool(processes=num_process)
    pool.map(worker, get_path.pathFinder.make_fips_list())
    pool.close()
    pool.join()
    end = time.time()

    print("\n****************************** end of the tasks **************************\n")
    print("multi-processing {} number of states".format(num_process))
    logger.timer(start, end)

