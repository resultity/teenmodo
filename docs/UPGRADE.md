# Upgrade to 0.3.3

Do not copy an old `volume/engines/diffusers` directory into this release. The old installer may contain a full repository snapshot, duplicate Hugging Face cache blobs, incomplete staging data, and root-owned backend files.

Preserve `volume/out` when you want to keep generated images and reports. Preserve `volume/teenmodo.sqlite3` only when you want historical run records; a clean database is safer for a clean reinstall.

After stopping the old Diffusers stack, the following old paths are disposable and will be recreated:

- `volume/engines/diffusers`
- `volume/generated/diffusers`
- `volume/teenmodo.lock`

The supported workflow remains:

```bash
teenmodo engine install diffusers
teenmodo model install diffusers sd15
teenmodo run diffusers sd15 image_smoke
```

From the old project directory, stop the active command first, then clean only disposable Diffusers state:

```bash
teenmodo engine stop diffusers 2>/dev/null || true
sudo rm -rf volume/engines/diffusers volume/generated/diffusers volume/teenmodo.lock
```

This preserves `volume/out`, `volume/in`, and `volume/teenmodo.sqlite3`.

