import utilities.utilities as utils
from os import path
import configs

music = utils.Music()

# potoken generator
potoken = music._potoken()
print(potoken)

# search
song_id, song_title = music.search("somebody real")
print((song_id, song_title))

# download
song_id = music.download(song_id)
print("completed: ", song_id)

# file exist test
print(path.isfile(path.join(configs.ROOT_DIR, "audios", "skdjks.mp4")))