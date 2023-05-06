from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class Data(_message.Message):
    __slots__ = ["hyperlinks", "players_freq", "weight"]
    HYPERLINKS_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FREQ_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    hyperlinks: str
    players_freq: str
    weight: int
    def __init__(self, weight: _Optional[int] = ..., players_freq: _Optional[str] = ..., hyperlinks: _Optional[str] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
