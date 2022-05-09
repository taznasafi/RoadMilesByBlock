import fnmatch
import os
import arcpy
import pandas as pd

from enum import Enum
from collections import defaultdict
import re

class pathFinder:


    def __init__(self, env=None, outPathFolder=None, outPathGDB = None):
        self.env = env
        self.outPathFolder = outPathFolder
        self.outPathGDB = outPathGDB

    def path_grabber(self, wildcard=None):
        parsed_path_list = []
        for root, dirs, files in os.walk(self.env):
            for file in fnmatch.filter(files, wildcard):
                parsed_path_list.append(os.path.join(root, file))
        return list(parsed_path_list)

    def gdb_path_grabber(self, wildcard=None):
        parsed_path_list = []
        for root, dirs, files in os.walk(self.env):
            for dir in fnmatch.filter(dirs, wildcard):
                parsed_path_list.append(os.path.join(root, dir))

        return list(parsed_path_list)


    def get_path_for_all_feature_from_gdb(self, type ="Polygon"):
        gdbPath =[]
        for dirpath, dirnames, filenames in arcpy.da.Walk(self.env, datatype="FeatureClass", type=type):
            for filename in filenames:
                gdbPath.append(os.path.join(dirpath, filename))

        return list(gdbPath)

    def get_file_path_with_wildcard_from_gdb(self, wildcard=None, type="Polygon"):
        gdbPath = []

        if wildcard is not None:


            for dirpath, dirnames, filenames in arcpy.da.Walk(self.env, datatype="FeatureClass", type=type):
                for filename in fnmatch.filter(filenames, wildcard):
                    gdbPath.append(os.path.join(dirpath, filename))
            print("\nfound {} many file(s)".format(len(gdbPath)))

        return list(gdbPath)



    @classmethod
    def get_shapefile_path_walk(cls, path):
        file_loc = []

        # use os.walk to find the root, directory, and files
        for root, dirs, files in os.walk(path):
            # create a loop by files
            for file in files:
                # for the files that endswith .shp, join the root and file
                if file.endswith(".shp"):
                    # create a local variable that we can assign the root and file path then loop it
                    path = os.path.join(root, file)
                    # append the path in our file_loc list
                    file_loc.append(path)

        return list(file_loc)


    @classmethod
    def get_shapefile_path_wildcard(cls, path, wildcard):
        file_loc = []

        # use os.walk to find the root, directory, and files
        for root, dirs, files in os.walk(path):
            # create a loop by files
            for file in fnmatch.filter(files, wildcard+".shp"):
                # for the files that endswith .shp, join the root and file
                file_loc.append(os.path.join(root, file))

        if list(file_loc) == 'NoneType':
            raise Warning("Did not find path, check your wild card")

        else:
            return list(file_loc)

    @classmethod
    # create a list of fips from the table.
    def make_fips_list(cls):
        import pandas as pd
        Fips_table_path = r"D:\FCC_GIS_Projects\MFII\csv\state FiPS.txt"
        data = pd.read_csv(Fips_table_path, sep='|')
        data["STATE"] = data["STATE"].astype(str)
        data['STATE'] = data["STATE"].apply(lambda x: x.zfill(2))
        return data.STATE.tolist()


    @classmethod
    def make_state_fips_name_dict(cls):

        Fips_table_path = r"D:\FCC_GIS_Projects\MFII\csv\state FiPS.txt"
        data = pd.read_csv(Fips_table_path, sep='|',dtype=object)
        return data.to_dict(orient="records")

    @classmethod
    def query_provider_by_FIPS(cls, path, fips):
        import pandas as pd
        df = pd.read_csv(path)
        fips_query = df.query("stateFIPS ==" + str(fips))
        fips_query = fips_query.dropna(axis=1, how="any")
        return list(fips_query.applymap(int).values.flatten()[1:])

    @classmethod
    def query_provider_pid_by_provider_FRN(cls, table_path, frn):
        df = pd.read_csv(table_path)
        df['f477_provider_frn'] = df["f477_provider_frn"].apply(lambda x: "%010d" % x)
        query_results = df.query("f477_provider_frn == '{}'".format(frn))
        #print(query_results)
        dic = query_results.to_dict('records')
        return dic[0]

    @classmethod
    def query_pid_by_dba(cls, table_path, dba):

        df = pd.read_csv(table_path)
        # print(df)
        query_results = df.query("dba =='{}'".format(dba))
        dic = query_results.to_dict('records')
        #print(dic)
        return dic[0]

    @classmethod
    def extract_dba(cls, fc_input, field_name_list):

        return list(set([row[0] for row in arcpy.da.SearchCursor(fc_input, field_name_list)]))[0]



    @classmethod
    def query_pid_by_state_fips(cls, table_path=r"D:\FCC_GIS_Projects\jon\cetc_subsidy-pid_spin_sac_fhcs_amount-with_territories-sep2017-19jun2018.csv", state_fips=None):

        df = pd.read_csv(table_path)
        # print(df)
        query_results = df.query("cetc_state_fips =='{}'".format(state_fips))
        dic = query_results.to_dict('records')
        # print(dic)
        return dic

    @classmethod
    def filter_List_of_shapefiles_paths_with_wildcard(cls, path_link_list, wildcard):
        sorted_list = []
        for path_link in path_link_list:
            if fnmatch.fnmatch(os.path.basename(path_link), wildcard + ".shp"):
                sorted_list.append(path_link)
        print("found {} number of files".format(len(sorted_list)))
        return list(sorted_list)



    @classmethod
    def filter_List_of_featureclass_paths_with_wildcard(cls, path_link_list, wildcard):
        sorted_list = []
        for path_link in path_link_list:
            if fnmatch.fnmatch(os.path.basename(path_link), wildcard):
                sorted_list.append(path_link)
        print("found {} number of files".format(len(sorted_list)))
        return list(sorted_list)


    @classmethod
    def get_shapefile_path_walk_dict(cls, path):


        file_dict = defaultdict(list)

        # use os.walk to find the root, directory, and files
        for root, dirs, files in os.walk(path):
            # create a loop by files
            for file in files:
                # for the files that endswith .shp, join the root and file
                if file.endswith(".shp"):
                    # create a local variable that we can assign the root and file path then loop it
                    file_dict[root].append(file)


        return file_dict

    def create_number_provider_per_state(self, regex = r"T(?P<state>\d{1,2})_(?P<pid>\d{1,2})(?P<cetc_sac>\w+)?", table_outpu=None):
        from collections import defaultdict

        fc_list = self.get_path_for_all_feature_from_gdb()

        file_path_dict = defaultdict(list)

        for x in fc_list:
            file_path_dict[os.path.dirname(x)].append(os.path.basename(x))


        #complete_dict = defaultdict(list)
        #for key, values in file_path_dict.items():
        #    for x in values:

        #        regex = regex
        #        regex_dict = re.search(regex, x).groupdict()
        #        complete_dict[regex_dict['state']].append(regex_dict["pid"])


        return file_path_dict


    @classmethod
    def get_number_of_provider_from_attribute_table(cls,in_feature, field):

        values = [row[0] for row in arcpy.da.SearchCursor(in_feature, field)]

        return set(values)

    @classmethod
    def findField(cls, fc, field):
        fieldnames = [field.name for field in arcpy.ListFields(fc)]
        if field in fieldnames:
            return field
        else:
            return "pass"


    @classmethod
    def make_list_from_filename(cls, inlist,
                                regex = r"^dagg_(?P<state>\d{1,2})_(?P<pid>\d{1,3})_(?P<pname>\w.+)_subsidized.+$"):

        def check_key(dt, key):
            if key in dt:
                #print("key exits")
                return True
            else:
                return False

        complete_dict = defaultdict(set)

        key = 0
        for name in inlist:

            regex_dict = re.search(regex, os.path.basename(name)).groupdict()
            #print(regex_dict)

            if check_key(regex_dict, 'pid'):
                complete_dict[name].add((regex_dict["pname"],regex_dict['pid']))
            else:
                complete_dict[name].add(regex_dict['pname'])

                key +=1

        return dict(complete_dict)
