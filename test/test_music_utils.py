import utilities.utilities as utils
from os import path
import configs
import re
import os

music = utils.Music()


# potoken generator
def test_potoken():
    visitor_data, po_token = music._potoken()
    assert type(visitor_data) == str
    assert type(po_token) == str


# search
def test_music_search():
    global song_id
    song_id, song_title, duration = music.search("somebody real")
    assert type(song_id) == str
    assert type(song_title) == str
    assert type(duration) == str


# stream
def test_music_get_stream_url():
    global song_id
    song_id = song_id or "WEBMU9HSChg"
    source = music.stream(song_id)
    assert type(source) == str


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
    assert len(pl_id) == 1
    id, title, duration, queue = music.playlist(pl_id[0])
    assert type(id) == str
    assert type(title) == str
    assert type(duration) == str
    assert type(queue) == list
    test_dict = {'duration': '', 'id': '', 'title': ''}
    for song_detail in queue:
        assert song_detail.keys() == test_dict.keys()


# download
def test_music_download():
    global song_id
    song_id = song_id or "WEBMU9HSChg"
    song_id = music.download(song_id)
    assert type(song_id) == str
    output_file = path.join(configs.ROOT_DIR, "audios", "{}.mp3".format(song_id))
    assert path.exists(output_file) == True


# file exist test
def test_file_exists():
    template = path.join(configs.ROOT_DIR, "audios")
    file = path.join(template, "skdjks.mp4")
    assert path.exists(file) == False
    file = path.join(template, "{}.mp3".format(song_id))
    assert path.exists(file) == True
    os.remove(file)
    assert path.exists(file) == False
