from giskard.ml_worker import websocket
from giskard.ml_worker.websocket import listener
from giskard.ml_worker.websocket.action import MLWorkerAction


NOT_USED_WEBSOCKET_ACTOR = [
    MLWorkerAction.generateQueryBasedSlicingFunction,
]


def test_all_registered_websocket_actor():
    # Any actor except not used should not be the default one
    for action in MLWorkerAction:
        if action not in NOT_USED_WEBSOCKET_ACTOR:
            assert listener.WEBSOCKET_ACTORS[action.name] != listener.websocket_log_actor


def test_websocket_actor_echo():
    msg = websocket.EchoMsg(msg="echo")
    reply = listener.echo(msg)
    assert isinstance(reply, websocket.EchoMsg)
    assert reply.msg == msg.msg
