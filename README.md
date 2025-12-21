# Gator Tune

A simple Discord music bot to play music from YouTube. Uses the native ffmpeg player to allow more customisations than using lavalink. The sound quality is shit tho on the mobile client of Discord, idk why.

## Foreword

This bot uses pytubefix underneath, hence possible errors relating to YouTube's side is probably coming from pytubefix.

Since pytubefix version 10.0.0, YouTube has changed their player's obfuscation so much that there were no other ways to stream audios directly from their url anymore other than to download them first through pytubefix (so long as I know). A separate service was created to accommodate this change in [this repo](https://github.com/karelbondan/gator-tune-service) to allow faster downloading if your home internet bandwidth is shiette like mine and you have a VPS that has 10000x the bandwidth speed.

OAuth was also added since PoToken is now deprecated, with the PoToken option still being available since it hasn't been removed yet from pytubefix at the time of this writing. Whether you want to use the separate service or not it's up to you, and you can set it up using the `.env` settings which is provided below. It's recommended to use OAuth to greatly minimize the chances of your IP being flagged as a bot by YouTube like mine lol.

## Setup

This project uses uv, which can be installed from [the official website](https://docs.astral.sh/uv/getting-started/installation/). If you haven't used UV before oh my god you're missing out use it rn it's miles better than pip.

If you decide to use OAuth, you will be prompted to enter your credentials only once when the bot is first run. **It is highly recommended not to use your main account** since you can be banned by YouTube.

Run the bot using `uv run main.py` after you've finished configuring.

### Example `.env` configuration

```python
# === bot config ===
TOKEN=token # your bot token
OWNER=12345 # your user id
# set to False if you want to use PoToken or if you're -using- the service
USE_OAUTH=True 

# === stdout config ===
TAB_AMT=5

# === service config ===
USE_SERVICE=False
# enter your api key if you're using the service (see service readme for more info)
API_KEY=abcdefg
# leave as "" if you're -not- using the service
SERVICE_URL=http://il.youtube.sm
# leave as "" if you're -using- the service or using the default "./downloads"
DOWNLOAD_LOC=""
```

## Commands

**All commands have aliases which can be adjusted in `config.yml`**

- Play (auto join)
- Pause
- Resume
- Repeat
- Skip
- Stop
- Leave
- List queue
- Clear queue
- Remove queue at index
- Now playing

## Features

- Play musics from any kinds of youtube links
- Automatically add songs from playlists
- Auto search and play music without using any links
- Adjustable prefix
- Adjustable command aliases

## Todo

- Handle request error (non 200 status) when using external service
  - Send meaningful message
- Handle if ever bot detection triggered even after using oauth
  - Prompt the user again (?)

## Upcoming

**_Disclaimer: might not be implemented_**

- Show lyrics for currently playing song, or search for any lyrics
- Seek
- Rewind
- Skip multiple songs
- Reorder queue

© 2024 Karel Bondan © 2024 Unofficial [private] Fazbear Entertainment Discord Server
