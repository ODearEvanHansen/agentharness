import signal
signal.alarm(5)
from fib import fib
assert fib(10) == 55
assert fib(80) == 23416728348467685
print('ok')
