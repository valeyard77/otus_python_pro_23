#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper

def decorator(deco, func):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """
    ret = update_wrapper(deco, func)
    if hasattr(func, 'calls'):
        ret.calls = func.calls
    return ret

def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """

    def memo_wrapper(*args, **kwargs):
        if args in memo_wrapper.mem:
            print('recover from memo[', args, ']=', wrapper.mem[args])
            return memo_wrapper.mem[args]
        else:
            memo_wrapper.mem[args] = func(*args, **kwargs)
            print('save to memo[',args,']=', memo_wrapper.mem[args])
            return memo_wrapper.mem[args]

    memo_wrapper.mem = dict()
    return decorator(memo_wrapper, func)


@memo
# @countcalls
# @n_ary
def foo(a, b):
    return a + b

def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    # print("foo was called", foo.calls, "times")

    # print(bar(4, 3))
    # print(bar(4, 3, 2))
    # print(bar(4, 3, 2, 1))
    # print("bar was called", bar.calls, "times")
    #
    # print(fib.__doc__)
    # fib(3)
    # print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()