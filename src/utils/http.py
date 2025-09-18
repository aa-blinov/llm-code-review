import logging
from typing import Any

import httpx
from httpx_retries import Retry, RetryTransport
from loguru import logger

from src.config import Config

_base_transport = httpx.HTTPTransport(retries=Config.MAX_RETRIES)
_timeout = httpx.Timeout(
    connect=Config.TIMEOUT,
    read=Config.TIMEOUT,
    write=Config.TIMEOUT,
    pool=Config.TIMEOUT,
)
_retries = Retry(
    total=Config.MAX_RETRIES + 1,  # including initial attempt
    allowed_methods={"GET", "PUT", "DELETE", "HEAD", "OPTIONS", "POST"},
    status_forcelist={429, 500, 502, 503, 504},
    backoff_factor=0.5,
)
_transport = RetryTransport(transport=_base_transport, retry=_retries)
_client = httpx.Client(transport=_transport, timeout=_timeout, follow_redirects=True)


class _LoguruHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = record.levelname
            logger.bind(src_logger=record.name).log(level, record.getMessage())
        except Exception as exc:
            logger.debug(f"log bridge error: {exc}")


_retry_logger = logging.getLogger("httpx_retries")
_retry_logger.setLevel(logging.DEBUG)
_retry_logger.propagate = False
if not any(isinstance(h, _LoguruHandler) for h in _retry_logger.handlers):
    _retry_logger.addHandler(_LoguruHandler())


def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> httpx.Response:
    logger.debug(f"HTTP {method} {url}")
    resp = _client.request(method, url, headers=headers, params=params, json=json)
    resp.raise_for_status()
    return resp


def get(url: str, headers: dict[str, str] | None = None, params: dict[str, Any] | None = None):
    return _request("GET", url, headers=headers, params=params).json()


def post(url: str, headers: dict[str, str] | None = None, data: dict[str, Any] | None = None):
    return _request("POST", url, headers=headers, json=data).json()


def put(url: str, headers: dict[str, str] | None = None, data: dict[str, Any] | None = None):
    return _request("PUT", url, headers=headers, json=data).json()


def delete(url: str, headers: dict[str, str] | None = None):
    return _request("DELETE", url, headers=headers).status_code
