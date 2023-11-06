# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Main module of awaitable_property."""

import functools
import inspect
import typing

_T_obj = typing.TypeVar('_T_obj')
_T_get = typing.TypeVar('_T_get')  # what wrapped coroutine returns
_T_ret = typing.TypeVar('_T_ret')  # what we return after the transformation

_Coroutine = typing.Coroutine[typing.Any, typing.Any, _T_get]
_Corofunc = typing.Callable[[_T_obj], _Coroutine[_T_get]]
_Transformer = typing.Callable[
    [_T_obj, _Corofunc[_T_obj, _T_get], str],
    _Coroutine[_T_ret],
]


async def no_transform(
    obj: _T_obj,
    corofunc: _Corofunc[_T_obj, _T_get],
    attrname: str,  # noqa: ARG001
) -> _T_get:
    return await corofunc(obj)


class AwaitableProperty(typing.Generic[_T_obj, _T_get, _T_ret]):
    __slots__ = ('__doc__', 'attrname', 'bound_cls', '__wrapped__', 'wrapper')
    attrname: str | None  # binds later
    bound_cls: type[_T_obj] | None  # binds later
    __wrapped__: _Corofunc[_T_obj, _T_get]
    wrapper: _Corofunc[_T_obj, _T_ret]

    def __init__(
        self: typing.Self,
        corofunc: _Corofunc[_T_obj, _T_get],
        transformer: _Transformer[_T_obj, _T_get, _T_ret],
    ) -> None:
        self.attrname = None
        self.__wrapped__ = corofunc
        assert inspect.iscoroutinefunction(corofunc)  # noqa: S101
        self.__doc__ = f'[awaitable property] {corofunc.__doc__}'

        @functools.wraps(self.__wrapped__)
        async def wrapper(obj: _T_obj) -> _T_ret:
            assert self.attrname is not None  # noqa: S101
            return await transformer(obj, self.__wrapped__, self.attrname)

        wrapper.__name__ = corofunc.__name__ + '.wrapper'
        wrapper.__qualname__ = corofunc.__qualname__ + '.wrapper'
        wrapper.__doc__ = f'[awaitable property wrapper] {corofunc.__doc__}'

        self.wrapper = wrapper

    # on attaching to class
    def __set_name__(
        self: typing.Self,
        bound_cls: type[_T_obj],
        attrname: str,
    ) -> None:
        self.bound_cls = bound_cls
        self.attrname = attrname

    @typing.overload  # .__get__(obj) invocation from an instance
    def __get__(
        self: typing.Self,
        obj: _T_obj,
        objtype: type[_T_obj],
    ) -> typing.Awaitable[_T_ret]: ...  # overload

    @typing.overload  # .__get__(None, cls) invocation from a class
    def __get__(
        self: typing.Self,
        obj: None,
        objtype: type,  # we don't care which type, we don't use it
    ) -> typing.Self: ...  # overload

    def __get__(
        self: typing.Self,
        obj: _T_obj | None,
        objtype: type[_T_obj] | None = None,
    ) -> typing.Awaitable[_T_ret] | typing.Self:
        # .__get__(None, cls) invocation from a class
        if obj is None:
            return self

        # .__get__(obj) invocation from an instance
        assert self.attrname is not None  # noqa: S101
        assert self.bound_cls  # noqa: S101
        assert obj is not None  # noqa: S101
        assert objtype is not None  # noqa: S101
        assert isinstance(obj, self.bound_cls)  # noqa: S101
        assert objtype is self.bound_cls  # noqa: S101

        return self.wrapper(obj)


@typing.overload  # for decorating with awaitable_property(transform=...)
def awaitable_property(
    *,
    transform: _Transformer[_T_obj, _T_get, _T_ret],
) -> typing.Callable[
    [_Corofunc[_T_obj, _T_get]],
    AwaitableProperty[_T_obj, _T_get, _T_ret],
]: ...  # overload


@typing.overload  # for decorating with awaitable_property, _T_get = _T_ret
def awaitable_property(
    corofunc: _Corofunc[_T_obj, _T_get],
) -> AwaitableProperty[_T_obj, _T_get, _T_get]: ...  # overload


# I want to be able to later extend it with parameters, so, two forms
def awaitable_property(
    corofunc: _Corofunc[_T_obj, _T_get] | None = None,
    *,
    transform: _Transformer[_T_obj, _T_get, _T_ret] | None = None,
) -> (
    AwaitableProperty[_T_obj, _T_get, _T_get]
    | typing.Callable[
        [_Corofunc[_T_obj, _T_get]],
        AwaitableProperty[_T_obj, _T_get, _T_ret],
    ]
):
    """Mark an `async def` method as an awaitable property.

    The decorated coroutine method must take `self` as the only argument.

    `@awaitable_property(transform=...)` can be specified
    to customize the property access (e.g., cache it).

    Transformer example:
    ```
    async def my_transformer(
        obj: 'MyClass',
        corofunc: typing.Callable[
            ['MyClass'],
            typing.Coroutine[typing.Any, typing.Any, OriginalType],
        ],
        attrname: str,
    ) -> TransformedType:
        await asyncio.sleep(0)
        return original_to_transformed(await corofunc(obj))
    ```

    Specifying setters and deleters is not supported.
    """
    if corofunc is None and transform is not None:
        return _mk_awaitable_property(transform)
    assert corofunc is not None  # noqa: S101
    assert transform is None  # noqa: S101
    return _mk_awaitable_property(no_transform)(corofunc)


def _mk_awaitable_property(
    transformer: _Transformer[_T_obj, _T_get, _T_ret],
) -> typing.Callable[
    [_Corofunc[_T_obj, _T_get]],
    AwaitableProperty[_T_obj, _T_get, _T_ret],
]:
    def wrapper(
        corofunc: _Corofunc[_T_obj, _T_get],
    ) -> 'AwaitableProperty[_T_obj, _T_get, _T_ret]':
        return AwaitableProperty(corofunc, transformer=transformer)

    return wrapper


__all__ = ['awaitable_property', 'AwaitableProperty']
