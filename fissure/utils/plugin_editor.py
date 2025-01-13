#!/usr/bin/python3
"""Plugin Editor Functionality
"""
import os
import csv
from typing import List
from fissure.utils import PLUGIN_DIR
from fissure.utils.plugin import TABLES_FUNCTIONS
import fissure.utils.library
import json
import shutil

TABLE_FIELDS = {
    'protocols': [("index", int, None), ("protocol_name", str), ("data_rates", float, None), ("median_packet_lengths", float, None)]
}


def plugin_exists(name: str, directory: os.PathLike = PLUGIN_DIR):
    """Check if Plugin Exists

    Check if plugin and its expected file structure exists.

    Parameters
    ----------
    name : str
        Plugin name
    directory : os.PathLike, optional
        Directory for plugins, by default PLUGIN_DIR

    Returns
    -------
    bool
        Plugin exists
    """
    basepath = os.path.join(directory, name)
    if os.path.isdir(basepath):
        if os.path.isdir(os.path.join(basepath, 'tables')):
            for entry in TABLES_FUNCTIONS:
                if not os.path.isfile(os.path.join(basepath, 'tables', entry[0])):
                    return False
        else:
            return False
        if not os.path.isdir(os.path.join(basepath, 'install_files')):
            return False
        return True
    else:
        return False


def create_plugin(name: str, directory: os.PathLike = PLUGIN_DIR):
    """Create Plugin Directory and File Structure

    Parameters
    ----------
    name : str
        Plugin name
    directory : os.PathLike, optional
        Directory for plugins, by default PLUGIN_DIR
    """
    print('\nDIRECTORY: ' + str(directory))
    print('NAME: ' + str(name))
    print('TABLES DIR: ' + os.path.join(directory, name, 'tables') + '\n')
    # Create plugin directory structure
    os.makedirs(os.path.join(directory, name), 0o777, True)
    os.makedirs(os.path.join(directory, name, 'tables'), 0o777, True)
    os.makedirs(os.path.join(directory, name, 'install_files'), 0o777, True)

    # Create empty tables
    for entry in TABLES_FUNCTIONS:
        if not os.path.isfile(os.path.join(directory, name, 'tables', entry[0])):
            # table file does not exist; create
            with open(os.path.join(directory, name, 'tables', entry[0]), 'w') as f:
                f.write('')


# def read_protocol_csv(file: os.PathLike):
#     entries = {}
#     with open(file, 'r') as f:
#         reader = csv.reader(f, dialect='unix', quotechar="'")
#         for row in reader:
#             # Add protocol to entries
#             entries[row[1]] = {
#                 "data_rates": None if len(row[2]) == 0 else float(row[2]),
#                 "median_packet_lengths": None if len(row[3]) == 0 else float(row[3])
#             }
#     return entries


# def read_modulation_types_csv(file: os.PathLike):
#     protocols = {}
#     with open(file, 'r') as f:
#         reader = csv.reader(f, dialect='unix', quotechar="'")
#         for row in reader:
#             print(row)
#             # add mod_type to protocol
#             if row[1] in protocols.keys():
#                 # protocol already exists
#                 protocols[row[1]].append(row[2])
#             else:
#                 protocols[row[1]] = [row[2]]
#     return protocols


# def read_packet_types(file: os.PathLike):
#     pkt_types = {}
#     with open(file, 'r') as f:
#         reader = csv.reader(f, dialect='unix', quotechar="'")
#         for row in reader:
#             # add pkt_type to protocol
#             if row[1] in pkt_types.keys():
#                 # protocol already exists
#                 pkt_types[row[1]].append(row[2:])
#             else:
#                 pkt_types[row[1]] = [row[2:]]
#     return pkt_types


# def write_protocol_csv(file: os.PathLike, protocol_name: str, data_rates: float=None, median_packet_lengths: float=None):
#     with open(file, 'a') as f:
#         writer = csv.writer(f, dialect='unix', quotechar="'")
#         writer.writerow([None, protocol_name, data_rates, median_packet_lengths])


class PluginEditor(object):
    def __init__(self, name: str, directory: os.PathLike = PLUGIN_DIR):
        # Create or ensure plugin file structure aligns to expectations
        create_plugin(name, directory)

        # Create class variables
        self.basepath = os.path.join(PLUGIN_DIR, name)
        self.name = name

        # Import plugin data
        self.__importData__()
        self.install_files = self.list_filepaths(os.path.join(self.basepath, "install_files"))


    def __importData__(self):
        """
        Packages the table data from CSV files in the 'tables' folder into a dictionary.
        Returns the packaged data in JSON format.
        """
        tables_path = os.path.join(self.basepath, "tables")
        table_data = {}

        for file_name in os.listdir(tables_path):
            if file_name.endswith(".csv"):
                table_name = os.path.splitext(file_name)[0]
                
                # Initialize list to store rows for this table
                table_data[table_name] = []

                csv_file_path = os.path.join(tables_path, file_name)
                with open(csv_file_path, "r", newline="") as csv_file:
                    reader = csv.reader(csv_file)
                    for row in reader:
                        table_data[table_name].append(row)

        self.table_data = json.dumps(table_data)  # Convert the data to JSON format


        # Read protocols file
        # self.protocols = read_protocol_csv(os.path.join(self.basepath, 'tables', 'protocols.csv'))

        # # Initialize remainder of protocols structure
        # for protocol in self.protocols:
        #     self.protocols[protocol]['mod_types'] = []

        # # Read mod types file and merge into protocols
        # mod_types = read_modulation_types_csv(os.path.join(self.basepath, 'tables', 'modulation_types.csv'))
        # for protocol in mod_types.keys():
        #     if protocol in self.protocols:
        #         self.protocols[protocol]['mod_types'] = mod_types[protocol]
        #     else:
        #         raise RuntimeError('`modulation_types.csv` contains protocol ' + str(protocol) + ' but ' + str(protocol) + ' is not in `protocols.csv`')

        # # Read packet types file and merge into protocols
        # pkt_types = read_packet_types(os.path.join(self.basepath, 'tables', 'packet_types.csv'))
        # for protocol in pkt_types.keys():
        #     if protocol in self.protocols:
        #         self.protocols[protocol]['pkt_types'] = pkt_types[protocol]
        #     else:
        #         raise RuntimeError('`packet_types.csv` contains protocol ' + str(protocol) + ' but ' + str(protocol) + ' is not in `protocols.csv`')

        # print('PROTOCOLS: ' + str(self.protocols))


    def list_filepaths(self, root_folder):
        """
        Recursively lists all filepaths in the given directory and its subdirectories, relative to the root_folder.

        Parameters:
            root_folder (str): The root directory to search.

        Returns:
            list: A list of filepaths relative to the root_folder.
        """
        filepaths = []
        for dirpath, _, filenames in os.walk(root_folder):
            for filename in filenames:
                full_path = os.path.join(dirpath, filename)
                relative_path = os.path.relpath(full_path, root_folder)
                filepaths.append(relative_path)
        
        return filepaths


    def applyChanges(self, table_data_json: dict, supporting_files_data_json: dict, os_version: str):
        """
        Overwrites the csv files with table data from the Plugin Editor tab.
        """
        # Delete Plugin (then rewrite)
        self.deletePlugin(self.name, True, os_version)

        # Initialize Plugin
        self.__init__(self.name, PLUGIN_DIR)

        # Rewrite Tables Folder/CSV Files
        # Convert the JSON back to a dictionary
        table_data = json.loads(table_data_json)
        # print(table_data)
        
        # Find the 'tables' folder
        tables_path = None
        for root, dirs, _ in os.walk(self.basepath):
            if "tables" in dirs:
                tables_path = os.path.join(root, "tables")
                break

        if not tables_path:
            # print("No 'tables' folder found.")
            return

        # Iterate over the table data
        for table_name, data in table_data.items():
            rows = data["rows"]

            # Construct the CSV file path for the current table
            csv_file_path = os.path.join(tables_path, f"{table_name}.csv")
            
            # Write the data to the CSV file
            with open(csv_file_path, "w", newline="") as csv_file:
                writer = csv.writer(csv_file)
                # writer.writerow(headers)  # Write the headers first
                writer.writerows(rows)  # Write the rows
            
            # Optionally, notify the user for each table
            # print(f"Table '{table_name}' has been updated in CSV.")

        # QtWidgets.QMessageBox.information(None, "Success", "CSV files have been updated!")

        # Update Database
        try:                
            # Maintain a Connection to the Database
            conn = fissure.utils.library.openDatabaseConnection()

            for table_name, data in table_data.items():
                rows = data["rows"]
                headers = rows[0]
                for row in rows[1:]:
                    fissure.utils.library.addTableRow(conn, table_name, headers, row)
            # print(table_name)
            # print(rows)

        except Exception as e:
            print(f"An error occurred while adding row to database table: {e}")
            return
        finally:
            conn.close()    

        # Update Supporting Files
        # print("AAAAAAAAAA")
        # print(supporting_files_data_json)
        supporting_files_data = json.loads(supporting_files_data_json)

        # Iterate over each key and value in the dictionary
        for key, value in supporting_files_data.items():
            # print(f"Key: {key}")
            
            # Check if the value is a list and not empty
            if isinstance(value, list) and value:
                # print(f"  {key} contains {len(value)} items:")
                
                # Iterate through items in the list
                for item in value:
                    if isinstance(item, dict):
                        self.addSupportFiles(key, item, os_version)

                        # # If item is a dictionary, print its keys and values
                        # for sub_key, sub_value in item.items():
                        #     print(f"    {sub_key}: {sub_value}")

                    else:
                        # If item is not a dictionary, print it directly
                        print(f"    {item}")
            else:
                pass
                # print(f"  {key} is empty or not a list.")
        
        # print("BBBBBBBBBBBBB")


    def deletePlugin(self, plugin_name: str, delete_from_library: bool, os_version: str):
        """
        Deletes plugins from the library and database.
        """
        if not os.path.isdir(self.basepath):
            print(f"Plugin folder '{plugin_name}' does not exist.")
            # QMessageBox.critical(None, "Error", f"Plugin folder '{plugin_name}' does not exist.")
            return

        # Remove from library/database
        if delete_from_library:
            try:
                # Find the 'tables' folder
                tables_path = None
                for root, dirs, _ in os.walk(self.basepath):
                    if "tables" in dirs:
                        tables_path = os.path.join(root, "tables")
                        break

                if not tables_path:
                    print("No 'tables' folder found.")
                    return
                
                # Maintain a Connection to the Database
                conn = fissure.utils.library.openDatabaseConnection()
        
                # Iterate through all CSV files in the folder
                for file_name in os.listdir(tables_path):
                    if file_name.endswith(".csv"):
                        table_name = os.path.splitext(file_name)[0]
                        csv_file_path = os.path.join(tables_path, file_name)

                        print(f"Processing table: {table_name} from file: {csv_file_path}")

                        try:
                            with open(csv_file_path, "r", newline="") as csv_file:
                                reader = csv.reader(csv_file)

                                # Skip the first row (header)
                                next(reader, None)

                                for row in reader:
                                    # Call the appropriate deletion function for the current table
                                    self.deleteTableRow(conn, table_name, row, os_version)
                        except Exception as e:
                            print(f"Error processing file '{csv_file_path}': {e}")
                            
                print(f"Deleted associated library files and database entries for plugin: {plugin_name}")
            except:
                print(f"An error occurred while deleting the plugin: {e} from the library/database. Plugin folder not deleted.")
                return
            finally:
                conn.close()

        # Delete the plugin folder
        try:
            shutil.rmtree(self.basepath)
            print(f"Deleted plugin folder: {self.basepath}")
        except Exception as e:
            print(f"An error occurred while deleting the plugin folder: {e}")


    def deleteTableRow(self, conn, table_name: str, row: list, os_version: str):
        """
        Handles a single row for a specific table by calling the appropriate deletion function.

        Parameters:
        ----------
        table_name : str
            Name of the table being processed.
        row : list
            Row data from the CSV file.
        """
        # Get Row ID if Exact Match
        print("Delete table row")
        print(table_name)
        print(row)
        row_id = fissure.utils.library.findMatchingRow(conn, table_name, row)  # Fix this
        delete_files = True
        print(row_id)
    
        # Remove from Database/Library
        if row_id:
            if table_name == "archive_collection":
                pass  # Extra deletion steps go here
            elif table_name == "archive_favorites":
                pass  # Extra deletion steps go here
            elif table_name == "attack_categories":
                pass  # Extra deletion steps go here
            elif table_name == "attacks":
                # Delete Python Files and Flow Graphs
                get_file = row[6]
                get_version = row[8]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "Single-Stage Flow Graphs", get_file)

                        # Remove files if they exist
                        for extension in [".py", ".grc"]:
                            file_path = get_path.replace(".py", extension)
                            if os.path.isfile(file_path):
                                os.system(f'rm "{file_path}"')
            elif table_name == "conditioner_flow_graphs":
                # Delete Python Files and Flow Graphs
                get_file = row[10]
                get_version = row[6]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "TSI Flow Graphs", "Conditioner", get_file)

                        # Remove files if they exist
                        for extension in [".py", ".grc"]:
                            file_path = get_path.replace(".py", extension)
                            if os.path.isfile(file_path):
                                os.system(f'rm "{file_path}"')
            elif table_name == "demodulation_flow_graphs":
                # Delete Python Files and Flow Graphs
                get_file = row[4]
                get_version = row[6]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "PD Flow Graphs", get_file)

                        # Remove files if they exist
                        for extension in [".py", ".grc"]:
                            file_path = get_path.replace(".py", extension)
                            if os.path.isfile(file_path):
                                os.system(f'rm "{file_path}"')
            elif table_name == "detector_flow_graphs":
                # Delete Python Files and Flow Graphs
                get_file = row[3]
                get_version = row[5]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "TSI Flow Graphs", "Detectors", get_file)

                        # Remove files if they exist
                        for extension in [".py", ".grc"]:
                            file_path = get_path.replace(".py", extension)
                            if os.path.isfile(file_path):
                                os.system(f'rm "{file_path}"')
            elif table_name == "inspection_flow_graphs":
                # Delete Python Files and Flow Graphs
                get_file = row[2]
                get_version = row[3]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "Inspection Flow Graphs", get_file)

                        # Remove files if they exist
                        for extension in [".py", ".grc"]:
                            file_path = get_path.replace(".py", extension)
                            if os.path.isfile(file_path):
                                os.system(f'rm "{file_path}"')
            elif table_name == "modulation_types":
                pass  # Extra deletion steps go here
            elif table_name == "packet_types":
                pass  # Extra deletion steps go here
            elif table_name == "protocols":
                pass  # Extra deletion steps go here
            elif table_name == "soi_data":
                pass  # Extra deletion steps go here
            elif table_name == "triggers":
                # Delete Python Files
                get_file = row[4]
                get_version = row[6]

                if get_file and get_version:
                    if get_version in ["maint-3.8", "maint-3.10"]:
                        library_path = (
                            fissure.utils.FLOW_GRAPH_LIBRARY_3_8
                            if get_version == "maint-3.8"
                            else fissure.utils.FLOW_GRAPH_LIBRARY_3_10
                        )
                        get_path = os.path.join(library_path, "Triggers", get_file)

                        # Remove file if it exists
                        if os.path.isfile(get_path):
                            os.system(f'rm "{get_path}"')

                # Secondary Trigger Files (Future)

            else:
                print(f"No deletion logic defined for table '{table_name}'. Skipping row: {row}")
                return
            
            # Remove From Table
            fissure.utils.library.removeFromTable(conn, table_name, row_id, delete_files, os_version)
            

    def addSupportFiles(self, table_name, row_dict, os_version):
        """
        Adds support files to the FISSURE library and plugin directory.
        """
        # print("Delete table row")
        # print(table_name)
        # print(row_dict)
        # Remove then Add
        if row_dict:
            # Remove from Plugin and Library
            get_filepath = row_dict["filepath"]
            get_new_filepath = row_dict["new_filepath"]
            if row_dict["action"] == "Keep":
                pass
            elif row_dict["action"] == "Replace":
                # Delete Existing Support Files
                plugin_filepath = os.path.join(self.basepath, "install_files", get_filepath)
                library_filepath = os.path.join(fissure.utils.FISSURE_ROOT, get_filepath)
                if os.path.isfile(plugin_filepath):
                    os.system(f'rm "{plugin_filepath}"')
                if os.path.isfile(library_filepath):
                    os.system(f'rm "{library_filepath}"')

            elif row_dict["action"] == "Delete":
                # Delete Existing Support Files
                plugin_filepath = os.path.join(self.basepath, "install_files", get_filepath)
                library_filepath = os.path.join(fissure.utils.FISSURE_ROOT, get_filepath)
                if os.path.isfile(plugin_filepath):
                    os.system(f'rm "{plugin_filepath}"')
                if os.path.isfile(library_filepath):
                    os.system(f'rm "{library_filepath}"')

            # Add to Plugin and Library
            if table_name == "archive_collection":
                pass
            elif table_name == "archive_favorites":
                pass
            elif table_name == "attack_categories":
                pass
            elif table_name == "attacks":
                if get_new_filepath:
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "Single-Stage Flow Graphs", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "Single-Stage Flow Graphs", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
            elif table_name == "conditioner_flow_graphs":
                if get_new_filepath:
                    # Put all conditioner flow graphs in one folder?
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "TSI Flow Graphs", "Conditioner", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "TSI Flow Graphs", "Conditioner", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
            elif table_name == "demodulation_flow_graphs":
                if get_new_filepath:
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "PD Flow Graphs", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "PD Flow Graphs", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
            elif table_name == "detector_flow_graphs":
                if get_new_filepath:
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "TSI Flow Graphs", "Detectors", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "TSI Flow Graphs", "Detectors", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
            elif table_name == "inspection_flow_graphs":
                if get_new_filepath:
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "Inspection Flow Graphs", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "Inspection Flow Graphs", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
            elif table_name == "modulation_types":
                pass
            elif table_name == "packet_types":
                pass
            elif table_name == "protocols":
                pass
            elif table_name == "soi_data":
                pass
            elif table_name == "triggers":
                if get_new_filepath:
                    plugin_filepath = os.path.join(fissure.utils.get_plugin_fg_library_dir(os_version, self.basepath), "Triggers", os.path.basename(get_new_filepath))
                    library_filepath = os.path.join(fissure.utils.get_fg_library_dir(os_version), "Triggers", os.path.basename(get_new_filepath))
                    self.copySupportFiles(get_new_filepath, plugin_filepath, library_filepath)
    

    def copySupportFiles(self, new_filepath, plugin_fileapth, library_filepath):
        """
        Copies files from a local HIPRFISR computer to the plugin folder and FISSURE library.
        """
        os.makedirs(os.path.dirname(plugin_fileapth), exist_ok=True)
        shutil.copy2(new_filepath, plugin_fileapth)
        shutil.copy2(new_filepath, library_filepath)


    ##########################################################################
    # def get_protocols(self):
    #     return list(self.protocols.keys())


    # def add_protocol(self, protocol_name: str, data_rates: float=None, median_packet_lengths: float=None):
    #     if not protocol_name in self.protocols.keys():
    #         # Protocol not in table
    #         with open(os.path.join(self.basepath, 'tables', 'protocols.csv'), 'a', newline='') as f:
    #             writer = csv.writer(f, dialect='unix', quotechar="'", quoting=csv.QUOTE_NONE)
    #             writer.writerow([None, protocol_name, data_rates, median_packet_lengths])
            
    #         # Update class dictionary
    #         self.protocols[protocol_name] = {
    #             "data_rates": data_rates,
    #             "median_packet_lengths": median_packet_lengths,
    #             "mod_types": [],
    #             "pkt_types": []
    #         }
    

    # def edit_protocol(self, protocol_name: str, data_rates: float, median_packet_lengths: float):
    #     if protocol_name in self.protocols.keys():
    #         # Protocol is in the set; perform edit
    #         # Read lines
    #         with open(os.path.join(self.basepath, 'tables', 'protocols.csv'), 'r') as f:
    #             reader = csv.reader(f, dialect='unix', quotechar="'")
    #             lines = list(reader)

    #         # Find line to edit
    #         for (i, line) in enumerate(lines):
    #             if line[1] == protocol_name:
    #                 lines[i][2] = '' if data_rates is None else str(data_rates)
    #                 lines[i][3] = '' if median_packet_lengths is None else str(median_packet_lengths)
    #                 print(line)
    #                 break
                    
    #         # Write lines back to file
    #         with open(os.path.join(self.basepath, 'tables', 'protocols.csv'), 'w', newline='') as f:
    #                 writer = csv.writer(f, dialect='unix', quotechar="'", quoting=csv.QUOTE_NONE)
    #                 writer.writerows(lines)

    #         # Update class dictionary
    #         self.protocols[protocol_name]["data_rates"] = data_rates
    #         self.protocols[protocol_name]["median_packet_lengths"] = median_packet_lengths

    #     else:
    #         self.add_protocol(protocol_name, data_rates, median_packet_lengths)


    # def get_protocol_parameters(self, protocol_name: str):
    #     return self.protocols.get(protocol_name)


    # def add_mod_type(self, protocol_name: str, mod_type: str):
    #     if len(mod_type) > 0:
    #         self.add_protocol(protocol_name) # ensure protocol exists in plugin

    #         if not mod_type in self.protocols.get(protocol_name).get('mod_types'):
    #             self.protocols[protocol_name]['mod_types'].append(mod_type)

    #             # protocol not in table
    #             with open(os.path.join(self.basepath, 'tables', 'modulation_types.csv'), 'a', newline='') as f:
    #                 writer = csv.writer(f, dialect='unix', quotechar="'", quoting=csv.QUOTE_NONE)
    #                 writer.writerow([None, protocol_name, mod_type])


    # def remove_mod_types(self, protocol_name: str, mod_types: List[str]):
    #     for mod_type in mod_types:
    #         # read lines
    #         with open(os.path.join(self.basepath, 'tables', 'modulation_types.csv'), 'r') as f:
    #             reader = csv.reader(f, dialect='unix', quotechar="'")
    #             lines = list(reader)

    #         print(lines)

    #         # find and remove line
    #         #line_idx = None
    #         for (i, line) in enumerate(lines):
    #             if line[2] == mod_type:
    #                 #print(i)
    #                 #print(line)
    #                 #line_idx = i
    #                 lines = lines[:i] + lines[i+1:]
    #                 break

    #         # write lines back to file
    #         with open(os.path.join(self.basepath, 'tables', 'modulation_types.csv'), 'w', newline='') as f:
    #                 writer = csv.writer(f, dialect='unix', quotechar="'", quoting=csv.QUOTE_NONE)
    #                 writer.writerows(lines)

    #         # remove from protocol dict
    #         self.protocols[protocol_name]['mod_types'].remove(mod_type)


    # def edit_pkt_types(self, protocol_name: str, pkt_types: List[List[str]]):
    #     # Rewrite packet types table with pkt_types
    #     self.protocols[protocol_name]['pkt_types'] = pkt_types
    #     with open(os.path.join(self.basepath, 'tables', 'packet_types.csv'), 'w', newline='') as f:
    #         writer = csv.writer(f, dialect='unix', quotechar="'", quoting=csv.QUOTE_MINIMAL)
    #         for pkt_type in pkt_types:
    #             line = [None, protocol_name] + pkt_type
    #             #print(['', protocol_name] + pkt_type)
    #             print('\nLINE: ' + str(line) + '\n')
    #             for entry in line:
    #                 print(entry)
    #             writer.writerow(line)


if __name__ == '__main__':
    pass
    # print(plugin_exists('test_plugin'))
    # print(plugin_exists('test'))
    # #create_plugin('test')
    # editor = PluginEditor('uitest')
    # '''editor.add_protocol('test2')
    # editor.add_protocol('test3', 42, 712.2)
    # editor.edit_protocol('test2', 75.1)
    # editor.edit_protocol('test3', None, 712.2)'''
    # #editor.edit_pkt_types('uitest2', [['', 'uitest2', 'uitest Plugin Packet!', '{"Port": null, "Filename": null}', '{"bb": {"Is CRC": true, "Length": 8, "CRC Range": "1-1", "Sort Order": 2, "Default Value": "00000000"}, "aaa": {"Is CRC": false, "Length": 8, "Sort Order": 1, "Default Value": "11111111"}}', " '1'"]])
    # editor.edit_pkt_types('uitest2', [['uitest Plugin Packet!', '{"Port": null, "Filename": null}', '{"bb": {"Is CRC": True, "Length": 8, "CRC Range": "1-1", "Sort Order": 2, "Default Value": "00000000"}, "aaa": {"Is CRC": False, "Length": 8, "Sort Order": 1, "Default Value": "11111111"}}', '1']])