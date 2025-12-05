from abc import ABC, abstractmethod


class MatrixCanvas(ABC):
    @abstractmethod
    def Clear(self):
        pass

    @abstractmethod
    def SetPixel(self, x: int, y: int, r: int, g: int, b: int):
        pass

    @abstractmethod
    def Fill(self, r: int, g: int, b: int):
        pass


class MockCanvas(MatrixCanvas):
    def __init__(self, width: int = 64, height: int = 32):
        self.width = width
        self.height = height
        self.pixels = {}

    def Clear(self):
        self.pixels = {}

    def SetPixel(self, x: int, y: int, r: int, g: int, b: int):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[(x, y)] = (r, g, b)

    def Fill(self, r: int, g: int, b: int):
        for x in range(self.width):
            for y in range(self.height):
                self.pixels[(x, y)] = (r, g, b)
