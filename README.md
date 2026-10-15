# Couchside for Home Assistant

A Home Assistant integration for [Couchside](https://github.com/Omle555/Couchside), the self-hosted
movie and TV server for Windows. Home Assistant finds Couchside on your home network by itself and
shows **Discovered: Couchside**.

## What's new

**2026-10-15: first version**
- Discovers Couchside on the local network (mDNS, `_couchside._tcp`), signs in with a Couchside
  administrator account and adds sensors for what is playing, converting streams, library totals
  and library scans.

## Requirements

- Couchside with network discovery (any build from 2026-10-15 on), running with
  `bind = "0.0.0.0"` and `discovery = true` (the default) under `[server]` in
  `C:\ProgramData\Couchside\config.toml`. The PC's network profile must be **Private**.
- Home Assistant 2024.11 or newer, on the same home network as Couchside.

## Install

**With HACS:** HACS → ⋮ → **Custom repositories**, add this repository's URL with type
**Integration**, then install **Couchside** and restart Home Assistant.

**By hand:** copy `custom_components/couchside` into the `custom_components` folder of your Home
Assistant configuration (so you have `config/custom_components/couchside/manifest.json`) and
restart Home Assistant.

## Set up

**Settings → Devices & services** shows **Discovered: Couchside**. Click **Add** and sign in with a
Couchside administrator account. If it isn't discovered, click **Add integration**, search for
Couchside and type the PC's address (for example `192.168.1.20`) and port (`8096`).

Home Assistant keeps its own Couchside session and polls every 15 seconds. If the session ends
(signed out, or unused for 30 days), it asks you to sign in again.

## Entities

| Entity | What it shows |
|---|---|
| Playing | On while anything is playing (handy for dimming the lights) |
| Now playing | How many things are playing; attributes list the titles, viewers and positions |
| Converting streams | Repackaged or converted streams currently open |
| Movies, TV shows, Episodes | Library totals |
| Library scan | On while a scan or metadata refresh runs |

The data comes from Couchside's `GET /api/v1/activity` endpoint.

## License

MIT OR Apache-2.0, the same as Couchside.
