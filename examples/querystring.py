import aiohttppag
import asyncio
import aiohttp
import socket
import math

SPOTIFY_TOKEN = 'Token'


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

    loop = asyncio.get_event_loop()
    loop.set_debug(enabled=True)
    loop.run_until_complete(main())

