from enum import Enum

class Mode(Enum):
    CONTENT = 1
    DATE = 2
    TYPE = 3

    def __str__(self):
        return self.name.lower()

    @classmethod
    def from_int(cls, value):
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"Invalid mode value: {value}")

    @classmethod
    def from_string(cls, value):
        for mode in cls:
            if mode.name.lower() == value.lower():
                return mode
        raise ValueError(f"Invalid mode value: {value}")
