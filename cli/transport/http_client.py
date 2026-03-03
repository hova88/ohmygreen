from __future__ import annotations

import requests

DEFAULT_TIMEOUT = 20


class APIClientError(Exception):
    pass


class APIAuthError(APIClientError):
    pass


class APIServerError(APIClientError):
    pass


class APIResponseError(APIClientError):
    pass


def _map_http_error(exc: requests.HTTPError) -> APIClientError:
    status = exc.response.status_code if exc.response is not None else None
    if status in (401, 403):
        return APIAuthError("Authentication failed")
    if status is not None and status >= 500:
        return APIServerError("Server error")
    return APIResponseError(f"Request failed with status: {status}")


def api_login(base_url: str, username: str, password: str) -> str:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/auth/login",
            json={"username": username, "password": password},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise _map_http_error(exc) from exc
    except requests.RequestException as exc:
        raise APIClientError("Network error while logging in") from exc

    token = response.json().get("token")
    if not token:
        raise APIResponseError("Missing auth token in response")
    return token


def api_publish(base_url: str, token: str, title: str, content: str) -> int:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/posts",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": title, "content": content},
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise _map_http_error(exc) from exc
    except requests.RequestException as exc:
        raise APIClientError("Network error while publishing") from exc

    post_id = response.json().get("id")
    if post_id is None:
        raise APIResponseError("Missing post id in response")
    return post_id
