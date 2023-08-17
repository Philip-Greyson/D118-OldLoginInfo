# importing module
import oracledb # needed for connection to PowerSchool server (ordcle database)
import sys # needed for  non-scrolling display
import os # needed for environement variable reading
import pysftp # needed for sftp file upload

un = 'PSNavigator'  # PSNavigator is read only, PS is read/write
# the password for the database account
pw = os.environ.get('POWERSCHOOL_DB_PASSWORD')
# the IP address, port, and database name to connect to
cs = os.environ.get('POWERSCHOOL_PROD_DB')

#set up sftp login info
sftpUN = os.environ.get('D118_SFTP_USERNAME')
sftpPW = os.environ.get('D118_SFTP_PASSWORD')
sftpHOST = os.environ.get('D118_SFTP_ADDRESS')
cnopts = pysftp.CnOpts(knownhosts='known_hosts') # connection options to use the known_hosts file for key validation

password = os.environ.get('D118_TEMP_PASSWORD') # just a generic password since it is not actually used to login, just to populate the fields

print("Username: " + str(un) + " |Password: " + str(pw) + " |Server: " + str(cs)) #debug so we can see where oracle is trying to connect to/with
print("SFTP Username: " + str(sftpUN) + " |SFTP Password: " + str(sftpPW) + " |SFTP Server: " + str(sftpHOST)) #debug so we can see what credentials are being used

# create the connecton to the database
with oracledb.connect(user=un, password=pw, dsn=cs) as con:
    with con.cursor() as cur:  # start an entry cursor
        with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
            with open('student_login_log.txt', 'w') as outputLog:
                with open('student-old-logins.txt', 'w') as output:
                    print("Connection established: " + con.version)
                    print('SFTP connection established')
                    sftp.chdir('/sftp/oldLogins/Students')  # change to the correct building subfolder
                    print(sftp.pwd)  # debug, show what folder we connected to
                    print(sftp.listdir())  # debug, show what other files/folders are in the current directory
                    cur.execute('SELECT student_number FROM students WHERE enroll_status = 0 OR enroll_status =-1')
                    students = cur.fetchall()
                    for student in students:
                        idNum = str(int(student[0]))
                        email = idNum + '@d118.org'
                        print(f'{idNum}\t{email}\t{email}', file=output)
                        
                # needs to be put up to sftp after the file is closed
                sftp.put('student-old-logins.txt') # upload the output file to the sftp server in the correct school directory
                print('\n' + 'student-old-logins.txt' + " placed on the remote server")
                print('student-old-logins.txt' + " placed on the remote server", file=outputLog)

