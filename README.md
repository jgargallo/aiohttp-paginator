# aiohttp paginator: Async http client for paginated requests
Based on aiohttp, provides an http client to iterate over paginated requests.

## Usage
A PaginatorHelper is required to implement how pagination works for the specific endpoint.
This would be an example where pagination works by `max` and `offset` as part of the querystring,
where the total number of elements is placed in a response header:
```python
import aiohttppag
import math

class TbPaginatorHelper(aiohttppag.PaginatorHelper):

    def __init__(self, url, *, max_results=100, **kwargs):
        self.url = '{}?max={}'.format(url, max_results)
        self.max_results = max_results
        self.kwargs = kwargs

    def num_pages(self, response):
        return math.ceil(int(response.headers.get('X-totalCount', 0)) / self.max_results)

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


async def main():
    pag_helper = TbPaginatorHelper('http://api.example.com/events', max_results=10,
                                   auth=aiohttp.BasicAuth('user', 'pass'))

    async with aiohttppag.PaginatorClientSession() as session:
        async for response in session.pget(pag_helper, buffer_size=1, keep_order=False):
            print(await response.text())

if __name__ == '__main__':

    asyncio.get_event_loop()run_until_complete(main())
    
```