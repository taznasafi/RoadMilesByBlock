import os
from sys import exit

# create initial Data folder for input and output
if not os.path.exists(r'./data'):
    os.mkdir(r'./data')

input_path = r'./data/input'
output_path = r'./data/output'

if not os.path.exists(input_path):
    os.mkdir(input_path)


if not os.path.exists(output_path):
    os.mkdir(output_path)


if not os.path.exists('my_paths.py'):
    print("""PLEASE CREATE A PYTHON FILE CALLED: my_paths.py \n
    edges_zip_path = r"" \n
    faces_zip_path = r"" \n
    faces_gdb_by_state_base_path = r"" \n

    tl_2020_blocks = r""
    """)
    exit()