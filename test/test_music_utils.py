import re

import utilities.classes.utilities as utils

music = utils.MusicUtils()


# potoken generator
def test_potoken():
    visitor_data, po_token = music._potoken()
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
    except Exception as e:
        print(music.search("somebody real"))
        raise e


# stream
def test_music_get_stream_url():
    global song_id
    try:
        song_id = song_id or "WEBMU9HSChg"
        source = music.stream(song_id)
        assert isinstance(source, str)
    except Exception as e:
        print(music.stream(song_id))
        raise e


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
        id, title, duration, queue, title = music.playlist(pl_id[0])
        assert isinstance(id, str)
        assert isinstance(title, str)
        assert isinstance(duration, str)
        assert isinstance(queue, list)
        test_dict = {"duration": "", "id": "", "title": ""}
        for song_detail in queue:
            assert song_detail.keys() == test_dict.keys()
    except Exception as e:
        print(music.playlist(pl_id[0]))
        raise e
