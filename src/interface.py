from abc import ABC, abstractmethod

class DriverManager(ABC):
    @abstractmethod
    def install(self) -> str:
        raise NotImplementedError()
    
    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError()
    
    @property
    def get_driver(self) -> str:
        pass