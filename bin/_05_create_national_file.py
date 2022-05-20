from RoadMilesByBlock import RoadMaker, os, get_path
import pandas as pd


def create_national_file(run=False):
    fileMaker = RoadMaker.RoadMaker()
    fileMaker.output_folder = os.path.join(fileMaker.base_output_folder, "all_blocks_with_road_miles", 'csv')

    if run:
        csv_list = get_path.pathFinder(env=fileMaker.output_folder).path_grabber(wildcard="*.csv")
        df_list = []
        for csv in csv_list:
            df = pd.read_csv(csv, dtype={"statefp": object, 'geoid': object})
            df_list.append(df)

        print("merging {} number of csvs".format(len(df_list)))
        master_df = pd.concat(df_list)
        print("outputing national csv file")
        master_df.to_csv(os.path.join(fileMaker.output_folder, "__all_blocks_with_road_miles_ALL_STATES.csv"),
                         index=False)
