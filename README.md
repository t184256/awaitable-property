# awaitable-property

@awaitable_property decorator, lets you await obj.attrname

## Basic usage

``` python
class Example:
    @awaitable_property
    async def aprop(self):
        return await something(self)

ex = Example()
assert await ex.aprop == await something(ex)
```

## Transformer usage
``` python
async def transformer(obj, corofunc, attrname):
    await asyncio.sleep(0)
    return convert(await corofunc(obj))

class Example:
    @awaitable_property(transform=transformer)
    async def aprop(self):
        return await something(self)

ex = Example()
await ex.aprop  # await transformer(ex, unbound_aprop, 'aprop')
```

Can be used for good and evil,
refer to [tests/test_caching.py](tests/test_caching.py) for inspiration.
