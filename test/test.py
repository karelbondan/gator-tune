from urllib import parse, request
from bs4 import BeautifulSoup
import requests
import re
import json

# this file's on crack man please leave 

# hello = {1: {"queue": [1, 2, 3]}, 2: "hello"}
# me = hello[1]
# queue = me["queue"]
# print(queue)
# queue.pop()
# print(queue)
# queue.append("world")
# print(hello[1]["queue"])

# headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"
# }
headers = {
    "User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36",
    "Range": "bytes=0-1023"
}
query = parse.urlencode({"search_query": "a sunny day is watching over you 8 bit"})
result = requests.get(url="https://www.youtube.com/results?" + query, headers=headers)

soup = BeautifulSoup(result.content, features="html5lib")

# with open("test.txt", "w") as output:
#     a = soup.prettify()
#     output.write(a)

# videos = {}

# with open("test.txt", "r") as scraped:
#     # read = scraped.readlines()
#     # read = "\n".join(read)
#     # soup = BeautifulSoup(read, features='html5lib')

#     test = soup.find_all("script")

#     for i in test:
#         if "ytInitialData" in str(i):
#             data = re.findall(r"(?<=var ytInitialData = ).+(?=;</script>)", str(i))

#             with open("formatted.txt", "w") as formatted:
#                 formatted.write(data[0])
#                 videos = json.loads(data[0])

#             break

# videos = videos \
#     ['contents'] \
#     ['twoColumnSearchResultsRenderer'] \
#     ['primaryContents'] \
#     ['sectionListRenderer'] \
#     ['contents'][0] \
#     ['itemSectionRenderer'] \
#     ['contents']

# print("===RESULTS===")
# for index, video in enumerate(videos):
#     if index > 10: break
#     try:
#         this = video['videoRenderer']
#         title = this['title']['runs'][0]['text']
#         video_id = this['videoId']

#         print(index + 1, title, video_id)
#     except KeyError:
#         continue


# out = ""
# for index, i in enumerate(test):
#     out += f"====={index}=====\n"
#     out += str(i) + "\n"

# with open("hadeh.txt", "w") as hadeh:
#     hadeh.write(out)


url = "https://rr3---sn-xmjxajvh-jb3zz.googlevideo.com/videoplayback?expire=1757966075&ei=mxrIaK3BBp6L1d8P1svT-As&ip=140.213.163.25&id=o-ABF4UsYTOXoM6p8Yece4qjEUPQHvjtS9HMInPep4c560&itag=140&source=youtube&requiressl=yes&xpc=EgVo2aDSNQ%3D%3D&met=1757944475%2C&mh=XS&mm=31%2C26&mn=sn-xmjxajvh-jb3zz%2Csn-30a7yner&ms=au%2Conr&mv=m&mvi=3&pl=24&rms=au%2Cau&initcwndbps=412500&bui=ATw7iSWclj2Hzp0h1oI8oUhfaZK9QFjRCwUOcg_AYzHsMkGjJ2a6aiioNtpj6I7JicqtAUNkFQhEvN-V&spc=hcYD5ZTXqWmb9G0wE9LRr-qyVFY1dTvkA2CZeoIDgZ9QBF2dM9GI5p-k&vprv=1&svpuc=1&mime=audio%2Fmp4&rqh=1&gir=yes&clen=3206254&dur=198.066&lmt=1726259259314584&mt=1757944110&fvip=1&keepalive=yes&fexp=51552689%2C51565115%2C51565681%2C51580968&c=ANDROID_VR&txp=4532434&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cxpc%2Cbui%2Cspc%2Cvprv%2Csvpuc%2Cmime%2Crqh%2Cgir%2Cclen%2Cdur%2Clmt&sig=AJfQdSswRgIhAMoeoCq08GRzPw1wpD1nDWPwur9HC3fBaqc-p6BD48u4AiEAx7tPDE5pF65FpsKjRcJJOhsFiObTvMSuPLPgIZcXocM%3D&lsparams=met%2Cmh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Crms%2Cinitcwndbps&lsig=APaTxxMwRQIgRG7fizscOf5OxsZqwvKTmPSdu41-3VqDArXxo8I4qMECIQDlQR_wKUP1nijgYrbIcN2yXK4OIQpwszD4lE9XFhYZmg%3D%3D&pot=MnRoRIrrznMvSGh8dgHk2kNMhqiGMVDUzrwk5a5enewsF3Hb2vL0Mk4gWyW-oz7bSAtdTDa00awVO-3XFkb-MWyIdkxnB89u4eozzM562r-slA9GzN5mTvCw_UciO7DAhAElIQ4HacLnd3p9Ajl9f8bF1MbliA%3D%3D"
url_valid = requests.get(url=url, headers=headers, timeout=(5, 5))
print(url_valid)
