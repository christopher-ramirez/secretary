class PadStringFilter():
    def __init__(self, renderer):
        pass

    @staticmethod
    def render(value, length=5):
        value = str(value)
        return value.zfill(length)
