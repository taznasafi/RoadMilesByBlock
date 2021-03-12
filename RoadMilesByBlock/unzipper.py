import zipfile
import os
import fnmatch

class Unzipper:

    def __init__(self, base_input_folder, base_output_folder):
        self.base_input_folder = base_input_folder
        self.base_output_folder = base_output_folder
        self.parsed_path_list = []


    def path_grabber(self, wildcard=None):

        for root, dirs, files in os.walk(self.base_input_folder):
            for file in fnmatch.filter(files, wildcard):
                self.parsed_path_list.append(os.path.join(root, file))
        print("i found {} file(s)".format(len(self.parsed_path_list)))
        
    def unzip(self, wildcard=None):
        Unzipper.path_grabber(self, wildcard=wildcard)
        for file_path in self.parsed_path_list:
            output = os.path.join(self.base_output_folder,os.path.basename(file_path).strip('.zip'))
            with zipfile.ZipFile(file=file_path, mode='r') as zip_ref:
                if not os.path.exists(os.path.join(self.base_output_folder,os.path.basename(file_path).strip(".zip"))):
                    #print("dir does not exits")
                    os.makedirs(output)
                    zip_ref.extractall(path=output)
                else:
                    #print(output)
                    zip_ref.extractall(path=output)
        