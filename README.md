# D118-OldLoginInfo

Scripts to generate info for the "old login" fields for staff and students within PowerSchool, which is needed for SSO logins to work properly.

## Overview

First, an explanation of why this script is needed to allow SSO to work: When the SSO information is entered for the first time into the "Identity Provider Global ID" field either on a students *Access Accounts* page or a staff member's *Security Settings* page, it attempts to make an entry in the [PCAS_ExternalAccountMap](https://ps.powerschool-docs.com/pssis-data-dictionary/latest/pcas_externalaccountmap-ver10-1-0) table with the email and relevant information. However, one of the fields, *PCAS_AccountToken*, needs to match the *AccountIdentifier* field from the [AccessStudent](https://ps.powerschool-docs.com/pssis-data-dictionary/latest/accessstudent-ver7-0-0), [AccessTeacher](https://ps.powerschool-docs.com/pssis-data-dictionary/latest/accessteacher-ver7-0-0) or [AccessAdmin](https://ps.powerschool-docs.com/pssis-data-dictionary/latest/accessadmin-ver7-0-0). But in our experience, the entry in the relevant "Access" table is not automatically created when the SSO information is input, it is seemingly only made when the "old" login fields for staff or students are populated. This needs to be done via AutoComm, since they get hidden once SSO is enabled. These login fields are *Student_Web_ID* and *Student_Web_Password* for students, *TeacherLoginID* and *TeacherLoginPW* for PowerSchool Teacher, and *LoginID* and *Password* for PowerSchool Admin. So a new staff member or student needs to have these fields populated, though it doesn't really matter with what (as long as the usernames are unique per user) since users will not actually use this information to log in at all. These scripts generate the .txt files that can be used to AutoComm to do this process.

For the staff script, we define two lists: one of the school names/abbreviations and the other is the school IDs (in the same order of the names). We go through each school one at a time, generating a unique text file with the name/abbreviation of the school, and only includes staff who have that building as their homeschool, so that when they are AutoComm imported, they do not create a new instance of that staff member in buildings they aren't actually in. The staff members in the building are queried, iterated through, and any staff who do not currently have the old login fields populated are given a username based on their email (stripping out after the @), and limited to 20 characters as that is the max length PowerSchool accepts. They are also given a generic password, and that information is exported to the school file. If a staff member already has the logins, there is nothing output to the file so that its size can stay small and the imports finish quickly. Once all staff in that building are processed, the school file is uploaded via SFTP to a folder with the same name as the school, and the next building is started.
For the student script, all students can be combined into one file and AutoComm imported from the District Office view, so the script is much simpler. All students are queried, iterated through, and if they do not currently have a login, they are given their email as both and exported to the student file, which is then uploaded to the SFTP server once all students are processed.

## Requirements

The following Environment Variables must be set on the machine running the script:

- POWERSCHOOL_READ_USER
- POWERSCHOOL_DB_PASSWORD
- POWERSCHOOL_PROD_DB
- D118_SFTP_USERNAME
- D118_SFTP_PASSWORD
- D118_SFTP_ADDRESS
- D118_TEMP_PASSWORD

These are fairly self explanatory, and just relate to the usernames, passwords, and host IP/URLs for PowerSchool and the local SFTP server. Additionally, the temp password is used for the staff logins. If you wish to directly edit the script and include these credentials or to use other environment variable names, you can.

You must also populate the list of school names/abbreviations and school numbers, by editing the `schoolList = [...]` and `schoolNumbers = [...]` lists. The schoolList is the names that will be used for the file name prefixes and the SFTP directory, while the schoolNumbers list is the matching schoolcodes (found in PowerSchool) for each name, and is used to do the actual SQL query.

Additionally, the following Python libraries must be installed on the host machine (links to the installation guide):

- [Python-oracledb](https://python-oracledb.readthedocs.io/en/latest/user_guide/installation.html)
- [pysftp](https://pypi.org/project/pysftp/)

**As part of the pysftp connection to the output SFTP server, you must include the server host key in a file** with no extension named "known_hosts" in the same directory as the Python script. You can see [here](https://pysftp.readthedocs.io/en/release_0.2.9/cookbook.html#pysftp-cnopts) for details on how it is used, but the easiest way to include this I have found is to create an SSH connection from a linux machine using the login info and then find the key (the newest entry should be on the bottom) in ~/.ssh/known_hosts and copy and paste that into a new file named "known_hosts" in the script directory.

You will also need a SFTP server running and accessible that is able to have files written to it in the directory /sftp/oldLogins/ or you will need to customize the script (see below). You also need subdirectories for each school name, as well as one labeled Students (/sftp/oldLogins/Students). That setup is a bit out of the scope of this readme.
In order to import the information into PowerSchool, scheduled AutoComm jobs should be setup, that uses the managed connection to your SFTP server, and imports into the login fields using tab as a field delimiter, LF as the record delimiter with the UTF-8 character set.

## Customization

Assuming you have everything set up in the requirements section, the script should pretty much just work. However, there are a few things you could customize:

- `OUTPUT_FILE_NAME` and `OUTPUT_FILE_DIRECTORY`define the file name and directory on the SFTP server that the student file will be exported to. These combined will make up the path for the AutoComm import. Similarly, `OUTPUT_FILE_NAME_SUFFIX` is the suffix for the staff school files, and the school name is the prefix.
  - If you want to change how this filename is constructed for the staff schools, edit the `filename = school + OUTPUT_FILE_NAME_SUFFIX` line.
- You will need to edit the `EMAIL_SUFFIX` constant in the student script to match whatever your emails are. Additionally, you may need to change how the email is constructed, as we use their student number. If you need to, you can change the `email = idNum + EMAIL_SUFFIX`.
- If you want to edit what the usernames are for staff, change the `login = email.split('@')[0]` and `login = login[0:20]` lines, as this currently gets the first 20 characters of the part of the email before the @ symbol.
  - For students, you will need to edit the output line `print(f'{idNum}\t{email}\t{email}', file=output)` to have a different field besides email.
