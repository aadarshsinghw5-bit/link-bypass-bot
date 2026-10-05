from abc import ABC, abstractmethod


class BaseResolver(ABC):
    @abstractmethod
    def supports(self, url: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def resolve(self, url: str) -> str | None:
        raise NotImplementedError
