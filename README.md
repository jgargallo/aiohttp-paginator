# aiohttp paginator: Async http client for endpoints supporting pagination
Based on aiohttp, provides an http client to iterate over paginated requests.

## Usage
A PaginatorHelper is required to implement how pagination works for the specific endpoint.
This would be an example where pagination works by `max` and `offset` as part of the querystring,
where the total number of elements is placed in a response header:
```python
import aiohttppag
import math

class SpotifyPaginatorHelper(aiohttppag.PaginatorHelper):

    def __init__(self, url, *, limit=100, **kwargs):
        self.url = '{}?limit={}'.format(url, limit)
        self.max_results = limit
        self.kwargs = kwargs

    async def num_pages(self, response):
        first_page = await response.json()
        return math.ceil(int(next(iter(first_page.values()))['total']) / self.max_results)

    def next_url(self, page):
        return '{}&offset={}'.format(self.url, (page - 1) * self.max_results)

    def next_request_params(self, page):
        return self.kwargs
```
You need to implement the following methods:
- num_pages: total number of pages based on the response of the first request
- next_url: based on the page, provides the next url to be requested
- next_request_params: as next_url, provides the parameters that will be passed 
to [aiohttp.ClientSession.request](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession.request)


`aiohttppag.PaginatorClientSession` inherits from [aiohttp.ClientSession](http://aiohttp.readthedocs.io/en/stable/client_reference.html#aiohttp.ClientSession) and extends its functionality 
by adding `pget` and `ppost` which return an async generator that can be used like this:

```python
import aiohttppag
import asyncio
import aiohttp

SPOTIFY_TOKEN = 'Token'

async def main():
    conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
    pag_helper = SpotifyPaginatorHelper('https://api.spotify.com/v1/browse/categories',
                                        limit=10,
                                        headers={'Authorization': 'Bearer {}'.format(SPOTIFY_TOKEN)})

    async with aiohttppag.PaginatorClientSession(connector=conn) as session:
        async for response in session.pget(pag_helper, buffer_size=1, keep_order=False):
            categories = await response.json()
            list(map(lambda c: print(c['name']), categories['categories']['items']))

if __name__ == '__main__':

    asyncio.get_event_loop()run_until_complete(main())
    
```

## Known issues
Aiohttp paginator cannot be used if total number of results is not provided by the first request. I.e:
those providing `next` url without `total` results.