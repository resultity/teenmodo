# Troubleshooting

## Start with doctor

```bash
teenmodo doctor
```

Do not diagnose model performance until Docker, Compose, and the intended accelerator path are working.

## Command or option does not exist

Use the command group help:

```bash
teenmodo --help
teenmodo engine --help
teenmodo model --help
teenmodo job --help
teenmodo report --help
```

Examples:

```bash
teenmodo model list ollama
teenmodo report summary --engine ollama --model ministral14b
```

`engine` is a positional argument for `model list`. `report` requires a subcommand.

## GPU was not detected

On Linux/WSL2 NVIDIA:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
teenmodo doctor
```

If the manual Docker test fails, TeenModo cannot repair the driver or container runtime.

## macOS shows CPU

That is the current Docker limitation. TeenModo cannot prove Apple GPU use through these containers. Do not treat it as an application detection bug.

## Find the failed run

```bash
teenmodo report list --limit 20
teenmodo report show RUN_ID
teenmodo paths
```

The failed report contains a stable error code and context. Engine logs may also be included in installation failures.

## Model exists in Ollama but not TeenModo

TeenModo requires both backend detection and a verified TeenModo model record. Reinstall or verify through TeenModo:

```bash
teenmodo model install ollama ALIAS SOURCE
teenmodo model verify ollama ALIAS
teenmodo model list ollama
```

## Report summary is empty

The summary aggregates passed runs only. Confirm filters and inspect the list:

```bash
teenmodo report list --engine ENGINE --model MODEL
```

