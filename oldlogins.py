# Script to generate the "old login info" for teachers in PS
# Fills in the login info, and teacher login info which is needed for them
# to get a PCAS account created, needed for other scripts to populate the Global ID field for SSO.
# Generates a separate file for each building which will then be autocomm'd into PS so it does not make duplicates of teachers
# Writing the values directly to the database also does not seem to make the PCAS account but autocomm does

# importing module
import datetime
import os  # needed for environement variable reading
from datetime import *

import oracledb  # needed for connection to PowerSchool server (ordcle database)
import pysftp  # needed for sftp file upload

DB_UN = os.environ.get('POWERSCHOOL_READ_USER')  # username for read-only database user
DB_PW = os.environ.get('POWERSCHOOL_DB_PASSWORD')  # the password for the database account
DB_CS = os.environ.get('POWERSCHOOL_PROD_DB')  # the IP address, port, and database name to connect to

#set up sftp login info
SFTP_UN = os.environ.get('D118_SFTP_USERNAME')  # username for the d118 sftp server
SFTP_PW = os.environ.get('D118_SFTP_PASSWORD')  # password for the d118 sftp server
SFTP_HOST = os.environ.get('D118_SFTP_ADDRESS')  # ip address/URL for the d118 sftp server
CNOPTS = pysftp.CnOpts(knownhosts='known_hosts')  # connection options to use the known_hosts file for key validation

OUTPUT_FILE_NAME_SUFFIX = '-Old-Logins.txt'
OUTPUT_FILE_DIRECTORY = '/sftp/oldLogins/'

password = os.environ.get('D118_TEMP_PASSWORD')  # just a generic password since it is not actually used to login, just to populate the fields

print(f"Database Username: {DB_UN} |Password: {DB_PW} |Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
print(f'SFTP Username: {SFTP_UN} | D118 SFTP Password: {SFTP_PW} | D118 SFTP Server: {SFTP_HOST}')  # debug so we can see what info sftp connection is using

schoolList = ['WHS', 'WMS', 'MMS', 'WGS', 'RCS', 'CCS', 'Onboarding', 'SSO', 'Transportation', 'Technology', 'Central Office', 'Curriculum', 'Superintendent', 'Sub', 'Maintenance', 'SEDOL', 'District Office']
schoolNumbers = ['5', '1003', '1004', '2001', '2005', '2007', '2', '133', '300', '134', '135', '131', '136', '500', '132', '183', '0']

if __name__ == '__main__':  # main file execution
    with open('staff_login_log.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:  # create the connecton to the database
            with con.cursor() as cur:  # start an entry cursor
                print(f'INFO: Connection established to PS database on version: {con.version}')
                print(f'INFO: Connection established to PS database on version: {con.version}', file=log)
                with pysftp.Connection(SFTP_HOST, username=SFTP_UN, password=SFTP_PW, cnopts=CNOPTS) as sftp:
                    print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established')
                    print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established', file=log)
                    # print(sftp.pwd)  # debug, show what folder we connected to
                    # print(sftp.listdir())  # debug, show what other files/folders are in the current directory
                    for index, school in enumerate(schoolList):  # go through each school in the list one at a time, allows us to search for only that building and output to individual files
                        #print(str(index) + ': ' + school + '|' + schoolNumbers[index])
                        filename = school + OUTPUT_FILE_NAME_SUFFIX  # make a unique filename for each output file
                        schoolcode = schoolNumbers[index]  # the school numeric code by passing the index of our current school to the related numbers list
                        sftp.chdir(OUTPUT_FILE_DIRECTORY + school)  # change to the correct building subfolder
                        # print(sftp.pwd)  # debug, make sure out changedir worked
                        # print(sftp.pwd, file=log)  # debug, make sure out changedir worked
                        # print(sftp.listdir())
                        with open (filename, 'w') as output:  # open the file for the specific school
                            print(f'DBUG: Starting {school} - {schoolcode}, outputting to file {filename}')
                            print(f'DBUG: Starting {school} - {schoolcode}, outputting to file {filename}', file=log)
                            # do a query of all staff who have the building as their homeschool (to avoid duplicates across district) and who are active
                            cur.execute("SELECT lastfirst, teachernumber, email_addr, loginID, teacherLoginID FROM teachers WHERE homeschoolid = :school AND schoolid = :school AND status = 1 AND email_addr IS NOT NULL ORDER BY users_dcid DESC", school=schoolcode)  # using bind variables as best practice https://python-oracledb.readthedocs.io/en/latest/user_guide/bind.html#bind
                            teachers = cur.fetchall()
                            for teacher in teachers:
                                try:  # do each teacher in try/except blocks so we can skip a user without breaking the whole thing
                                    name = str(teacher[0])
                                    teacherNum = str(teacher[1])
                                    email = str(teacher[2])
                                    currentTeacherLogin = teacher[3]
                                    currentAdminLogin = teacher[4]
                                    login = email.split('@')[0]  # split the string with email by the @ symbol and only take the first part
                                    login = login[0:20]  # take only the first 20 characters if their name is longer, as that is the max length for the login field in PS
                                    print(f'DBUG: {name} | {login}', file=log)  # debug
                                    # print the fields out to the output file, duplicate the logins and passwords since there is both teacher and admin side login info
                                    if (currentTeacherLogin == None or currentAdminLogin == None):
                                        print(f'ACTION: {name} has missing login info in PS, writing to file for autocomm')
                                        print(f'ACTION: {name} has missing login info in PS, writing to file for autocomm', file=log)
                                        print(f'{name}\t{teacherNum}\t{login}\t{login}\t{password}\t{password}', file=output)  # output the fields as tab delimited
                                except Exception as er:
                                    print(f'ERROR on user {name}: {er}')
                                    print(f'ERROR on user {name}: {er}', file=log)

                        sftp.put(filename)  # upload the output file to the sftp server in the correct school directory
                        print(f'INFO: {filename} placed on the remote server')
                        print(f'INFO: {filename} placed on the remote server', file=log)

