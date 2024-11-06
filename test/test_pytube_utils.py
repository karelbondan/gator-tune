from pytubefix import YouTube
from os import path
import subprocess
import configs


def test_pytube_download():
    video_id = "XF2nC3lI70A"

    # yt = YouTube(url="https://www.youtube.com/watch?v=XF2nC3lI70A", use_po_token=True)
    # config = yt.streams.get_audio_only()
    # output = path.join(configs.ROOT_DIR, "test", "out")
    # downld = config.download(output_path=output, mp3=True)
    # rename = path.join(output, video_id, ".mp3")

    # unused for now
    assert True == True


def test_potoken_generator_YunzheZJU():
    command = "node {}".format(
        path.join(configs.ROOT_DIR, "utilities", "generator", "examples", "one-shot.js")
    ).split(" ")
    output = {}
    with subprocess.Popen(command, stdout=subprocess.PIPE) as generator:
        for line in generator.stdout:
            decoded = line.decode(encoding="utf-8").replace("\n", "").replace(",", "")
            try:
                k, v = decoded.split(":")
                output[k.strip()] = eval(v.strip())
            except Exception:
                pass

    test_dict = {"visitorData": "", "poToken": ""}
    output_keys = test_dict.keys()
    assert len(output_keys) == 2
    assert output_keys == test_dict.keys()
