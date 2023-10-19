# https://stomp.github.io/stomp-specification-1.2.html#STOMP_Frames

# NULL                = <US-ASCII null (octet 0)>
# LF                  = <US-ASCII line feed (aka newline) (octet 10)>
# CR                  = <US-ASCII carriage return (octet 13)>
# EOL                 = [CR] LF
# OCTET               = <any 8-bit sequence of data>

# frame-stream        = 1*frame

# frame               = command EOL
#                       *( header EOL )
#                       EOL
#                       *OCTET
#                       NULL
#                       *( EOL )

# command             = client-command | server-command

# client-command      = "SEND"
#                       | "SUBSCRIBE"
#                       | "UNSUBSCRIBE"
#                       | "BEGIN"
#                       | "COMMIT"
#                       | "ABORT"
#                       | "ACK"
#                       | "NACK"
#                       | "DISCONNECT"
#                       | "CONNECT"
#                       | "STOMP"

# server-command      = "CONNECTED"
#                       | "MESSAGE"
#                       | "RECEIPT"
#                       | "ERROR"

# header              = header-name ":" header-value
# header-name         = 1*<any OCTET except CR or LF or ":">
# header-value        = *<any OCTET except CR or LF or ":">


import re
from enum import Enum

NULL_BYTE = b"\x00"
LF = "\n"
CR = "\r"
# EOL = f"{LF}*{CR}"
CR_LITTERAL = "\\r"
LF_LITTERAL = "\\n"
UTF_8 = "utf-8"

# \r (octet 92 and 114) translates to carriage return (octet 13)
# \n (octet 92 and 110) translates to line feed (octet 10)
# \c (octet 92 and 99) translates to : (octet 58)
# \\ (octet 92 and 92) translates to \ (octet 92)

HEADER_TRANSFORMATIONS = {"cr": ("\\r", CR), "lf": ("\\n", LF), "colon": ("\\c", ":"), "backslash": ("\\\\", "\\")}
REGEX_ENCODE = re.compile(
    "|".join([f"(?P<{name}>{re.escape(to_escape)})" for name, (_, to_escape) in HEADER_TRANSFORMATIONS.items()])
)
REGEX_DECODE = re.compile(
    "|".join([f"(?P<{name}>{re.escape(to_escape)})" for name, (to_escape, _) in HEADER_TRANSFORMATIONS.items()])
)


class HeaderType(str, Enum):
    CONTENT_TYPE = "content-type"
    CONTENT_LENGTH = "content-length"
    HOST = "host"
    HEART_BEAT = "heart-beat"
    DESTINATION = "destination"
    ID = "id"
    ACCEPT_VERSION = "accept-version"
    LOGIN = "login"
    PASSCODE = "passcode"
    VERSION = "version"
    TRANSACTION = "transaction"
    ACK = "ack"
    RECEIPT = "receipt"
    SUBSCRIPTION = "subscription"
    MESSAGE_ID = "message-id"
    RECEIPT_ID = "receipt-id"


class CommandType(str, Enum):
    CLIENT = "CLIENT"
    SERVER = "SERVER"


class StompCommand(str, Enum):
    SEND = "SEND"
    SUBSCRIBE = "SUBSCRIBE"
    UNSUBSCRIBE = "UNSUBSCRIBE"
    BEGIN = "BEGIN"
    COMMIT = "COMMIT"
    ABORT = "ABORT"
    ACK = "ACK"
    NACK = "NACK"
    DISCONNECT = "DISCONNECT"
    CONNECT = "CONNECT"
    STOMP = "STOMP"

    CONNECTED = "CONNECTED"
    MESSAGE = "MESSAGE"
    RECEIPT = "RECEIPT"
    ERROR = "ERROR"


class AckType(str, Enum):
    AUTO = "auto"
    CLIENT = "client"
    CLIENT_INDIVIDUAL = "client-individual"
