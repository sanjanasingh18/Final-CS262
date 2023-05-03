from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Pair(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class Dictionary(_message.Message):
    __slots__ = ["pairs"]
    PAIRS_FIELD_NUMBER: _ClassVar[int]
    pairs: _containers.RepeatedCompositeFieldContainer[Pair]
    def __init__(self, pairs: _Optional[_Iterable[_Union[Pair, _Mapping]]] = ...) -> None: ...

class List(_message.Message):
    __slots__ = ["link"]
    LINK_FIELD_NUMBER: _ClassVar[int]
    link: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, link: _Optional[_Iterable[str]] = ...) -> None: ...

class Data(_message.Message):
    __slots__ = ["hyperlinks", "players_freq", "weight"]
    HYPERLINKS_FIELD_NUMBER: _ClassVar[int]
    PLAYERS_FREQ_FIELD_NUMBER: _ClassVar[int]
    WEIGHT_FIELD_NUMBER: _ClassVar[int]
    hyperlinks: List
    players_freq: Dictionary
    weight: int
    def __init__(self, weight: _Optional[int] = ..., players_freq: _Optional[_Union[Dictionary, _Mapping]] = ..., hyperlinks: _Optional[_Union[List, _Mapping]] = ...) -> None: ...

class Message(_message.Message):
    __slots__ = ["message"]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...
