import ftplib
import ssl
import logging
from config import CONFIG as cfg
import os


class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, host='', port='990', username='', passwd='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None
        self.set_debuglevel(cfg['RUN']['DEBUG_LEVEL'])
        self.set_pasv(True)

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value


class Ftps:
    def __init__(self, input_format='.mp3', output_format='.ctm'):
        self.ftp_user_var_name = cfg['SFTP']['USER_VARIABLE_NAME']
        self.ftp_pwd_var_name = cfg['SFTP']['PWD_VARIABLE_NAME']
        self.host = cfg['SFTP']['URL']
        self.port = cfg['SFTP']['PORT']
        self.username = None
        self.passwd = None
        self.client = ImplicitFTP_TLS()
        self.input_format = cfg['RUN']['INPUT_FORMAT']
        self.output_format = cfg['RUN']['OUTPUT_FORMAT']
        self._get_ftp_credentials()

    def _get_ftp_credentials(self):
        logging.debug('Trying to get ftp credentials')
        if cfg['RUN']['TEST_PHASE'] == True:
            self.username = 'xxx'
            self.passwd = 'xxxx'
            return True

        output = True
        try:
            self.username = os.environ[self.ftp_user_var_name]
            logging.debug('FTP user: ->[' + self.username + ']<-')
        except:
            logging.error('Could not get ftp user, can not continue')
            exit(1001)

        try:
            self.passwd = os.environ[self.ftp_pwd_var_name]
            logging.debug('FTP password: ->[' + self.passwd + ']<-')
        except:
            logging.error('Could not get ftp password, can not continue')
            exit(1002)

        return output

    def connect(self):
        logging.debug('Trying to connect to ->[' + self.host + ']<- on port ->[' + str(self.port) + ']<-')
        try:
            self.client.connect(self.host, self.port)
            self.login()
        except Exception as e:
            logging.error('Could not connect to ftp, reason: ' + e.__str__())
            return False

        logging.debug('Establishing secure connection')
        try:
            self.client.prot_p()
            logging.info('Connection established')
            return True
            # return self.client
        except Exception as e:
            logging.error('Could not establish secure connection' + e.__str__())
            return False

    def login(self):
        logging.debug('Trying to login')
        try:
            self.client.login(self.username, self.passwd)
            logging.info('Successfully logged in')
            return True
        except Exception as e:
            logging.error('Could not login' + e.__str__())
            return False

    def _cd(self, folder):
        logging.debug('Changing directory to ->[' + folder + ']<-')
        try:
            self.client.cwd(folder)
            logging.debug('Directory changed successfully')
        except Exception as e:
            logging.error('Could not change directory' + e.__str__())
            return False

    def download(self, filename, local_folder, remote_folder=None):
        output = False
        file_id = filename  # keep filename without the extension for overwrite function
        filename += self.input_format
        logging.debug('Trying to download file ->[' + filename + ']<- from ->[' + str(
            remote_folder) + ']<- to ->[' + local_folder + ']<-')

        if self.connect():
            if remote_folder: self._cd(remote_folder)

            current_folder = self.client.pwd()
            if not cfg['RUN']['OVERWRITE']:
                logging.debug('Overwrite turned off')
                converted_file_path = current_folder.strip('/') + '/' + file_id + self.output_format
                if self.file_exists(converted_file_path):
                    logging.info('File was already converted, skipping')
                    return False

            logging.debug('Trying to download from folder: ' + str(current_folder))
            handle = open(local_folder.rstrip("/") + "/" + filename.lstrip("/"), 'wb')
            try:
                result = self.client.retrbinary('RETR %s' % filename, handle.write)
                logging.debug('Download result: ' + str(result))
                output = True
            except Exception as e:
                logging.error('Download failed: ' + e.__str__())
                output = False


        if output:
            if result.__contains__('Successfully transferred'):
                logging.info('File downloaded successfully')
            else:
                logging.error('Download failed')
        else:
            print('Failure')

        self.client.quit()
        return output

    def size(self, filename, remote_folder=''):
        output = False
        if self.connect():
            if remote_folder: self._cd(remote_folder)
            logging.debug("Trying to get a size of file ->[" + filename + "]<-")
            try:
                size = self.client.size(filename)
                logging.debug('Size of the uploaded file is: ' + str(size))
                output = int(size)

            except Exception as e:
                logging.error('Could not get the file size: ' + e.__str__())
            finally:
                self.client.quit()

        return output

    def upload(self, filename, local_folder, remote_folder=None):
        result = False
        logging.debug('Trying to upload file ->[' + filename + ']<- from ->[' + str(
            local_folder) + ']<- to ->[' + str(remote_folder) + ']<-')

        if self.connect():
            if remote_folder: self._cd(remote_folder)

            current_folder = self.client.pwd()
            # filepath = current_folder.rstrip("/") + '/' + filename.lstrip("/")
            logging.debug('Trying to upload into: ' + str(current_folder))
            handle = open(local_folder.rstrip("/") + "/" + filename.lstrip("/"), 'rb')
            try:
                self.client.storbinary('STOR %s' % filename, handle)
                # logging.debug('Upload result: ' + str(result))
            except Exception as e:
                logging.error('Upload failed: ' + e.__str__())
            finally:
                self.client.quit()

    def file_exists(self, filepath):
        filepath = filepath.strip('/')
        logging.debug('Checking if file ->[' + filepath + ']<- exists')
        output = False
        files = self.client.nlst()
        if filepath in files:
            logging.info('File ->[' + filepath + ']<- exists')
            output = True
        return output