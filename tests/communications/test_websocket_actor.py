from giskard.ml_worker import ml_worker, websocket
from giskard.ml_worker.websocket import listener
from giskard.ml_worker.websocket.action import MLWorkerAction

from tests.utils import MockedWebSocketMLWorker


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


def test_websocket_actor_get_info():
    internal_ml_worker = MockedWebSocketMLWorker(is_server=True)    # Internal worker
    external_ml_worker = MockedWebSocketMLWorker(is_server=False)   # External worker

    without_package_params = websocket.GetInfoParam(list_packages=False)
    with_package_params = websocket.GetInfoParam(list_packages=True)

    # Internal worker, without packages
    server_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(internal_ml_worker),
        params=without_package_params,
    )
    assert isinstance(server_ml_worker_info, websocket.GetInfo)
    assert server_ml_worker_info.isRemote == False
    assert server_ml_worker_info.mlWorkerId == ml_worker.INTERNAL_WORKER_ID
    assert 0 == len(server_ml_worker_info.installedPackages.values())

    # Internal worker, with packages
    server_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(internal_ml_worker),
        params=with_package_params,
    )
    assert isinstance(server_ml_worker_info, websocket.GetInfo)
    assert server_ml_worker_info.isRemote == False
    assert server_ml_worker_info.mlWorkerId == ml_worker.INTERNAL_WORKER_ID
    assert 0 != len(server_ml_worker_info.installedPackages.values())

    # External worker, without packages
    remote_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(external_ml_worker),
        params=without_package_params,
    )
    assert isinstance(remote_ml_worker_info, websocket.GetInfo)
    assert remote_ml_worker_info.isRemote == True
    assert remote_ml_worker_info.mlWorkerId == ml_worker.EXTERNAL_WORKER_ID
    assert 0 == len(remote_ml_worker_info.installedPackages.values())

    # External worker, with packages
    remote_ml_worker_info = listener.on_ml_worker_get_info(
        ml_worker=listener.MLWorkerInfo(external_ml_worker),
        params=with_package_params,
    )
    assert isinstance(remote_ml_worker_info, websocket.GetInfo)
    assert remote_ml_worker_info.isRemote == True
    assert remote_ml_worker_info.mlWorkerId == ml_worker.EXTERNAL_WORKER_ID
    assert 0 != len(remote_ml_worker_info.installedPackages.values())


def test_websocket_actor_stop_worker():
    reply = listener.on_ml_worker_stop_worker()
    assert isinstance(reply, websocket.Empty)
