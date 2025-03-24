from fastapi import HTTPException


class ICoreException(HTTPException):
    message: str
    http_code: int
    key: str

    def __init__(self):
        super().__init__(
            status_code=self.http_code,
            detail=f"{self.message} ({self.key})",
        )
