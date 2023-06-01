from numpy.testing import assert_array_equal

from giskard.utils.analytics_collector import anonymize


def test_anonymize_simple():
    assert anonymize("clear text") == "3ede875cc5"
    assert anonymize(123) == "40bd001563"
    assert anonymize(1.23) == "1ee00eff57"
    assert anonymize(None) is None


def test_anonymize_complex():
    assert_array_equal(anonymize(["hello", "world"]), ["aaf4c61ddc", "7c211433f0"])
