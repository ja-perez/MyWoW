import json
import datetime
from os import path, getcwd, listdir

def get_files_by_extension(folder_path, extension):
    return [path.join(folder_path, file) for file in listdir(folder_path) if file.endswith(extension)]

def get_path_from_cwd(*args):
    return path.join(getcwd(), *args)

def get_path_from_log_dir(*args):
    return path.join(getcwd(), "logs", *args)

def write_data_to_file(file_path: str, data: dict) -> None:
    print("Writing data to file path: " + file_path)
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Failed to write data to file: " + file_path)
        print("Error:\n", e)
        return
    print("Successfully wrote data to file: " + file_path)

def append_data_to_file(file_path: str, data: dict) -> None:
    print("Adding data to file path: " + file_path)
    try:
        existing_data = {}
        if path.exists(file_path):
            with open(file_path, "r") as f:
                existing_data = json.load(f)
                existing_data.update(data)
        with open(file_path, "w") as f:
            json.dump(existing_data, f, indent=4)
    except Exception as e:
        print("Failed to add data to file: " + file_path)
        print("Error:\n", e)
        return
    print("Successfully added data to file: " + file_path)

def get_data_from_file(file_path: str) -> dict:
    print("Reading data from file path: " + file_path)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print("Failed to read data from file: " + file_path)
        print("Error:\n", e)
        return

def unix_to_date_string(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

def unix_to_datetime_string(timestamp: int) -> str:
    return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def get_weekday(date: datetime.datetime) -> str:
    match date.weekday():
        case 0:
            return "Monday"
        case 1:
            return "Tuesday"
        case 2:
            return "Wednesday"
        case 3:
            return "Thursday"
        case 4:
            return "Friday"
        case 5:
            return "Saturday"
        case 6:
            return "Sunday"
        case _:
            return "Invalid Date"