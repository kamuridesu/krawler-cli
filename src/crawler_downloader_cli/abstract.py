import abc


class BaseDriver(abc.ABC):

    @abc.abstractmethod
    async def fetch_page(self, url: str) -> str: ...
