import logging

import giskard


def test_giskard_log_level():
    assert (
        logging.getLogger(giskard.__name__).level == logging.INFO
    ), "giskard log level should be set to INFO when importing giskard"


def test_other_package_log_level_unset():
    assert (
        logging.getLogger(giskard.llm.client.__name__).level == logging.NOTSET
    ), "Non giskard package log level should't be touched by giskard (NOTSET)"


def test_root_log_level_default_warning():
    assert logging.getLogger().level == logging.WARNING, "Root package log level should be set to WARNING by default"
