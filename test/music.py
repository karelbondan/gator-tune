import utilities.utilities as utils

music = utils.Music()
song_id, song_title = music.search("somebody real")
print((song_id, song_title))
song_id = music.download(song_id)
print("completed: ", song_id)
