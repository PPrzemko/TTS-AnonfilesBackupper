import os
import sqlite3
import json
import requests
from dotenv import load_dotenv

class FileInfo:
    def __init__(self, path, name, size):
        self.path = path
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
    for entry in os.scandir('./'):
        if entry.is_file():
            file_name = entry.name
            file_path = os.path.join(entry.path, file_name)
            file_size = os.path.getsize(entry) / 1000000.0
            if file_name.endswith('.ttsmod'):
                files.append(FileInfo(file_path, file_name, file_size))
    return files



def compare_to_database():
    db_path = './data.db'
    conn = sqlite3.connect(db_path)
    c = conn.cursor()



    # Insert data
    #c.execute("INSERT INTO files (name, path, filesize, workshopid) VALUES (?, ?, ?, ?)",
    #          ('test', 'John', 30, 54353453))

    for file in files:
        # Define the dataset to search for
        dataset = (file.workshop_id,)

        # Execute a SELECT query on the table that contains the dataset
        query = 'SELECT * FROM files WHERE workshopid = ?'
        c.execute(query, dataset)
        if c.fetchone():
            print('Dataset exists in database')
        else:
            print('Dataset does not exist in database')





    # Commit changes
    conn.commit()
    conn.close()


def curl_test():
    load_dotenv()
    url = "https://api.anonfiles.com/upload?token=" + os.getenv('API_KEY')
    filename = "Lotti Karotti (German) (1152125980).ttsmod"

    with open(filename, "rb") as f:
        response = requests.post(url, files={"file": f})
        response_json = json.loads(response.text)
        print(response_json)
        if response.ok:
            # parse JSON response
            data = json.loads(response.content)

            # check if status is true
            if data['status']:
                print('Upload successful')
                full_url = data['data']['file']['url']['full']
                file_id = data['data']['file']['metadata']['id']

                print("Full URL:", full_url)
                print("File ID:", file_id)

            else:
                print('Upload failed')
        else:
            print('Error uploading file')


def create_database():
    # Connect to the database
    conn = sqlite3.connect('data.db')
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
                "path"	TEXT,
                "filesize"	TEXT,
                "workshopid"	TEXT,
                "anon_fileid"	TEXT,
                "anon_link" TEXT,
                "anon_success"	TEXT,
                "anon_lastChecked"	TEXT,
                UNIQUE("workshopid"),
                PRIMARY KEY("workshopid"),
                UNIQUE("anon_fileid")
                     )''')

    # Close the database connection
    conn.close()


if __name__ == '__main__':
    create_database()
    files = get_files_in_directory()
    compare_to_database()
    for file in files:
        print(file.name)
        print(file.path)
        print(file.filesize)
        print(file.workshop_id)
        print()

    curl_test()
    input("Press any key to exit...")
