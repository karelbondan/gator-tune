import utilities.utilities as utils
from os import path
from pytubefix import Search, Playlist
import configs
import time

music = utils.Music()

first = time.time()

# potoken generator
potoken = music._potoken()
print(potoken)

# search
song_id, song_title = music.search("somebody real")
print((song_id, song_title))

# stream
source = music.stream(song_id)
print(source)

# playlist
url = "https://www.youtube.com/watch?v=WEBMU9HSChg&list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5&pp=gAQBiAQB"
id, title, duration, queue = music.playlist("PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5")
print(queue)


# # download
# song_id = music.download(song_id)
# print("completed: ", song_id)

# # file exist test
# print(path.isfile(path.join(configs.ROOT_DIR, "audios", "skdjks.mp4")))

# test 
# a = Search("kaiju 8 nobody")
# for i in range(10):
#     print(a.videos[i])

print("elapsed: ", time.time() - first)