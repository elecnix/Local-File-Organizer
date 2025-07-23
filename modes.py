from enum import Enum

class Mode(Enum):
    CONTENT = 1
    DATE = 2
    TYPE = 3

    def __str__(self):
        if self == Mode.CONTENT:
            return "By Content"
        elif self == Mode.DATE:
            return "By Date"
        elif self == Mode.TYPE:
            return "By Type"
        return super().__str__()

    @classmethod
    def from_int(cls, value):
        for mode in cls:
            if mode.value == value:
                return mode
        raise ValueError(f"Invalid mode value: {value}")
