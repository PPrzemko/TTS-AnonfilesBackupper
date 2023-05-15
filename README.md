# Tabletop Simulator Mod Uploader
## Introduction
This program is a Python script to upload mods for the game Tabletop Simulator which are created from [TTS Mod Backup](https://www.nexusmods.com/tabletopsimulator/mods/263) to the website [AnonFiles](https://anonfiles.com/).  
It "automatically" scans a directory for mods and uploads any new ones to AnonFiles.
The script creates and updates a sqllite database containing information about the uploaded mods, including their name, filesize, workshopid, anonid, and anonlink.
It also has the ability to validate all links in the database and mark any that are invalid. 
Additionally, there is a community contribution feature where all links are sent to a Google form, which is linked to a [spreadsheet](https://docs.google.com/spreadsheets/d/13npagZxitdzyb-YC1w-ZdjYuAh8aDzXhrjZBE0-zKFo/edit?usp=sharing)

## Installation 
### From Release - Windows10/11 only
1. Download the latest version of the TTS-Anonfiles Backupper.
2. Run the "TTS-AnonfilesBackupper.exe" file to launch the program.
3. Enter your API key, which you can obtain from the [AnonFiles](https://anonfiles.com/docs/api) website after creating an account.
4. Choose if you want to contribute your uploads. (true,false)
5. Optionally, you can modify the "api-key", "path" and "community contribution" settings in the configuration (.config) file.

### Linux (Tested on Ubuntu 22.04.2 LTS)
Make sure to have python installed (Tested with Python 3.10.6)
- Manually download the required files.
- or with git
```bash
git clone https://github.com/PPrzemko/TTS-AnonfilesBackupper.git
```
Install requirements
```bash
pip install -r requirements.txt
```
Run programm
```bash
python3 main.py 
```

## Usage

0. - exit 
1. - upload newly added files 
2. - verify if the uploaded files are still available 
3. - reprocess local files
4. - export to csv 
5. - enter setup config



## Contributing
Contributions to this project are welcome! To contribute, please submit a pull request.
Please be gentle this is my first Python project.

## License
This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more information.
