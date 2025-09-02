from ftplib import FTP
from io import BytesIO

class InMemoryFTPClient:
    def __init__(self, host: str, user: str = "anonymous", password: str = ""):
        self.host = host
        self.user = user
        self.password = password
        self.ftp: FTP | None = None

    def __enter__(self):
        self.ftp = FTP(self.host)
        self.ftp.login(user=self.user, passwd=self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ftp:
            self.ftp.quit()

    def list_files(self, path: str = ".") -> list[str]:
        """List files in a directory."""
        assert self.ftp
        return self.ftp.nlst(path)

    def download_file(self, remote_path: str) -> bytes:
        """Download a file and return its contents as bytes."""
        assert self.ftp
        buffer = BytesIO()
        self.ftp.retrbinary(f"RETR {remote_path}", buffer.write)
        buffer.seek(0)
        return buffer.getvalue()
