from threading import ExceptHookArgs
import threading
from unittest.mock import patch



def test_excepthook_should_work():
    with patch("giskard.utils.analytics_collector.settings") as mock_settings:
        mock_settings.disable_analytics = False
        from giskard.utils.analytics_collector import settings

        assert not settings.disable_analytics
        if hasattr(threading, "__excepthook__"):  # only for python > 3.10
            assert threading.__excepthook__ != threading.excepthook

        args = ExceptHookArgs((type(RuntimeError), RuntimeError("Nothing"), None, None))
        threading.__excepthook__(args)
        threading.excepthook(args)
        # threading.excepthook("type", "value", "traceback", "thread")

        # def raiser():
        #     raise RuntimeError("Nothing much")

        # error = StringIO()
        # sys.stderr = error
        # thread: Thread = Thread(target=raiser)
        # with pytest.raises(RuntimeError) as exc_info:
        #     thread.run()
        #     thread.join(1)
        # assert str(exc_info) == ""
        # assert not thread.is_alive()
        # assert error.getvalue() == ""
        # error.close()
