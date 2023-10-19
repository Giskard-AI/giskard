from typing import Dict, Optional

import pytest

from giskard.ml_worker.stomp.constants import StompCommand
from giskard.ml_worker.stomp.parsing import StompFrame, StompProtocolError


@pytest.mark.parametrize(
    "stomp_frame,headers",
    [(StompFrame.CONNECT, {}), (StompFrame.CONNECT, {"host": "localhost"})],
)
def test_should_provide_all_mandatory_headers(stomp_frame: StompFrame, headers: Dict[str, str]):
    with pytest.raises(StompProtocolError) as exc_info:
        stomp_frame.build_frame(headers)
    assert "Missing mandatory headers in frame" in str(exc_info)


@pytest.mark.parametrize(
    "stomp_frame,headers,body",
    [
        (StompFrame.CONNECT, {"host": "localhost", "accept-version": "1.2"}, "aezaeaze"),
        (StompFrame.SUBSCRIBE, {"destination": "/toto", "id": "12345"}, "body"),
    ],
)
def test_should_not_have_body(stomp_frame: StompFrame, headers: Dict[str, str], body: str):
    with pytest.raises(StompProtocolError) as exc_info:
        stomp_frame.build_frame(headers, body)
    assert "Cannot have body for command" in str(exc_info)


@pytest.mark.parametrize(
    "stomp_frame,headers,body",
    [
        (
            StompFrame.SEND,
            {"destination": "/toto", "message-id": "1"},
            None,
        ),
        (
            StompFrame.SEND,
            {"destination": "/toto", "message-id": "1"},
            "azeaze",
        ),
        (StompFrame.MESSAGE, {"destination": "/toto", "message-id": "1", "subscription": "/toto"}, "body"),
        (StompFrame.MESSAGE, {"destination": "/toto", "message-id": "1", "subscription": "/toto"}, None),
        (StompFrame.ERROR, {}, "error"),
        (StompFrame.ERROR, {}, None),
    ],
)
def test_body_is_optional(stomp_frame: StompFrame, headers: Dict[str, str], body: str):
    frame = stomp_frame.build_frame(headers, body)
    assert frame.body == body
    if body is None:
        assert frame.body is None


@pytest.mark.parametrize(
    "raw_frame,command,headers,body",
    [
        (
            """CONNECT
host:localhost
accept-version:1.2
content-length:0

""",
            StompCommand.CONNECT,
            {"host": "localhost", "accept-version": "1.2", "content-length": "0"},
            None,
        ),
        (
            """SEND
destination:/home

some content""",
            StompCommand.SEND,
            {"destination": "/home"},
            b"some content",
        ),
        (
            """SUBSCRIBE
destination:/home
id:some-id

""",
            StompCommand.SUBSCRIBE,
            {"destination": "/home", "id": "some-id"},
            None,
        ),
        (
            """MESSAGE
destination:/home
content-type:text/plain
message-id:123
subscription:/toto

some content""",
            StompCommand.MESSAGE,
            {
                "destination": "/home",
                "content-type": "text/plain;charset=utf-8",
                "message-id": "123",
                "subscription": "/toto",
            },
            "some content",
        ),
        (
            """MESSAGE
destination:/home
content-type:application/json
message-id:123
subscription:/toto

["azea", 1n, true]""",
            StompCommand.MESSAGE,
            {
                "destination": "/home",
                "content-type": "application/json;charset=utf-8",
                "message-id": "123",
                "subscription": "/toto",
            },
            '["azea", 1n, true]',
        ),
    ],
)
def test_parsing(raw_frame: str, command: StompCommand, headers: Dict[str, str], body: Optional[str]):
    frame = StompFrame.from_string(raw_frame)
    assert frame.command == command
    assert frame.headers == headers
    assert frame.body == body


@pytest.mark.parametrize(
    "message,error",
    [
        (
            """MESSAGE
destination:/home
content-type:application/json
message-id:123
subscription:/toto
content-length:2

["azea", 1n, true]""",
            "Got data after content length",
        ),
        (
            """MESSAGE
destination:/home
content-type:application/json
message-id:123
subscription:/toto
content-length:20000

["azea", 1n, true]""",
            "Content length is longer than data",
        ),
        (
            """MESSAGE
destination:/home
content-type:application/json
message-id:123
subscription:/toto
content-length:azeazee

["azea", 1n, true]""",
            "Invalid content length given, expected an integer",
        ),
    ],
)
def test_invalid_content_length(message: str, error: str):
    with pytest.raises(StompProtocolError) as exc_info:
        StompFrame.from_string(message)
    assert error in str(exc_info)
