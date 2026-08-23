class GatorExplode(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class MisconfiguredService(GatorExplode):
    pass


class TokenGenerationFailure(GatorExplode):
    pass


class ServiceError(GatorExplode):
    pass


class StreamError(GatorExplode):
    pass


class NotImplementedYet(GatorExplode):
    pass


class SelectionExpired(GatorExplode):
    pass
