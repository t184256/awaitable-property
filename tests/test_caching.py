# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""Test awaitable_property functionality using a caching transformer."""

import asyncio
import dataclasses
import typing

import pytest

from awaitable_property import awaitable_property

_T = typing.TypeVar('_T')


class Cache:
    """A simplistic caching class for example purposes."""

    d: typing.ClassVar[dict[str, typing.Any]] = {}
    hits: typing.ClassVar[int] = 0
    misses: typing.ClassVar[int] = 0

    @classmethod
    async def cache(
        cls: type[typing.Self],
        obj: 'Example',
        corofunc: typing.Callable[
            ['Example'],
            typing.Coroutine[typing.Any, typing.Any, _T],
        ],
        attrname: str,
    ) -> _T:
        """Hooks into the property fetching process and performs caching."""
        # doesn't maintain per-object caches, but it's a simplistic test
        await asyncio.sleep(0)
        try:
            r = typing.cast(_T, cls.d[attrname])
        except KeyError:
            pass
        else:
            cls.hits += 1
            return r
        cls.misses += 1
        r = cls.d[attrname] = await corofunc(obj)
        return r


@dataclasses.dataclass(frozen=True)
class Example:
    """Example dataclass to have an awaitable property, no transformer."""

    value: int

    @awaitable_property(transform=Cache.cache)
    async def aprop(self: typing.Self) -> int:
        """Return the internal value, but it's async. Cached."""
        await asyncio.sleep(0)
        return self.value


@pytest.mark.asyncio()
async def test_caching() -> None:
    """Smoke-test awaitable_property on a regular class."""
    ex = Example(1)
    assert (Cache.hits, Cache.misses, Cache.d) == (0, 0, {})
    assert await ex.aprop == 1
    assert (Cache.hits, Cache.misses, Cache.d) == (0, 1, {'aprop': 1})
    assert await ex.aprop == 1
    assert (Cache.hits, Cache.misses, Cache.d) == (1, 1, {'aprop': 1})
    assert await ex.aprop == 1
    assert (Cache.hits, Cache.misses, Cache.d) == (2, 1, {'aprop': 1})
