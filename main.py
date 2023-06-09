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
from file import FileInfo

logging.basicConfig(filename='TTS-AnonfilesBackupper.log', level=logging.WARNING,
                    format='%(asctime)s:%(levelname)s:%(message)s', filemode='a')


def get_files_in_directory():
    files = []
    mod_path = os.getenv('MOD_PATH')
    total_files = sum(1 for entry in os.scandir(mod_path) if entry.is_file() and entry.name.endswith('.ttsmod'))
    for entry in tqdm(os.scandir(mod_path), total=total_files, desc="Processing files"):
        if entry.is_file() and entry.name.endswith('.ttsmod'):
            file_size = entry.stat().st_size / 1000000.0
            file_info = FileInfo(entry.path, entry.name, file_size)
            # Filecount -1 means zip can not be opened. So probably corrupted
            if file_info.filecount != -1:
                files.append(file_info)
    return files


def create_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('data.db')
        if conn:
            print("Database connection successful")
        else:
            print("Connection could not be established (big trouble)\n")
            logging.error("Connection could not be established (big trouble)")
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
                        "filecount"    TEXT DEFAULT 0,
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
    except Exception as e:
        print("An error occurred:", str(e))
        logging.info("Error: Unable to open the zip file. " + '"' + e + '"')


def update_database(givenfiles):
    print("Updating Database... \n")
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    alreadyInDb = 0
    updateFound = 0
    newlyAdded = 0

    select_query = "SELECT filecount FROM files WHERE workshopid = ?"
    insert_query = "INSERT INTO files (name, filesize, workshopid, filecount) VALUES (?, ?, ?, ?)"
    update_query = "UPDATE files SET anon_success = 0, filecount = ?, filesize = ? WHERE workshopid = ?"

    for file in givenfiles:
        workshopid = (file.workshop_id,)
        cursor.execute(select_query, workshopid)
        rows = cursor.fetchone()

        if rows is None:
            my_data = (file.name, file.filesize, file.workshop_id, file.filecount)
            cursor.execute(insert_query, my_data)
            newlyAdded += 1
        else:
            dbfilecount = int(rows[0])

            if dbfilecount == file.filecount:
                alreadyInDb += 1
            elif dbfilecount < file.filecount:
                updateFound += 1
                querydata2 = (file.filecount, file.filesize, file.workshop_id)
                cursor.execute(update_query, querydata2)
            elif dbfilecount > file.filecount:
                print(file.name + "Info: File has fewer files than recorded file count in Database. Ignoring...")
                logging.info('File has fewer files than recorded file count in Database. "{}"'.format(file.name))
            else:
                print("File count could not be checked.")

    print("\nAdded {} new Datasets".format(newlyAdded))
    print("Updated {} old Datasets".format(updateFound))
    print("Found {} old Datasets".format(alreadyInDb))

    conn.commit()
    cursor.close()
    conn.close()


def upload_files(givenfiles):
    try:
        for file in givenfiles:
            conn = sqlite3.connect('data.db')
            cursor = conn.cursor()
            workshopid = (file.workshop_id,)
            # Check if the dataset is already in the database
            select_query = "SELECT anon_success FROM files WHERE workshopid=?"
            cursor.execute(select_query, workshopid)

            filedata = cursor.fetchone()
            if filedata is None:
                print(file.name + "is not in found in Database.")
                logging.warning(file.name + "is not in found in Database.")
            else:
                file_success = filedata[0]
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
    load_dotenv()
    url = "https://api.anonfiles.com/upload?token=" + os.getenv('API_KEY')
    filepath = os.getenv('MOD_PATH') + os.path.sep + file.name
    print("<----Uploading: " + file.name + "---->")
    with open(filepath, "rb") as f:
        encoder = MultipartEncoder({"file": (file.name, f)})
        progress_bar = tqdm(total=encoder.len, unit="B", unit_scale=True)
        monitor2 = MultipartEncoderMonitor(encoder,
                                           lambda monitor2: progress_bar.update(monitor2.bytes_read - progress_bar.n))
        headers = {"Content-Type": monitor2.content_type}
        response = requests.post(url, data=monitor2, headers=headers)
        if response.ok:
            progress_bar.close()
            # parse JSON response
            data = json.loads(response.content)
            # check if status is true
            if data['status']:
                print('\033[92m' + 'Uploaded successfully' + '\033[0m')
                file_id = data['data']['file']['metadata']['id']
                full_url = data['data']['file']['url']['full']
                if os.getenv('COMMUNITY_CONTRIBUTION') == 'true':
                    community_contribution(file.filecount, file.workshop_id, file.name, full_url)

                return file_id, full_url
            else:
                print('Upload failed. ' + data['error']['message'])
                logging.warning('Upload failed. ' + data['error']['message'])
        else:
            print('Error uploading file')
            logging.warning(
                'Upload failed. Response was not Ok.' + file.name + str(response.status_code) + response.text)


def community_contribution(filecount, workshopid, name, anon_link):
    form_url = "https://docs.google.com/forms/u/0/d/e/1FAIpQLSfSh9WY6dzxueZ5yXSCXdzWNvm9gHosvhM6li-XBIUiAWPX4Q/formResponse"
    form_data = {
        f"entry.1845967574": f"{filecount}",
        f"entry.326097042": f"{workshopid}",
        f"entry.2142133025": f"{name}",
        f"entry.1514890636": f"{anon_link}",
    }
    # Send the POST request to submit the form
    response = requests.post(form_url, data=form_data)
    if response.status_code == 200:
        print("Has been added to community list. Thank you!")
    else:
        print("Submission failed. :(")
        logging.warning('Community Submission failed.' + str(response.status_code) + response.text)


def verify_uploads():
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        select_query = "SELECT anon_fileid, name, workshopid FROM files WHERE anon_fileid IS NOT NULL;"
        cursor.execute(select_query)
        successful = 0
        failed = 0

        update_query_failed = "UPDATE files SET anon_success = 0 WHERE workshopid = ?;"
        update_query_success = "UPDATE files SET anon_success = 1, anon_lastSeen = ? WHERE workshopid = ?;"

        for row in tqdm(cursor.fetchall(), desc="Verifying uploads"):
            anon_fileid, filename, workshopid = row[:3]
            api_url = f"https://api.anonfiles.com/v2/file/{anon_fileid}/info"
            response = requests.get(api_url)

            if response.ok:
                response_json = response.json()
                status = response_json['status']
                if not status:
                    print('\033[31mError getting file status\033[0m', filename)
                    logging.warning('Error getting file status {} {}'.format(response.status_code, response.text))
                    cursor.execute(update_query_failed, (workshopid,))
                    failed += 1
                else:
                    cursor.execute(update_query_success, (int(time.time()), workshopid))
                    successful += 1
            else:
                print('\033[31mError:', response.status_code, filename, '\033[0m' + '. Will be uploaded again next time')
                cursor.execute(update_query_failed, (workshopid,))
                failed += 1

            conn.commit()

        print("\n")
        print('\033[31m{} links are broken and will be reuploaded next time.\033[0m'.format(failed))
        print('\033[32m{} links have been successfully checked.\033[0m'.format(successful))

        conn.commit()
        cursor.close()
        conn.close()
    except KeyboardInterrupt:
        print("\033[91m" + "\n \n Verifying stopped by user.\n" + "\033[0m")

def export_csv():
    with open('export.csv', 'w+', newline='', encoding="utf-8") as write_file:
        writer = csv.writer(write_file, quoting=csv.QUOTE_ALL)
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
        setup_conf()


def setup_conf():
    default_env = {
        'API_KEY': input("Please enter the API key for Anonfiles: "),
        'MOD_PATH': '.',
        'COMMUNITY_CONTRIBUTION': input(
            "Would you like to save your entries in the community spreadsheet? Please answer with \"true\" or \"false\".")
    }
    with open('.config', 'w') as f:
        for key, value in default_env.items():
            f.write(f"{key}={value}\n")


def main():
    check_config()
    load_dotenv('.config')
    print('Using path ->  ' + os.getenv('MOD_PATH'))
    create_database()
    files = get_files_in_directory()
    update_database(files)

    menu = '69'
    while menu != '0':
        menu = input("0 - exit \n"
                     "1 - upload newly added files \n"
                     "2 - verify if the uploaded files are still available \n"
                     "3 - reprocess local files \n"
                     "4 - export to csv \n"
                     "5 - enter setup \n"
                     )
        if menu == '1':
            upload_files(files)
        elif menu == '2':
            print("This can take a while...")
            time.sleep(0.1)
            verify_uploads()
        elif menu == '3':
            files = get_files_in_directory()
            update_database(files)
        elif menu == '4':
            export_csv()
        elif menu == '5':
            setup_conf()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.exception("main crashed. Error: %s", e)
