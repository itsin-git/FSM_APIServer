"""
HTTP Basic Auth – FortiSIEM 형식

클라이언트는 다음 형식으로 인증 헤더를 전송한다:
  Authorization: Basic base64(<org>/<username>:<password>)
  예) super/admin:password1234  →  Basic c3VwZXIvYWRtaW46cGFzc3dvcmQxMjM0

검증 절차:
  1. Authorization: Basic <token> 헤더 파싱
  2. base64 디코드 → "<org>/<username>:<password>" 또는 "<username>:<password>"
  3. username 부분을 '/' 로 분리해 org / username 추출
  4. .env의 API_ORG / API_USERNAME / API_PASSWORD 와 대조
"""

import base64
import secrets
from typing import Tuple

from fastapi import HTTPException, Request, status

from app.core.config import Settings, get_settings


def _decode_basic(authorization: str) -> Tuple[str, str, str]:
    """
    Authorization 헤더 값을 파싱해 (org, username, password)를 반환한다.
    org가 없으면 빈 문자열로 반환한다.

    Raises:
        ValueError: 헤더 형식이 잘못된 경우
    """
    if not authorization.startswith("Basic "):
        raise ValueError("Not a Basic auth header")

    try:
        decoded = base64.b64decode(authorization[6:]).decode("utf-8")
    except Exception:
        raise ValueError("Invalid base64 encoding")

    # decoded = "org/username:password" 또는 "username:password"
    if ":" not in decoded:
        raise ValueError("Missing ':' separator between username and password")

    colon_idx = decoded.index(":")
    raw_user = decoded[:colon_idx]        # "super/admin" 또는 "admin"
    password = decoded[colon_idx + 1:]    # "password1234"

    if "/" in raw_user:
        slash_idx = raw_user.index("/")
        org = raw_user[:slash_idx]
        username = raw_user[slash_idx + 1:]
    else:
        org = ""
        username = raw_user

    return org, username, password


def require_auth(request: Request) -> str:
    """
    FastAPI Depends로 사용하는 인증 함수.
    검증 성공 시 'org/username' 문자열을 반환한다.
    """
    settings = get_settings()

    authorization = request.headers.get("Authorization", "")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": 'Basic realm="FortiSIEM Adapter"'},
        )

    try:
        org, username, password = _decode_basic(authorization)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Authorization header: {exc}",
            headers={"WWW-Authenticate": 'Basic realm="FortiSIEM Adapter"'},
        )

    # org가 비어 있으면 설정값과 무관하게 통과 (org 없이 username만 보낸 경우)
    # org가 있으면 설정된 api_org와 대조 (대소문자 무시)
    ok_org = not org or secrets.compare_digest(org.lower(), settings.api_org.lower())
    ok_user = secrets.compare_digest(username, settings.api_username)
    ok_pass = secrets.compare_digest(password, settings.api_password)

    if not (ok_org and ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": 'Basic realm="FortiSIEM Adapter"'},
        )

    return f"{org}/{username}" if org else username
