import functools

def test_func_arg():
    taker(functools.partial(process, a="pom"))

def process(a):
    print("process")
    print(a)

def taker(p):
    p()