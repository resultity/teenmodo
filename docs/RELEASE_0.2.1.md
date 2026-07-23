# TeenModo 0.2.1

- Replaced the Compose `gpus` service key, which requires Compose 2.30+, with the broadly supported NVIDIA device reservation form.
- Preserved explicit NVIDIA device selection through `device_ids`.
- Prevented Rich markup parsing from producing a second traceback while rendering structured TeenModo errors.

