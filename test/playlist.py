import requests
import configs
from bs4 import BeautifulSoup
import json
import re
import time

first = time.time()

test_type = "video"
print("Acquiring playlist from type {}...".format(test_type))

if test_type == "video":
    url = "https://www.youtube.com/watch?v=WEBMU9HSChg&list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5&pp=gAQBiAQB"
    file_video = "./out/playlist_video.txt"
    file_script = "./out/playlist_video_script.txt"
    file_stripped = "./out/playlist_video_json.txt"
else:
    url = "https://www.youtube.com/playlist?list=PLnjSDipHxD67AUyODmVlrNElfzhpVZqL5"
    file_video = "./out/playlist_playlist.txt"
    file_script = "./out/playlist_playlist_script.txt"
    file_stripped = "./out/playlist_playlist_json.txt"

# invalid
# url = "https://www.youtube.com/watch?v=WEBMU9HSChg"
hadeh = re.findall(r"(?<=list=)[\w-]+", url)
template = "https://www.youtube.com/playlist?list="

if len(hadeh) == 0:
    print("not a playlist url")
    exit()

url = template + hadeh[0]
print("list url:", url)

response = requests.get(url=url, headers=configs.HEADERS)

soup = BeautifulSoup(response.content, features="html5lib")

with open(file_video, "w") as playlist:
    a = soup.prettify()
    playlist.write(a)

data = {}

with open(file_script, "w") as script_find:
    test = soup.find_all("script")

    for i in test:
        stringified = str(i)
        if "ytInitialData" in stringified:
            stripped = re.findall(r"(?<=ytInitialData = ).+(?=;</script>)", stringified)
            script_find.write(stringified)
            with open(file_stripped, "w") as stripped_out:
                stripped_out.write(str(stripped[0]))
            data = json.loads(stripped[0])
            break

# fmt:off
playlist_title = data["header"]["pageHeaderRenderer"]["pageTitle"]
actual_list = data["contents"] \
    ["twoColumnBrowseResultsRenderer"]["tabs"][0] \
    ["tabRenderer"]["content"]["sectionListRenderer"] \
    ["contents"][0]["itemSectionRenderer"]["contents"][0] \
    ["playlistVideoListRenderer"]["contents"]
# fmt:on

print("\n===Showing video list for playlist {}===".format(playlist_title))
for video in actual_list:
    this = video["playlistVideoRenderer"]
    id = this["videoId"]
    title = this["title"]["runs"][0]["text"]
    duration = this["lengthText"]["simpleText"]

    print(id, title, duration)


print("\nDone")
print("elapsed: ", time.time() - first)
