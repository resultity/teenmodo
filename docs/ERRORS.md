# Error contract

Expected failures are emitted as one stable code plus a direct reason and context. The CLI does not expose a traceback for handled failures.

Important codes include:

- `ENGINE_NOT_FOUND`, `ENGINE_INSTALL_ERROR`, `ENGINE_VERIFICATION_ERROR`
- `MODEL_SOURCE_INVALID`, `MODEL_SOURCE_UNSUPPORTED`, `MODEL_INSTALL_ERROR`, `MODEL_VERIFICATION_ERROR`, `MODEL_NOT_FOUND`
- `JOB_NOT_FOUND`, `JOB_UNSUPPORTED`, `JOB_INVALID`
- `DOCKER_COMMAND_ERROR`, `COMMAND_TIMEOUT`, `CONTROLLER_BUSY`, `OPERATION_LOCKED`
- `RUN_EXECUTION_ERROR`

A failed staged model install restores the prior verified model. A failed engine install captures logs and tears down the failed package. Unexpected faults are reported as `UNEXPECTED_ERROR` without claiming success.

