import warnings
from io import BytesIO

from PIL import Image, UnidentifiedImageError

from app.errors import AppError


def validate_image(raw, filename, mime):
    extension = (filename or "").lower().rsplit(".", 1)[-1]
    if extension not in {"jpg", "jpeg", "png"} or mime not in {"image/jpeg", "image/png"}:
        raise AppError(415, "INVALID_IMAGE_TYPE", "JPG, PNG(5MB 이하)만 가능합니다.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                actual = {"JPEG": "image/jpeg", "PNG": "image/png"}.get(image.format)
                if actual != mime or (extension == "png") != (image.format == "PNG"):
                    raise AppError(415, "INVALID_IMAGE_TYPE", "파일 확장자·MIME·실제 이미지 형식이 일치하지 않습니다.")
                if image.width * image.height > 16_000_000:
                    raise AppError(413, "IMAGE_TOO_LARGE", "이미지 해상도는 1600만 픽셀 이하여야 합니다.")
                image.load()
                image = image.convert("RGB")
                image.thumbnail((2048, 2048))
                buffer = BytesIO()
                image.save(buffer, "JPEG", quality=90)
                return buffer.getvalue(), "image/jpeg"
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise AppError(415, "INVALID_IMAGE_TYPE", "올바른 JPG 또는 PNG 이미지가 아닙니다.") from exc
