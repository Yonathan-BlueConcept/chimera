# test_script.py
from script import add, multiply

def test_add_logic():
    # If add(2, 3) doesn't equal 5, this test fails
    assert add(2, 3) == 5

def test_multiply_logic():
    assert multiply(10, 2) == 20