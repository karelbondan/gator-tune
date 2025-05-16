from pytubefix import YouTube

def main(): 
    yt = YouTube("https://youtu.be/WEBMU9HSChg", use_po_token=True, allow_oauth_cache=False)
    print(yt.streams.get_audio_only())

if __name__ == "__main__":
    main()