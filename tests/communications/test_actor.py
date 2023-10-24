
from giskard.ml_worker.websocket import EchoMsg
from giskard.ml_worker.websocket.listener import echo


def test_actor_echo():
    msg = EchoMsg(msg="echo")
    reply = echo(msg)
    assert isinstance(reply, EchoMsg)
    assert reply.msg == msg.msg
