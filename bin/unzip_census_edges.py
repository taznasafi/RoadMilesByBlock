from RoadMilesByBlock import unzipper
import my_paths

def unzip_edges(run=False):
    edges_unzipper = unzipper.Unzipper(base_input_folder=my_paths.edges_zip_path,
                                   base_output_folder=my_paths.edges_zip_path)

    if run:
        edges_unzipper.unzip(wildcard="*.zip")


if __name__ == "__main__":

    print("you have chosen to unzip faces")
    unzip_edges(run=True)
