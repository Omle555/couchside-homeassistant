# Couchside for Home Assistant

A Home Assistant integration for [Couchside](https://github.com/Omle555/Couchside), the self-hosted
movie and TV server for Windows. Home Assistant finds Couchside on your home network by itself and
shows **Discovered: Couchside**.

## What's new

**2026-10-15: Movie art (0.3.0)**
- New **Movie poster** image shows the backdrop (or poster, if there is no backdrop) of the movie
  being watched. The **Movie playing** sensor uses it as its picture while a movie plays.
- See [Dashboard card](#dashboard-card) for a card with the art as the background and the title
  on top.

**2026-10-15: Movie playing sensor (0.2.0)**
- New **Movie playing** sensor shows the title of the movie being watched, or `Nothing playing`.
  Its attributes say who is watching, the position, runtime and percent watched, and list every
  movie playing if there's more than one.

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
| Movie playing | Title of the movie being watched (the newest if several), or `Nothing playing`; attributes `viewer`, `position`, `runtime`, `progress` (%) and `movies` |
| Movie poster | Backdrop (or poster) of the movie being watched; empty when no movie is playing |
| Now playing | How many things are playing; attributes list the titles, viewers and positions |
| Converting streams | Repackaged or converted streams currently open |
| Movies, TV shows, Episodes | Library totals |
| Library scan | On while a scan or metadata refresh runs |

The data comes from Couchside's `GET /api/v1/activity` endpoint. The art comes from
`GET /api/v1/items/{id}/image/backdrop` (or `.../poster`), fetched by Home Assistant with its own
Couchside session, so your browser never needs to reach Couchside.

## Dashboard card

A short banner with the movie art as the background and the title on the left, centred
vertically, only while a movie is playing. Edit a dashboard → **Add card** → **Manual**, paste this
and replace `couchside` in the entity ids with yours (see **Settings → Devices & services →
Couchside → entities**). Change `aspect_ratio` to make it taller (`3:1`) or shorter (`8:1`).

```yaml
type: conditional
conditions:
  - condition: state
    entity: sensor.couchside_movie_playing
    state_not: Nothing playing
card:
  type: picture-elements
  image_entity: image.couchside_movie_poster
  aspect_ratio: "64:9"
  elements:
    - type: state-label
      entity: sensor.couchside_movie_playing
      style:
        top: 50%
        left: 0
        transform: translate(0, -50%)
        padding: 0 20px
        color: white
        font-size: 24px
        font-weight: 600
        text-shadow: 0 1px 6px rgba(0, 0, 0, 0.9)
```

## License

MIT OR Apache-2.0, the same as Couchside.
