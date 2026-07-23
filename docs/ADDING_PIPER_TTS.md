# Piper TTS backend

This backend benchmarks local text-to-speech vocalization with Piper inside Docker.

## User flow

```bash
teenmodo engine install piper_tts
teenmodo model install piper_tts VOICE_ALIAS DIRECT_ONNX_URL
teenmodo run piper_tts VOICE_ALIAS vocalize_short
```

The user supplies one direct `.onnx` URL. The backend automatically derives and downloads the required adjacent `.onnx.json` voice configuration. No model YAML and no host registry are used.

## Known working voice

Alias:

```text
lessac
```

Model URL:

```text
https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
```

The corresponding configuration is resolved automatically from the same URL plus `.json`.

## Canonical job

`jobs/audio/vocalize_short.yaml` introduces the `text_to_speech` job kind:

```yaml
version: 1
id: vocalize_short
kind: text_to_speech
media_type: audio
input:
  text: "TeenModo is testing local text to speech inside Docker."
parameters:
  sentence_silence: 0.15
  volume: 1.0
```

Create an editable copy:

```bash
teenmodo job create vocalize_short my_voice_test
```

Edit only `volume/jobs/my_voice_test.yaml`, then run:

```bash
teenmodo run piper_tts lessac my_voice_test
```

## Files owned by the backend

```text
engines/piper_tts/
    __init__.py
    adapter.py
    backend.yaml
    compose.yaml
    Dockerfile
```

The backend owns:

- Piper runtime image build;
- direct ONNX and companion JSON download;
- retry and partial download resume;
- staged atomic installation and rollback;
- real synthesis verification before registration;
- WAV validation;
- generated installation manifests;
- TTS execution and audio metrics.

The host remains generic.

## Stored data

```text
volume/engines/piper_tts/models/<alias>/
volume/engines/piper_tts/model-manifests/
volume/out/piper_tts/<alias>/
```

## Report metrics

Each successful run records:

- inference wall time;
- generated audio duration;
- real-time factor;
- generated-audio-seconds per wall second;
- characters per second;
- sample rate, frames, channels and sample width;
- input and output byte counts;
- host CPU, RAM and container telemetry collected by TeenModo.

## Served failures

The adapter returns structured errors for:

- missing source URL;
- invalid alias;
- non-HTTP source;
- non-ONNX source;
- failed model or configuration download;
- malformed configuration JSON;
- synthesis/load failure;
- empty or invalid WAV output;
- unsupported job kind;
- empty text;
- invalid job parameters;
- missing installed files;
- engine command timeout.

