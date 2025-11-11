class ClientError(Exception):
    """Base exception for client errors."""
    pass

class FtpError(ClientError):
    """Raised for FTP-specific errors."""
    pass


class CcvError(ClientError):
    pass


class PerfionError(ClientError):
    pass


class LocalFileError(ClientError):
    """Raised for local file-specific errors."""
    pass
