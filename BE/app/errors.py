class AppError(Exception):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


class AIUnavailable(AppError):
    def __init__(self):
        super().__init__(503, "AI_UNAVAILABLE", "AI 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.")


class DataSourceError(AppError):
    def __init__(self):
        super().__init__(502, "DATA_SOURCE_ERROR", "교육·채용 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")


class DatabaseError(AppError):
    def __init__(self):
        super().__init__(500, "DB_ERROR", "데이터 저장 또는 조회에 실패했습니다. 다시 시도해 주세요.")
