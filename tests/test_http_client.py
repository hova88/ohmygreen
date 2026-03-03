from __future__ import annotations

import unittest
from unittest.mock import Mock

import requests

from cli.transport.http_client import APIAuthError, APIResponseError, APIServerError, _map_http_error


class HttpClientErrorMappingTests(unittest.TestCase):
    def _http_error(self, status: int) -> requests.HTTPError:
        response = Mock()
        response.status_code = status
        return requests.HTTPError(response=response)

    def test_map_http_error_auth(self) -> None:
        err = _map_http_error(self._http_error(401))
        self.assertIsInstance(err, APIAuthError)

    def test_map_http_error_server(self) -> None:
        err = _map_http_error(self._http_error(500))
        self.assertIsInstance(err, APIServerError)

    def test_map_http_error_response(self) -> None:
        err = _map_http_error(self._http_error(400))
        self.assertIsInstance(err, APIResponseError)


if __name__ == "__main__":
    unittest.main()
