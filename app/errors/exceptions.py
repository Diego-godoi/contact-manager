class AppError(Exception):
    def __init__(self, detail, status_code=500):
        super().__init__(detail)
        self.detail: str = detail
        self.status_code: int = status_code


class NotFoundError(AppError):
    def __init__(self, detail='Resource not found'):
        super().__init__(detail, 404)


class ConflictError(AppError):
    def __init__(self, detail='Resource already exists'):
        super().__init__(detail, 409)


class InvalidCredentialsError(AppError):
    def __init__(self, detail='Invalid Resource'):
        super().__init__(detail, 401)


class ForbiddenError(AppError):
    def __init__(self, detail='Access Denied'):
        super().__init__(detail, 403)
