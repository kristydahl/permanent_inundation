from ftplib import FTP

ftp = FTP('ftp2.census.gov')

ftp.cwd('/geo/tiger/TIGER2016/COUSUB/')
ftp.login(user = 'USER', passwd = 'PASS')

def grabFile():

    state_number = ['01']

    filename = 'tl_2016_' + state_number + '_cousub.zip'

    localfile = open(filename, 'wb')

    ftp.retrbinary('RETR ' + filename, localfile.write, 1024)

    print 'retrieved binary'

    ftp.quit()

    localfile.close()


grabFile()
#,'06','09','10','11','12','13','22','23','24','25','28','33','34','36','37','41','42','44','45','48','51','53'