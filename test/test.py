from urllib import parse, request
from bs4 import BeautifulSoup
import requests
import re
import json

# hello = {1: {"queue": [1, 2, 3]}, 2: "hello"}
# me = hello[1]
# queue = me["queue"]
# print(queue)
# queue.pop()
# print(queue)
# queue.append("world")
# print(hello[1]["queue"])

headers = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246"}
query = parse.urlencode({"search_query": "a sunny day is watching over you 8 bit"})
result = requests.get(url="https://www.youtube.com/results?" + query, headers=headers)

soup = BeautifulSoup(result.content, features='html5lib')

# with open("test.txt", "w") as output: 
#     a = soup.prettify()
#     output.write(a)

videos = {}

with open("test.txt", "r") as scraped: 
    # read = scraped.readlines()
    # read = "\n".join(read)
    # soup = BeautifulSoup(read, features='html5lib')
    
    test = soup.find_all("script")
    
    for i in test: 
        if "ytInitialData" in str(i):
            data = re.findall(r"(?<=var ytInitialData = ).+(?=;</script>)", str(i))
            
            with open("formatted.txt", "w") as formatted:
                formatted.write(data[0])
                videos = json.loads(data[0])
                
            break

videos = videos \
    ['contents'] \
    ['twoColumnSearchResultsRenderer'] \
    ['primaryContents'] \
    ['sectionListRenderer'] \
    ['contents'][0] \
    ['itemSectionRenderer'] \
    ['contents']

print("===RESULTS===")
for index, video in enumerate(videos):
    if index > 10: break
    try: 
        this = video['videoRenderer']
        title = this['title']['runs'][0]['text']
        video_id = this['videoId']
        
        print(index + 1, title, video_id)
    except KeyError:
        continue
        
    
    # out = ""
    # for index, i in enumerate(test):
    #     out += f"====={index}=====\n"
    #     out += str(i) + "\n"
        
    # with open("hadeh.txt", "w") as hadeh:
    #     hadeh.write(out)
