import logging
import zipfile

logging.basicConfig(filename='TTS-AnonfilesBackupper.log', level=logging.WARNING,
                    format='%(asctime)s:%(levelname)s:%(message)s', filemode='a')
class FileInfo:
    def __init__(self, path, name, size):
        self.name = name
        self.filesize = size
        self.filepath = path
        self.workshop_id = self.get_workshop_id(self.name)
        self.filecount = self.get_file_count_of_zip(self.filepath)

    def get_workshop_id(self, filename):
        id = 0
        start = filename.rfind('(')
        end = filename.rfind(')')
        if start != -1 and end != -1 and end > start:
            tmpid = filename[start + 1: end]
            id = int(tmpid)
        return id

    def get_file_count_of_zip(self, filepath):
        try:
            with zipfile.ZipFile(filepath, 'r') as myzip:
                # Get the list of all files and directories in the zip file
                file_list = myzip.namelist()
                # Count the number of files (excluding directories)
                file_count = len([f for f in file_list if not myzip.getinfo(f).is_dir()])
            return file_count
        except zipfile.BadZipFile:
            print("Error: Unable to open the zip file. " + '"' + self.name + '"')
            logging.info("Error: Unable to open the zip file. " + '"' + self.name + '"')
            return -1








