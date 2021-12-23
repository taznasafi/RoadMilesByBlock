from RoadMilesByBlock import RoadMaker

def import_table_from_faces(run=False):

    if run:
        table_maker = RoadMaker.RoadMaker()
        table_maker.extract_data_from_shapefiles()

