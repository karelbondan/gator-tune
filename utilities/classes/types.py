from typing import Optional, TypedDict


class Queue(TypedDict):
    id: str
    title: str
    duration: str
    source: str


class PlaylistQueue(TypedDict):
    id: str
    title: str
    duration: str


class Song(TypedDict):
    id: str
    url: Optional[str]
    title: str
    queue: Optional[list[PlaylistQueue]]
    duration: str
    playlist_title: Optional[str]
