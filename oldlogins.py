# Script to generate the "old login info" for teachers in PS
# Fills in the login info, and teacher login info which is needed for them
# to get a PCAS account created, needed for other scripts to populate the Global ID field for SSO.
# Generates a separate file for each building which will then be autocomm'd into PS so it does not make duplicates of teachers
# Writing the values directly to the database also does not seem to make the PCAS account but autocomm does

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

schoolList = ['WHS', 'WMS', 'MMS', 'WGS', 'RCS', 'CCS', 'Onboarding', 'SSO', 'Transportation', 'Technology', 'Central Office', 'Curriculum', 'Superintendent', 'Sub', 'Maintenance', 'SEDOL', 'District Office']
schoolNumbers = ['5', '1003', '1004', '2001', '2005', '2007', '2', '133', '300', '134', '135', '131', '136', '500', '132', '183', '0']

# create the connecton to the database
with oracledb.connect(user=un, password=pw, dsn=cs) as con:
    with con.cursor() as cur:  # start an entry cursor
        with pysftp.Connection(sftpHOST, username=sftpUN, password=sftpPW, cnopts=cnopts) as sftp:
            with open('login_log.txt', 'w') as outputLog:
                print("Connection established: " + con.version)
                print('SFTP connection established')
                # print(sftp.pwd)  # debug, show what folder we connected to
                # print(sftp.listdir())  # debug, show what other files/folders are in the current directory
                for index, school in enumerate(schoolList): # go through each school in the list one at a time, allows us to search for only that building and output to individual files
                    #print(str(index) + ': ' + school + '|' + schoolNumbers[index])
                    filename = school + '-Old-Logins.txt' # make a unique filename for each output file
                    schoolcode = schoolNumbers[index] # the school numeric code by passing the index of our current school to the related numbers list
                    sftp.chdir('/sftp/oldLogins/' + school)  # change to the correct building subfolder
                    print(sftp.pwd)  # debug, make sure out changedir worked
                    print(sftp.pwd, file=outputLog)  # debug, make sure out changedir worked
                    # print(sftp.listdir())
                    with open (filename, 'w') as output:
                        print("Starting " + school)
                        print("Starting " + school, file=outputLog)
                        print(filename, file=outputLog) # debug
                        print(schoolcode, file=outputLog) # debug
                        # do a query of all staff who have the building as their homeschool (to avoid duplicates across district) and who are active
                        cur.execute("SELECT lastfirst, teachernumber, email_addr FROM teachers WHERE homeschoolid = " + schoolcode + " AND schoolid = " + schoolcode + " AND status = 1 AND email_addr IS NOT NULL ORDER BY users_dcid DESC")
                        teachers = cur.fetchall()
                        for count, teacher in enumerate(teachers):
                            try: # do each teacher in try/except blocks so we can skip a user without breaking the whole thing
                                sys.stdout.write('\rProccessing staff entry %i' % count) # sort of fancy text to display progress of how many students are being processed without making newlines
                                sys.stdout.flush()
                                name = str(teacher[0])
                                teacherNum = str(teacher[1])
                                email = str(teacher[2])
                                login = email.split('@')[0] # split the string with email by the @ symbol and only take the first part
                                login = login[0:20] # take only the first 20 characters if their name is longer, as that is the max length for the login field in PS
                                print(name + ' | ' + login, file=outputLog) # debug
                                # print the fields out to the output file, duplicate the logins and passwords since there is both teacher and admin side login info
                                print(name + '\t' + teacherNum + '\t' + login + '\t' + login + '\t' + password + '\t' + password, file=output)
                            except Exception as er:
                                print("Error on user " + str(teacher[0]) + str(er))
                                print("Error on user " + str(teacher[0]) + str(er), file=outputLog)
                    
                    sftp.put(filename) # upload the output file to the sftp server in the correct school directory
                    print('\n' + filename + " placed on the remote server")
                    print(filename + " placed on the remote server", file=outputLog)
                    print('------------------------') # visual divider between school entries

