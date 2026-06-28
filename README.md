# storitad-web

Browser webapp for the [Storitad](https://github.com/barrulus/storitad) voice/video
journal — record, browse, and edit entries from any phone. Replaces the Android
capture app. Hosted behind pocket-id passkey auth.

- **Capture**: `MediaRecorder` voice/video + metadata + optional geolocation.
- **Browse/edit**: server-rendered from a markdown archive (the source of truth).
- **Transcription**: server-side whisper-small.en, async.
- **Auth**: Caddy `forward_auth` → oauth2-proxy → pocket-id; owner allowlist.

Vendors the ingest pipeline modules (`storitad_web/ingest/`) so it is a
self-contained deployable.

## Develop

    nix develop -c python -m pytest

## Run

    cp config.example.yml ~/.config/storitad/web.yml   # edit owners/paths
    nix run

Deployment (systemd + Caddy + oauth2-proxy on NixOS) lives in the quixote repo.
