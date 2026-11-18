"""GitLab HTTP session that accepts either a personal access token or an OAuth bearer token."""

from typing import Any, Dict

import requests


class GitLabClient(object):
    """Sends PRIVATE-TOKEN first, then retries once with Authorization: Bearer.

    Personal access tokens use PRIVATE-TOKEN. OAuth access tokens on this
    instance are accepted only as bearer tokens.
    """

    def __init__(self, token: str) -> None:
        self.token = token
        self.mode = "private"
        self.session = requests.Session()
        self._apply()

    def _apply(self) -> None:
        self.session.headers.pop("PRIVATE-TOKEN", None)
        self.session.headers.pop("Authorization", None)
        if self.mode == "bearer":
            self.session.headers["Authorization"] = "Bearer %s" % self.token
        else:
            self.session.headers["PRIVATE-TOKEN"] = self.token

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        try:
            response = self.session.get(url, **kwargs)
        except requests.RequestException as exc:
            raise RuntimeError("GitLab request failed: %s" % exc)
        if response.status_code == 401 and self.mode == "private":
            self.mode = "bearer"
            self._apply()
            try:
                response = self.session.get(url, **kwargs)
            except requests.RequestException as exc:
                raise RuntimeError("GitLab request failed: %s" % exc)
        return response
