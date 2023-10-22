from typing import Dict, Optional, Set, Union

import re
from dataclasses import dataclass
from enum import Enum

from giskard.ml_worker.stomp.constants import (
    UTF_8,
    CommandType,
    HeaderType,
    StompCommand,
)
from giskard.ml_worker.stomp.utils import (
    read_line,
    transform_header_data,
    untransform_header_data,
    validate_header_part,
)

# A frame looks like
# COMMAND
# header1:value1
# header2:value2


# Body^@
class StompProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    command: StompCommand
    headers: Dict[str, str]
    body: Optional[Union[str, bytes]] = None

    def to_bytes(self) -> bytes:
        headers = [self.headers.items()]
        if self.command not in [StompCommand.CONNECT, StompCommand.CONNECTED]:
            headers = [f"{transform_header_data(k)}:{transform_header_data(v)}" for k, v in self.headers.items()]
        else:
            headers = [f"{k}:{v}" for k, v in self.headers.items()]
        if self.body is not None:
            body = self.body.encode(UTF_8)
            headers.append(f"{HeaderType.CONTENT_LENGTH}:{len(body)}")
        else:
            body = b""
            headers.append(f"{HeaderType.CONTENT_LENGTH}:0")
        # Todo : verify headers
        return (
            "\n".join(
                [
                    self.command.name,
                    "\n".join(headers),
                    "\n",
                ]
            ).encode(UTF_8)
            + body
            # + NULL_BYTE
        )


class FrameParser:
    def __init__(self, frame: str) -> None:
        self.to_parse = frame
        self.command: Optional[StompCommand] = None
        self.headers: Dict[str, str] = dict()
        self.body: Optional[str] = None
        self.encoding: Optional[str] = None
        self.content_type: Optional[str] = None
        self.content_length: Optional[int] = None
        self.known_headers: Set[str] = set()

    @classmethod
    def parse(cls, frame: Union[str, bytes]) -> Frame:
        if isinstance(frame, bytes):
            frame = frame.decode(UTF_8)
        return cls(frame).read_command().read_headers().read_body().build_frame()

    def read_command(self) -> "FrameParser":
        # Read command
        command, leftover = read_line(self.to_parse)
        self.to_parse = leftover
        try:
            self.command = StompCommand[command]
        except KeyError as e:
            raise StompProtocolError(f"{command} not in allowed values of ServerCommand: {list(StompCommand)}") from e

        return self

    def read_headers(self) -> "FrameParser":
        # Reading headers
        should_untransform = self.command not in [StompCommand.CONNECT, StompCommand.CONNECTED]

        header_line, self.to_parse = read_line(self.to_parse)
        while header_line != "":
            header_splitted = header_line.split(":", 1)
            if len(header_splitted) == 1:
                raise StompProtocolError(f"Header should contains : to separate key and value, got'{header_line}'")
            if should_untransform:
                header_name, header_value = map(untransform_header_data, map(validate_header_part, header_splitted))
            else:
                header_name, header_value = header_splitted
            header_name = header_name.casefold()
            if header_name in self.known_headers:
                continue

            if header_name == HeaderType.CONTENT_TYPE:
                encoding = None
                if ";" in header_value:
                    header_value, charset = header_value.split(";", 1)
                    name, encoding = charset.split("=", 1)
                    if name != "charset":
                        raise StompProtocolError(
                            f"Unexpected value in content type after, expected charset, got {name}"
                        )
                if encoding is None and (
                    header_value.startswith("text/") or header_value in ["application/json", "application/xml"]
                ):
                    encoding = UTF_8
                self.encoding = encoding
                self.content_type = header_value.casefold()
                self.headers[HeaderType.CONTENT_TYPE] = self.content_type
                if self.encoding is not None:
                    self.headers[HeaderType.CONTENT_TYPE] += f";charset={self.encoding}"
            elif header_name == HeaderType.CONTENT_LENGTH:
                try:
                    self.content_length = int(header_value)
                    self.headers[HeaderType.CONTENT_LENGTH] = header_value
                except ValueError as e:
                    raise StompProtocolError(
                        f"Invalid content length given, expected an integer, got {header_value}"
                    ) from e
            else:
                self.headers[header_name] = header_value
            self.known_headers.add(header_name)
            # Read next line
            header_line, self.to_parse = read_line(self.to_parse)
        return self

    def read_body(self) -> "FrameParser":
        # Decode data from utf-8
        raw_data = self.to_parse.encode(encoding=UTF_8)
        if self.content_length is not None and self.content_length > len(raw_data):
            raise StompProtocolError(
                f"Content length is longer than data: '{self.content_length}' >  '{len(raw_data)}'"
            )
        if self.content_length is None:
            self.content_length = len(raw_data)

        footer = raw_data[self.content_length + 1 :].decode(UTF_8)
        if re.sub("\n|\r", "", footer) != "":
            raise StompProtocolError(f"Got data after content length, '{footer}'")

        if self.encoding is None:
            # Assuming binary type ?
            self.body = raw_data[: self.content_length]
        else:
            self.body = raw_data[: self.content_length].decode(self.encoding)
        if len(self.body) == 0:
            self.body = None
        return self

    def build_frame(self):
        return Frame(body=self.body, command=self.command, headers=self.headers)


class StompFrame(Enum):
    def __init__(
        self, command: StompCommand, command_type: CommandType, mandatory_headers: Set[HeaderType], allow_body=False
    ):
        super().__init__()
        self._command = command
        self._command_type = command_type
        self._mandatory_headers = mandatory_headers
        self._allow_body = allow_body

    CONNECT = (StompCommand.CONNECT, CommandType.CLIENT, {HeaderType.ACCEPT_VERSION, HeaderType.HOST})
    SEND = (StompCommand.SEND, CommandType.CLIENT, {HeaderType.DESTINATION}, True)
    SUBSCRIBE = (StompCommand.SUBSCRIBE, CommandType.CLIENT, {HeaderType.DESTINATION, HeaderType.ID})
    UNSUBSCRIBE = (StompCommand.UNSUBSCRIBE, CommandType.CLIENT, {HeaderType.ID})
    ACK = (StompCommand.ACK, CommandType.CLIENT, {HeaderType.ID})
    NACK = (StompCommand.NACK, CommandType.CLIENT, {HeaderType.ID})
    BEGIN = (StompCommand.BEGIN, CommandType.CLIENT, {HeaderType.TRANSACTION})
    COMMIT = (StompCommand.COMMIT, CommandType.CLIENT, {HeaderType.TRANSACTION})
    ABORT = (StompCommand.ABORT, CommandType.CLIENT, {HeaderType.TRANSACTION})
    DISCONNECT = (StompCommand.DISCONNECT, CommandType.CLIENT, set())

    CONNECTED = (StompCommand.CONNECTED, CommandType.SERVER, {HeaderType.VERSION})
    MESSAGE = (
        StompCommand.MESSAGE,
        CommandType.SERVER,
        {HeaderType.DESTINATION, HeaderType.SUBSCRIPTION, HeaderType.MESSAGE_ID},
        True,
    )
    RECEIPT = (StompCommand.RECEIPT, CommandType.SERVER, {HeaderType.RECEIPT_ID})
    ERROR = (StompCommand.ERROR, CommandType.SERVER, set(), True)

    def is_client_command(self) -> bool:
        return self._command_type == CommandType.CLIENT

    def validate(self, frame: Frame):
        missing_headers = self._mandatory_headers - set(frame.headers.keys())
        if len(missing_headers) > 0:
            raise StompProtocolError(f"Missing mandatory headers in frame, {missing_headers}")
        if not self._allow_body and frame.body is not None:
            raise StompProtocolError(f"Cannot have body for command {frame.command}, got '{frame.body}'")

    @classmethod
    def from_string(cls, raw_frame: Union[str, bytes]) -> Frame:
        frame = FrameParser.parse(raw_frame)
        cls[frame.command].validate(frame)
        return frame

    def build_frame(
        self,
        headers: Dict[Union[str, HeaderType], str],
        body: Optional[Union[str, bytes]] = None,
    ) -> Frame:
        new_frame = Frame(
            command=self._command,
            headers={k.value if isinstance(k, HeaderType) else k: v for k, v in headers.items()},
            body=body,
        )
        self.validate(new_frame)
        return new_frame
