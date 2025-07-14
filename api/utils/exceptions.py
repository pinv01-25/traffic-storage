class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass

class IPFSError(StorageError):
    """Exception raised for IPFS-related errors."""
    pass

class BlockDAGError(StorageError):
    """Exception raised for BlockDAG-related errors."""
    pass

class ValidationError(StorageError):
    """Exception raised for data validation errors."""
    pass

class UploadError(StorageError):
    """Exception raised for upload operation errors."""
    pass

class DownloadError(StorageError):
    """Exception raised for download operation errors."""
    pass 