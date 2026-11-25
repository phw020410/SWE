from collections import deque

from starlette.responses import JSONResponse


class ImageBodyLimitMiddleware:
    """파일 파싱 전 전체 multipart를 메모리 한도 안에서만 받는다. chunked 요청에도 적용한다."""
    def __init__(self, app, limit):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/image-query":
            return await self.app(scope, receive, send)
        messages, size = deque(), 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            size += len(message.get("body", b""))
            if size > self.limit:
                response = JSONResponse({"code": "IMAGE_TOO_LARGE", "message": "JPG, PNG(5MB 이하)만 가능합니다."}, status_code=413)
                return await response(scope, receive, send)
            messages.append(message)
            if not message.get("more_body", False):
                break

        async def replay():
            return messages.popleft() if messages else await receive()
        return await self.app(scope, replay, send)
