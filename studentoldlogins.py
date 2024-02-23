"""Script to generate the old login fields for staff in PowerSchool, output to school specific files and upload to SFTP server.

https://github.com/Philip-Greyson/D118-OldLoginInfo

Goes through each active or pre-enrolled student, and if they do not have the web login fields populated, outputs their email twice to a file.
That file is then uploaded to a local SFTP server, where it will be imported into PowerSchool via AutoComm.
"""


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

OUTPUT_FILE_NAME = 'student-old-logins.txt'
OUTPUT_FILE_DIRECTORY = '/sftp/oldLogins/Students/'

EMAIL_SUFFIX = '@d118.org'  # email suffix which is used to construct their email, which is used as the login username and password since they do not actually use it to login, just needs to exist

print(f"Database Username: {DB_UN} |Password: {DB_PW} |Server: {DB_CS}")  # debug so we can see where oracle is trying to connect to/with
print(f'SFTP Username: {SFTP_UN} | D118 SFTP Password: {SFTP_PW} | D118 SFTP Server: {SFTP_HOST}')  # debug so we can see what info sftp connection is using


if __name__ == '__main__':  # main file execution
    with open('student_login_log.txt', 'w') as log:
        startTime = datetime.now()
        startTime = startTime.strftime('%H:%M:%S')
        print(f'INFO: Execution started at {startTime}')
        print(f'INFO: Execution started at {startTime}', file=log)
        try:
            with oracledb.connect(user=DB_UN, password=DB_PW, dsn=DB_CS) as con:  # create the connecton to the database
                with con.cursor() as cur:  # start an entry cursor
                    with open(OUTPUT_FILE_NAME, 'w') as output:
                        cur.execute('SELECT student_number, student_web_id, student_web_password FROM students WHERE enroll_status = 0 OR enroll_status =-1')
                        students = cur.fetchall()
                        for student in students:
                            try:
                                idNum = str(int(student[0]))
                                currentLogin = student[1]
                                currentPassword = student[2]
                                if (currentLogin == None or currentPassword == None):
                                    email = idNum + EMAIL_SUFFIX
                                    print(f'ACTION: {email} has missing login info in PS, writing to file for autocomm')
                                    print(f'ACTION: {email} has missing login info in PS, writing to file for autocomm', file=log)
                                    print(f'{idNum}\t{email}\t{email}', file=output)
                            except Exception as er:
                                print(f'ERROR while processing student {student[0]}: {er}')
                                print(f'ERROR while processing student {student[0]}: {er}', file=log)
        except Exception as er:
            print(f'ERROR while connecting to PowerSchool or doing query: {er}')
            print(f'ERROR while connecting to PowerSchool or doing query: {er}', file=log)

        try:
            # Now connect to the D118 SFTP server and upload the file to be imported into PowerSchool
            with pysftp.Connection(SFTP_HOST, username=SFTP_UN, password=SFTP_PW, cnopts=CNOPTS) as sftp:
                print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established')
                print(f'INFO: SFTP connection to D118 at {SFTP_HOST} successfully established', file=log)
                # print(sftp.pwd)  # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.chdir(OUTPUT_FILE_DIRECTORY)
                # print(sftp.pwd) # debug to show current directory
                # print(sftp.listdir())  # debug to show files and directories in our location
                sftp.put(OUTPUT_FILE_NAME)  # upload the file to our sftp server
                print("INFO: Student old logins file placed on remote server")
                print("INFO: Student old logins file placed on remote server", file=log)
        except Exception as er:
            print(f'ERROR while connecting or uploading to D118 SFTP server: {er}')
            print(f'ERROR while connecting or uploading to D118 SFTP server: {er}', file=log)

        endTime = datetime.now()
        endTime = endTime.strftime('%H:%M:%S')
        print(f'INFO: Execution ended at {endTime}')
        print(f'INFO: Execution ended at {endTime}', file=log)

