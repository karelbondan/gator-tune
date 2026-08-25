import re

import classes.music_utils as utils
from main import bot

music = utils.MusicUtils(bot)


# potoken generator
async def test_potoken():
    visitor_data, po_token = await music._potoken()
    assert isinstance(visitor_data, str)
    assert isinstance(po_token, str)


# search
def test_music_search():
    global song_id
    try:
        url, song_id, song_title, duration = music.search("somebody real")
        assert isinstance(url, str)
        assert isinstance(song_id, str)
        assert isinstance(song_title, str)
        assert isinstance(duration, str)
    except Exception:
        print(music.search("somebody real"))
        raise


# stream
def test_music_get_stream_url():
    global song_id
    try:
        song_id = song_id or "WEBMU9HSChg"
        source = music.stream(song_id)
        assert isinstance(source, str)
    except Exception:
        print(music.stream(song_id))
        raise


# playlist
def test_playlist_regex():
    global pattern
    pattern = r"(?<=list=)[\w-]+"
    url = "https://www.youtube.com/watch?v=WEBMU9HSChg&list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5&pp=gAQBiAQB"
    pl_id = re.findall(pattern, url)
    assert len(pl_id) == 1
    url = "https://www.youtube.com/playlist?list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5"
    pl_id = re.findall(pattern, url)
    assert len(pl_id) == 1
    url = "https://www.youtube.com/watch?v=WEBMU9HSChg"
    pl_id = re.findall(pattern, url)
    assert len(pl_id) == 0


def test_playlist_find():
    url = "https://www.youtube.com/playlist?list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5"
    pl_id = re.findall(pattern, url)
    try:
        assert len(pl_id) == 1
        # id, title, duration, queue, title = music.playlist(pl_id[0])
        playlist = music.playlist(pl_id[0])
        assert isinstance(playlist["id"], str)
        assert isinstance(playlist["title"], str)
        assert isinstance(playlist["duration"], str)
        assert isinstance(playlist["queue"], list)
        test_dict = {"duration": "", "id": "", "title": ""}
        for song_detail in playlist["queue"]:
            assert song_detail.keys() == test_dict.keys()
    except Exception:
        print(music.playlist(pl_id[0]))
        raise
