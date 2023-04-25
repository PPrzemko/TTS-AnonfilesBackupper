import os
import sqlite3
import json
from dotenv import load_dotenv
import time
import csv
from requests_toolbelt import MultipartEncoder, MultipartEncoderMonitor
import requests
from tqdm import tqdm
import logging

logging.basicConfig(filename='TTS-AnonfilesBackupper.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')


class FileInfo:
    def __init__(self, path, name, size):
        self.name = name
        self.filesize = size
        self.workshop_id = self.get_workshop_id(self.name)

    def get_workshop_id(self, filename):
        id = 0
        start = filename.rfind('(')
        end = filename.rfind(')')
        if start != -1 and end != -1 and end > start:
            tmpid = filename[start + 1: end]
            id = int(tmpid)
        return id


def get_files_in_directory():
    files = []
    for entry in os.scandir(os.getenv('MOD_PATH')):
        if entry.is_file():
            file_name = entry.name
            file_path = os.path.join(entry.path, file_name)
            file_size = os.path.getsize(entry) / 1000000.0
            if file_name.endswith('.ttsmod'):
                files.append(FileInfo(file_path, file_name, file_size))
    return files


def create_database():
    # Connect to the database
    conn = sqlite3.connect('data.db')
    if conn:
        print("Database connection successful")
    else:
        print("Connection could not be established (big trouble)\n")
        return
    cursor = conn.cursor()
    # Define the table to check for
    table_name = 'files'
    # Execute a query to check if the table exists
    query = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    cursor.execute(query)

    # Check if the table exists in the database
    if cursor.fetchone():
        print('Use existing database')
    else:
        print('Table creation...')
        cursor.execute('''
                CREATE TABLE "files" (
                "name"	TEXT,
                "filesize"	TEXT,
                "workshopid"	TEXT,
                "anon_fileid"	TEXT,
                "anon_link"	TEXT,
                "anon_success"	TEXT DEFAULT 0,
                "anon_lastSeen"	TEXT,
                UNIQUE("anon_fileid"),
                UNIQUE("workshopid"),
                PRIMARY KEY("workshopid")
                )''')

    # Close and commit the database connection
    conn.commit()
    conn.close()


def update_database(files):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    alreadyInDb = 0
    newlyAdded = 0

    for file in files:
        workshopid = (file.workshop_id,)
        # Check if the dataset is already in the database
        select_query = "SELECT * FROM files WHERE workshopid=?"
        cursor.execute(select_query, workshopid)

        if cursor.fetchone() is None:
            # If the dataset is not in the database, insert it
            my_data = (file.name, file.filesize, file.workshop_id,)
            insert_query = 'INSERT INTO files (name, filesize, workshopid) VALUES (?, ?, ?)'
            cursor.execute(insert_query, my_data)
            conn.commit()
            newlyAdded = newlyAdded + 1
        else:
            # If the dataset is already in the database, do nothing
            # TODO: maybe implement version controll via filesize or hash
            alreadyInDb = alreadyInDb + 1

    print("Added " + str(newlyAdded) + " new Datasets")
    print("Found " + str(alreadyInDb) + " old Datasets")
    cursor.close()
    conn.close()


def upload_files(files):
    get_files_in_directory()

    try:
        for file in files:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            workshopid = (file.workshop_id,)
            # Check if the dataset is already in the database
            select_query = "SELECT * FROM files WHERE workshopid=?"
            cursor.execute(select_query, workshopid)

            filedata = cursor.fetchone()
            if filedata is None:
                print("Error file is not in dataset")
            else:
                file_success = filedata[5]
                # print(f"File {file_name} with ID {file_workshopid} and size {file_size} is already in the dataset")
                if file_success == '0':
                    fileid, fullurl = upload_file(file)
                    querydata = (fileid, fullurl, int(time.time()), file.workshop_id)
                    select_query = "UPDATE files SET anon_fileid = ?, anon_link= ?, anon_success = 1, anon_lastSeen=? WHERE workshopid = ?;"
                    cursor.execute(select_query, querydata)
            cursor.close()
            conn.commit()
            conn.close()
    except KeyboardInterrupt:
        print("\033[91m" + "\n \n Upload stopped by user.\n" + "\033[0m")


def upload_file(file):
    # TODO: Maybe add Progressbar
    load_dotenv()
    url = "https://api.anonfiles.com/upload?token=" + os.getenv('API_KEY')
    filename = os.getenv('MOD_PATH') + os.path.sep + file.name

    with open(filename, "rb") as f:
        encoder = MultipartEncoder({"file": (file.name, f)})
        progress_bar = tqdm(total=encoder.len, unit="B", unit_scale=True)
        monitor = MultipartEncoderMonitor(encoder,
                                          lambda monitor: progress_bar.update(monitor.bytes_read - progress_bar.n))
        headers = {"Content-Type": monitor.content_type}
        response = requests.post(url, data=monitor, headers=headers)
        if response.ok:
            progress_bar.close()
            # parse JSON response
            data = json.loads(response.content)
            # check if status is true
            if data['status']:
                print('\033[92m' + file.name + ' uploaded successfully' + '\033[0m')
                file_id = data['data']['file']['metadata']['id']
                full_url = data['data']['file']['url']['full']
                if os.getenv('COMMUNITY_CONTRIBUTION') == 'true':
                    community_contribution(file.workshop_id, file.name, full_url)

                return file_id, full_url
            else:
                print('Upload failed. ' + data['error']['message'])
        else:
            print('Error uploading file')


def community_contribution(workshopid, name, anon_link):
    form_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSfSh9WY6dzxueZ5yXSCXdzWNvm9gHosvhM6li-XBIUiAWPX4Q/formResponse"
    form_data = {
        f"entry.326097042": f"{workshopid}",
        f"entry.2142133025": f"{name}",
        f"entry.1514890636": f"{anon_link}",
    }
    # Send the POST request to submit the form
    response = requests.post(form_url, data=form_data)
    # TODO: Remove debug
    # print(response.status_code)
    # print(response.text)
    if response.status_code == 200:
        print(name + " has been added to community list. Thank you!")
    else:
        print(name + " submission failed. :(")


def verify_uploads():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    select_query = "SELECT anon_fileid, name, workshopid FROM files WHERE anon_fileid IS NOT NULL;"
    cursor.execute(select_query)
    successful = 0
    failed = 0

    for row in cursor.fetchall():
        anon_fileid = row[0]
        filename = row[1]
        workshopid = row[2]
        api_url = f"https://api.anonfiles.com/v2/file/{anon_fileid}/info"
        response = requests.get(api_url)
        if response.ok:
            response_json = json.loads(response.content)
            status = response_json['status']
            if status is False:
                # update anon_success to 0
                print('\033[31mError getting file status\033[0m' + filename)
                querydata = (workshopid,)
                select_query = "UPDATE files SET anon_success = 0 WHERE workshopid = ?;"
                cursor.execute(select_query, querydata)
                failed = failed + 1
            elif status is True:
                # update anon_success and last seen
                querydata = (int(time.time()), workshopid)
                select_query = "UPDATE files SET anon_success = 1, anon_lastSeen=? WHERE workshopid = ?;"
                cursor.execute(select_query, querydata)
                successful = successful + 1

        else:
            print('\033[31mError:', response.status_code, filename, '\033[0m' + '. Will be uploaded again next time')
            # update anon_success to 0
            querydata = (workshopid,)
            select_query = "UPDATE files SET anon_success = 0 WHERE workshopid = ?;"
            cursor.execute(select_query, querydata)
            failed = failed + 1
    print("\n")
    print('\033[31m' + str(failed) + ' links are broken and will be reuploaded next time.' + '\033[0m')
    print('\033[32m' + str(successful) + ' links have been successfully checked.' + '\033[0m')

    cursor.close()
    conn.commit()
    conn.close()


def export_csv():
    with open('export.csv', 'w+', newline='') as write_file:
        writer = csv.writer(write_file)
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # create a cursor object (which lets you address the table results individually)
        for row in cursor.execute('SELECT * FROM files'):
            # use the cursor as an iterable
            writer.writerow(row)
        conn.close()
    print("Exported to export.csv\n/")


def check_config():
    # Check if the .config file exists
    if not os.path.exists('.config'):
        default_env = {
            'API_KEY': '',
            'MOD_PATH': '.',
            'COMMUNITY_CONTRIBUTION': 'false'
        }
        with open('.config', 'w') as f:
            for key, value in default_env.items():
                f.write(f"{key}={value}\n")


if __name__ == '__main__':
    check_config()
    load_dotenv('.config')
    print('Using path ->  ' + os.getenv('MOD_PATH'))
    create_database()
    files = get_files_in_directory()
    update_database(files)

    menu = '4'
    while menu != '0':
        menu = input("0 - exit \n"
                     "1 - upload newly added files \n"
                     "2 - verify if the uploaded files are still available \n"
                     "3 - export to csv \n"
                     )
        if menu == '1':
            upload_files(files)
        elif menu == '2':
            verify_uploads()
        elif menu == '3':
            export_csv()
