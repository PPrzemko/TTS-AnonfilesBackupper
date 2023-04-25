# Tabletop Simulator Mod Uploader (Currently Windows10/11 only)
## Introduction
This program is a Python script to upload mods for the game Tabletop Simulator to the website [AnonFiles](https://anonfiles.com/).  
It "automatically" scans a directory for mods and uploads any new ones to AnonFiles.
The script creates and updates a sqllite database containing information about the uploaded mods, including their name, filesize, workshopid, anonid, and anonlink.
It also has the ability to validate all links in the database and mark any that are invalid. 
Additionally, there is a community contribution feature where all links are sent to a Google form, which is linked to a spreadsheet [spreadsheet](https://docs.google.com/spreadsheets/d/13npagZxitdzyb-YC1w-ZdjYuAh8aDzXhrjZBE0-zKFo/edit?usp=sharing)

## Installation 
### From Release - Windows10/11 only
1. Download the latest version of the TTS-Anonfiles Backupper.
2. Run the "TTS-AnonfilesBackupper.exe" file to launch the program.
3. Open the ".config" file using a text editor like Notepad.
4. Locate the section for "API_KEY" and enter your API key, which you can obtain from the [AnonFiles](https://anonfiles.com/docs/api) website after creating an account.
5. Optionally, you can modify the "path" and "community contribution" settings in the configuration file.

## Usage

0. - exit 
1. - upload newly added files 
2. - verify if the uploaded files are still available 
3. - export to csv 
4. - enter setup config

[TTS Mod Backup](https://www.nexusmods.com/tabletopsimulator/mods/263)

## Contributing
Contributions to this project are welcome! To contribute, please submit a pull request.
Please be gentle this is my first Python project.

## License
This project is licensed under the GNU GENERAL PUBLIC LICENSE. See the LICENSE file for more information.