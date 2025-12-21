from pytubefix import YouTube


def main():
    yt = YouTube(
        "https://youtu.be/WEBMU9HSChg", use_po_token=True, allow_oauth_cache=False
    )
    rs = yt.streams.get_audio_only()
    assert rs
    print(rs.url)


if __name__ == "__main__":
    main()
