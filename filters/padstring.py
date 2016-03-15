class PadStringFilter():
    def __init__(self, engine):
        engine.environment.filters['pad'] = self.padstr

    def padstr(self, value, length=5):
        value = str(value)
        return value.zfill(length)
