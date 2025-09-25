import logging
from ftplib import FTP, error_perm, all_errors
from io import BytesIO

from clients.errors import FtpError


logger = logging.getLogger(__name__)



class FTPClient:
    def __init__(self, host: str, user: str = "anonymous", password: str = ""):
        self.host = host
        self.user = user
        self.password = password
        self.ftp: FTP | None = None

    def __enter__(self) -> "FTPClient":
        try:
            logger.debug(f"Connecting to FTP server at {self.host}")
            self.ftp = FTP(self.host, timeout=30)
            self.ftp.login(user=self.user, passwd=self.password)
            logger.info(f"Logged in to FTP server: {self.host} as {self.user}")
            return self
        except all_errors as e:
            logger.error(f"Failed to connect or login to FTP server: {self.host}, error: {e}")
            raise FtpError(f"FTP connection/login failed: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ftp:
            try:
                self.ftp.quit()
                logger.info(f"FTP connection to {self.host} closed successfully.")
            except all_errors as e:
                logger.warning(f"Error while closing FTP connection: {e}")

    def list_files(self, path: str = ".") -> list[str]:
        if not self.ftp:
            logger.error("FTP connection not established. Cannot list files.")
            raise FtpError("FTP connection not established.")

        try:
            logger.debug(f"Listing files at path: {path}")
            files = self.ftp.nlst(path)
            logger.info(f"Found {len(files)} file(s) at path: {path}")
            return files
        except error_perm as e:
            logger.warning(f"Permission error when listing files at {path}: {e}")
            return []  # Return empty list on permission error
        except all_errors as e:
            logger.error(f"Failed to list files at {path}: {e}")
            raise FtpError(f"Error listing files at {path}: {e}") from e

    def download_file(self, remote_path: str) -> bytes:
        if not self.ftp:
            logger.error("FTP connection not established. Cannot download file.")
            raise FtpError("FTP connection not established.")

        buffer = BytesIO()
        try:
            logger.debug(f"Downloading file: {remote_path}")
            self.ftp.retrbinary(f"RETR {remote_path}", buffer.write)
            logger.info(f"Successfully downloaded file: {remote_path}")
            buffer.seek(0)
            return buffer.getvalue()
        except error_perm as e:
            logger.error(f"Permission error when downloading {remote_path}: {e}")
            raise FtpError(f"Permission denied for file: {remote_path}") from e
        except all_errors as e:
            logger.error(f"Failed to download file {remote_path}: {e}")
            raise FtpError(f"Error downloading file {remote_path}: {e}") from e
