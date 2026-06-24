import io
import logging
import tarfile
import time

import docker
from docker.errors import ContainerError, NotFound
from lgs_shared.models.sandbox import SandboxResult, SandboxSubmission, SubmissionStatus

from sandbox.limits import (
    DEFAULT_TIMEOUT_SECONDS,
    MAX_TIMEOUT_SECONDS,
    MEM_LIMIT,
    NANO_CPUS,
    PIDS_LIMIT,
    RUNNER_IMAGE,
)

logger = logging.getLogger("sandbox.docker_runner")

WORKDIR = "/sandbox"
SUBMISSION_FILE = "test_submission.py"


def _build_tar(code: str, test_code: str | None) -> bytes:
    """Packs the submission (+ optional separate test file) into a tar stream
    so it can be injected via put_archive — avoids host/container path
    mismatches inherent to bind-mounting from a sibling container."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        content = code if test_code is None else f"{code}\n\n{test_code}\n"
        data = content.encode("utf-8")
        info = tarfile.TarInfo(name=SUBMISSION_FILE)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def run_submission(submission: SandboxSubmission) -> SandboxResult:
    timeout = min(submission.timeout_seconds, MAX_TIMEOUT_SECONDS) or DEFAULT_TIMEOUT_SECONDS
    client = docker.from_env()

    container = client.containers.create(
        image=RUNNER_IMAGE,
        command=["pytest", SUBMISSION_FILE, "-q"],
        working_dir=WORKDIR,
        network_disabled=True,
        mem_limit=MEM_LIMIT,
        nano_cpus=NANO_CPUS,
        pids_limit=PIDS_LIMIT,
        detach=True,
    )

    try:
        container.put_archive(WORKDIR, _build_tar(submission.code, submission.test_code))
        container.start()

        start = time.monotonic()
        try:
            exit_status = container.wait(timeout=timeout)
            status_code = exit_status.get("StatusCode", 1)
            timed_out = False
        except Exception:
            timed_out = True
            status_code = None

        elapsed = time.monotonic() - start
        logger.info("submission ran in %.2fs (timed_out=%s)", elapsed, timed_out)

        if timed_out:
            try:
                container.kill()
            except (NotFound, ContainerError):
                pass
            return SandboxResult(status=SubmissionStatus.TIMEOUT, stdout="", stderr="execution exceeded time limit")

        logs = container.logs(stdout=True, stderr=True).decode("utf-8", errors="replace")
        status = SubmissionStatus.PASS if status_code == 0 else SubmissionStatus.FAIL
        return SandboxResult(status=status, stdout=logs, stderr="", exit_code=status_code)
    except Exception as exc:
        logger.exception("sandbox execution error")
        return SandboxResult(status=SubmissionStatus.ERROR, stdout="", stderr=str(exc))
    finally:
        try:
            container.remove(force=True)
        except (NotFound, ContainerError):
            pass
