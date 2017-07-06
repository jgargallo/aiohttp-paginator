import aiohttppag
import asyncio
import aiohttp
import socket
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

async def main():
    conn = aiohttp.TCPConnector(family=socket.AF_INET, verify_ssl=False)
    pag_helper = TbPaginatorHelper('https://api.example.com/events', max_results=10,
                                   auth=aiohttp.BasicAuth('user', 'pass'))

    async with aiohttppag.PaginatorClientSession(connector=conn) as session:
        async for response in session.pget(pag_helper, buffer_size=1, keep_order=False):
            print(await response.text())
            print('.'*100)
            print(response.headers)
            print('-'*100)

if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    loop.run_until_complete(main())

