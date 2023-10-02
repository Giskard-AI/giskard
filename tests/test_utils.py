from numpy.testing import assert_array_equal

from giskard.utils.analytics_collector import anonymize


def test_anonymize_simple():
    assert anonymize("clear text") == "3ede875cc56517b8"
    assert anonymize(123) == "40bd001563085fc3"
    assert anonymize(1.23) == "1ee00eff570301a5"
    assert anonymize(None) is None


def test_anonymize_complex():
    assert_array_equal(anonymize(["hello", "world"]), ["aaf4c61ddcc5e8a2", "7c211433f0207159"])
