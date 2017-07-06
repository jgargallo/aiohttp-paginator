import abc

import aiohttp
import asyncio

DEFAULT_BUFFER_SIZE = 10


class PaginatorClientSession(aiohttp.ClientSession):
    """First-class interface for making paginated HTTP requests."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def pget(self, pag_helper, *, buffer_size=DEFAULT_BUFFER_SIZE, keep_order=True):
        """

        :param pag_helper: PaginatorHelper to define pagination
        :param buffer_size: number of simultaneous requests
        :param keep_order: returns pages keeping order.
        :return: aiohttp.ClientResponse
        """
        return _Paginator(self, 'get', pag_helper, buffer_size, keep_order)

    def ppost(self, pag_helper, *, buffer_size=DEFAULT_BUFFER_SIZE, keep_order=True):
        """

        :param pag_helper: PaginatorHelper to define pagination
        :param buffer_size: number of simultaneous requests
        :param keep_order: returns pages keeping order.
        :return: aiohttp.ClientResponse
        """
        return _Paginator(self, 'post', pag_helper, buffer_size, keep_order)


class _Paginator:

    def __init__(self, session, method, pag_helper, buffer_size, keep_order):
        self.pag_helper = pag_helper
        self.session = session
        self.method = getattr(self.session, method)
        self.buffer_size = buffer_size
        self.keep_order = keep_order

        self.expected_page = 2
        self.last_enqueued_page = 2
        self.buffered_results = {}
        self.num_pages = None

        self.done = set()
        self.not_done = set()

    async def __aiter__(self):
        return self

    async def _fetch(self, page=1):
        async with self.method(self.pag_helper.next_url(page),
                               **self.pag_helper.next_request_params(page)) as response:
            return [response, page]

    async def _create_next_tasks(self):
        next_enqueued_page = min(self.last_enqueued_page + self.buffer_size, self.num_pages + 1)
        self.not_done |= {self._fetch(i) for i in range(self.last_enqueued_page, next_enqueued_page)}
        self.last_enqueued_page = next_enqueued_page

    async def _get_first_page(self):
        res = await self._fetch()
        self.num_pages = self.pag_helper.num_pages(res[0])

        await self._create_next_tasks()

        return res[0]

    async def __anext__(self):
        if self.num_pages is None:
            return await self._get_first_page()

        while True:
            if self.keep_order and self.expected_page in self.buffered_results:
                buffered_result = self.buffered_results.pop(self.expected_page)
                self.expected_page += 1
                return buffered_result

            if not self.done and self.not_done:
                self.done, self.not_done = await asyncio.wait(
                    self.not_done, return_when=asyncio.FIRST_COMPLETED)

                await self._create_next_tasks()

            if not self.done and not self.not_done:
                if len(self.buffered_results) > 0:
                    continue
                raise StopAsyncIteration

            x = self.done.pop().result()

            if not self.keep_order:
                return x[0]
            else:
                self.buffered_results[x[1]] = x[0]


class PaginatorHelper(object, metaclass=abc.ABCMeta):
    """A paginator helper is required to implement how pagination works"""

    @abc.abstractmethod
    def num_pages(self, response):
        """

        :param response: aiohttp.ClientResponse from the first requested page
        :return: Total number of pages
        """
        raise NotImplementedError('get_num_pages must be implemented to use this base class')

    @abc.abstractmethod
    def next_url(self, page):
        """

        :param page: page number
        :return: Next url to be requested based on the provided page
        """
        raise NotImplementedError('next_url must be implemented to use this base class')

    @abc.abstractmethod
    def next_request_params(self, page):
        """

        :param page: page number
        :return: Next request attributes based on the provided page
        """
        raise NotImplementedError('next_request_attrs must be implemented to use this base class')
