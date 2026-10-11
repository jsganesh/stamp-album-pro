"""THROWAWAY: fails on purpose to check annotations on real CI. Reverted in this PR."""

import pytest


def test_demo_plain_failure():
    frame_w = 19
    assert frame_w == 21, "frame too narrow (deliberate CI check)"


@pytest.mark.parametrize("label", ["a,b:c 100%"])
def test_demo_escaped_name(label):
    assert label == "x", "second line follows\nhere it is"
