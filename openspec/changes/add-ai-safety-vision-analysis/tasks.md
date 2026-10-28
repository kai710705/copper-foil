# Tasks

## 1. External service configuration and client boundary

- [x] 1.1 Add environment-based Ollama settings for endpoint, API key, model, timeout, and image limits; verify no secret is present in source, documentation, or `.env.example`.
- [x] 1.2 Implement an Ollama client boundary for authenticated image requests and normalized provider errors; verify unit tests cover success, timeout, non-success HTTP responses, and missing configuration.
- [x] 1.3 Confirm the current Ollama cloud endpoint, authentication header, and Gemma vision payload format from authoritative service documentation or a controlled test; record the confirmed contract without storing credentials.

## 2. Vision analysis service

- [x] 2.1 Add a service input/output model for a camera frame and the three safety checks; verify invalid image size, format, and missing frame are rejected.
- [x] 2.2 Implement the vision analysis service using the Ollama client and structured output validation; verify `pass`, `fail`, `unknown`, invalid JSON, missing fields, and out-of-range confidence cases.
- [x] 2.3 Add the authorized manual analysis API under `/api/v1/` and return the standard success/error envelopes; verify unapproved users are denied and provider failures do not expose secrets or block `/video` streaming.
- [x] 2.4 Add the manual analysis control and loading/success/failure states to the `/video` Vue page using local Axios, Bootstrap, and SweetAlert2 resources; verify the existing MJPEG image remains visible while analysis is unavailable.

## 3. Alert persistence and state handling

- [x] 3.1 Add a repeatable SQLite migration for analysis metadata, check statuses, confidence values, model information, observation time, and deduplication support; verify existing alert data remains readable and integrity checks pass.
- [x] 3.2 Implement the safety alert repository with parameterized queries for creation, open-alert lookup, observation update, listing, and resolution; verify transaction rollback leaves no partial alert record.
- [x] 3.3 Implement the safety alert service so only explicit `fail` creates or updates an open alert, while all-pass and unknown-only results do not create danger alerts; verify duplicate observations update rather than insert.
- [x] 3.4 Integrate administrator alert query and resolution behavior with existing authorization and CSRF rules; verify non-administrators cannot change alert state and resolved incidents can produce a later new alert.

## 4. Verification and documentation

- [x] 4.1 Add service and API tests for camera-frame acquisition, Ollama responses, structured validation, alert deduplication, authorization, and error mapping; verify the focused test suite passes in the project interpreter.
- [x] 4.2 Update README and environment documentation with safe Ollama configuration, manual analysis usage, offline behavior, and the limitation that AI results do not replace human safety inspection; verify every documented command is executable without a real key.
- [ ] 4.3 Perform an end-to-end local verification with a fake Ollama client and fake camera frame, then verify `/video`, analysis response, database alert record, and alert resolution flow; record any real-device or external-service checks that remain pending.
