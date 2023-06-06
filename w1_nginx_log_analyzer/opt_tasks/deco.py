#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper


def disable(func):
    """
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:
    memo = disable
    """

    def disable_wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return decorator(disable_wrapper, func)


def decorator(deco, func):
    """
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    """
    r = update_wrapper(deco, func)
    return r


def countcalls(func):
    """Decorator that counts calls made to the function decorated."""

    ## не получается сделать без дополнительного элемента. листа, dict, без разницы
    ## если декоратор memo стоит первым в вызове(и соотвествено инициализируется на уровне вызова import скрипта),
    # то мы получаем значение, которое будет стоять в корне верхнеуровневой функции countcalls, например count_wrapper.calls = 1
    #

    def count_wrapper(*args, **kwargs):
        count_wrapper.calls['count'] += 1
        return func(*args, **kwargs)

    count_wrapper.calls = {"count": 1}
    return decorator(count_wrapper, func)


def memo(func):
    """
    Memoize a function so that it caches all return values for
    faster future lookups.
    """

    def memo_wrapper(*args, **kwargs):
        if args in memo_wrapper.mem:
            print(f" <- recover from memo['{args}'] = {memo_wrapper.mem[args]}")
            return memo_wrapper.mem[args]
        else:
            r = func(*args, **kwargs)
            memo_wrapper.mem[args] = r
            print(f" -> save to memo['{args}'] = {memo_wrapper.mem[args]}")
            return r

    memo_wrapper.mem = {}
    return decorator(memo_wrapper, func)


def n_ary(func):
    """
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    """

    def nary_wrapper(*args):
        if len(args) == 1:
            return args[0]
        elif len(args) == 2:
            return func(args[0], args[1])
        else:
            return func(args[0], nary_wrapper(*args[1:]))

    return decorator(nary_wrapper, func)


def trace(trace_symbols):
    """Trace calls made to function decorated.
    @trace("____")
    def fib(n):
        ....

    fib(3)
     --> fib(3)
    ____ --> fib(2)
    ________ --> fib(1)
    ________ <-- fib(1) == 1
    ________ --> fib(0)
    ________ <-- fib(0) == 1
    ____ <-- fib(2) == 2
    ____ --> fib(1)
    ____ <-- fib(1) == 1
     <-- fib(3) == 3

    """

    def decorate(func):
        def trace_wrapper(*args):
            print(trace_symbols * trace_wrapper.count, ' --> ', func.__name__, '(', *args, ')', sep='')
            trace_wrapper.count += 1
            r = func(*args)
            trace_wrapper.count -= 1
            print(trace_symbols * trace_wrapper.count, ' <-- ', func.__name__, '(', *args, ')', ' == ', r, sep='')
            return r

        trace_wrapper.count = 0
        return decorator(trace_wrapper, func)

    return decorate


# memo = disable

@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@trace("---")
@memo
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n - 1) + fib(n - 2)


def main():
    print('=================FOO==================')
    print('=====@memo, @countcalls, @n_ary=======')
    print('======================================')
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls['count'], "times")

    print('===============BAR====================')
    print('=====@countcalls, @memo , @n_ary======')
    print('======================================')
    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls['count'], "times")

    print('=================FIB==================')
    print('=====@countcalls, @trace, @memo=======')
    print('======================================')
    print(fib.__doc__)
    fib(3)
    print(fib.calls['count'], 'calls made')


if __name__ == '__main__':
    main()
