from sqlalchemy import Engine


class AbstractService:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        pass
