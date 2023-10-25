# SPDX-FileCopyrightText: 2023 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: GPL-3.0

"""awaitable-property.

@awaitable_property decorator, lets you await obj.attrname
"""

from awaitable_property._awaitable_property import awaitable_property

__all__ = ['awaitable_property']
