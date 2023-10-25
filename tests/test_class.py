# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test awaitable_property functionality using a regular class."""

import asyncio
import inspect
import typing

import pytest

from awaitable_property import awaitable_property


async def my_transformer(
    obj: 'Example',
    corofunc: typing.Callable[
        ['Example'],
        typing.Coroutine[typing.Any, typing.Any, int],
    ],
    _unused_attrname: str,
) -> str:
    """Hooks into the property fetching process and allows customizing it."""
    await asyncio.sleep(0)
    return str(await corofunc(obj))


class Example:
    """Example class to have an awaitable property, no transformer."""

    value: int

    def __init__(self: typing.Self, val: int) -> None:
        """Construct an instance, store a value inside it."""
        self.value = val

    @awaitable_property
    async def aprop(self: typing.Self) -> int:
        """Return the internal value, but it's async. No transformer."""
        await asyncio.sleep(0)
        return self.value

    @awaitable_property(transform=my_transformer)
    async def aprop_transformed(self: typing.Self) -> int:
        """Return the internal value, but it's async. Has a transformer."""
        await asyncio.sleep(0)
        return self.value


@pytest.mark.asyncio()
async def test_simple() -> None:
    """Smoke-test awaitable_property on a regular class."""
    t = Example(1)
    assert (await t.aprop) == 1

    a = t.aprop
    assert inspect.isawaitable(a)
    assert (await a) == 1

    t = Example(1)
    assert (await t.aprop_transformed) == '1'


def test_misc() -> None:
    """Test access from a class instead of from an instance."""
    class_aprop = Example.aprop
    assert class_aprop.__class__.__name__ == 'AwaitableProperty'
    assert class_aprop.attrname == 'aprop'
