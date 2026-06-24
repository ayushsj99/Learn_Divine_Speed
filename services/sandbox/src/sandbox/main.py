from fastapi import FastAPI
from lgs_shared.models.sandbox import SandboxResult, SandboxSubmission

from sandbox.docker_runner import run_submission

app = FastAPI(title="Sandbox Service")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/execute", response_model=SandboxResult)
def execute(submission: SandboxSubmission) -> SandboxResult:
    return run_submission(submission)
