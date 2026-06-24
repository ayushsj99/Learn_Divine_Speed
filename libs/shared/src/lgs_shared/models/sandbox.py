from enum import StrEnum

from pydantic import BaseModel


class SubmissionStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    ERROR = "error"


class SandboxSubmission(BaseModel):
    code: str
    test_code: str | None = None
    timeout_seconds: int = 10


class SandboxResult(BaseModel):
    status: SubmissionStatus
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
