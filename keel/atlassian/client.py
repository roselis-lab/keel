"""The few Confluence and Jira REST calls a publish needs, for Cloud and Data Center.

Standard library only, so a security engineer's machine needs nothing new to reach a
company Atlassian. Authentication is the person's own token:

* Cloud: an API token with the account e-mail, sent as Basic auth;
* Data Center: a personal access token, sent as Bearer.

Both products' REST v1/v2 endpoints used here exist on Cloud and Data Center. The one
place they differ is Jira search: Cloud moved it to `/search/jql`, so that is tried first
and the older `/search` is the fallback.

`transport` is injectable so the tests run without a network.
"""
from __future__ import annotations

import base64
import json
import uuid
from collections.abc import Callable
from typing import Any
from urllib import error, parse, request

Transport = Callable[[str, str, dict[str, str], bytes | None], tuple[int, bytes]]


class AtlassianError(RuntimeError):
    pass


def _urllib(method: str, url: str, headers: dict[str, str], body: bytes | None) -> tuple[int, bytes]:
    req = request.Request(url, data=body, method=method, headers=headers)
    try:
        with request.urlopen(req, timeout=60) as resp:  # noqa: S310 - https enforced below
            return resp.status, resp.read()
    except error.HTTPError as e:
        return e.code, e.read()


class Api:
    def __init__(
        self, base_url: str, token: str, email: str | None = None,
        transport: Transport | None = None,
    ):
        base_url = base_url.rstrip("/")
        if not base_url.startswith("https://"):
            raise AtlassianError(f"{base_url}: only https is accepted, the token travels with every call")
        self.base = base_url
        if email:
            raw = base64.b64encode(f"{email}:{token}".encode()).decode()
            self.auth = f"Basic {raw}"
        else:
            self.auth = f"Bearer {token}"
        self.transport = transport or _urllib

    def call(
        self, method: str, path: str, *, params: dict[str, Any] | None = None,
        body: Any = None, files: dict[str, tuple[str, bytes, str]] | None = None,
        xsrf: str | None = None, ok: tuple[int, ...] = (200, 201, 204),
    ) -> tuple[int, Any]:
        url = self.base + path + (("?" + parse.urlencode(params)) if params else "")
        headers = {"Authorization": self.auth, "Accept": "application/json"}
        data: bytes | None = None
        if files is not None:
            boundary = uuid.uuid4().hex
            parts = []
            for field, (name, content, ctype) in files.items():
                parts.append(
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
                    f"filename=\"{name}\"\r\nContent-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n"
                )
            parts.append(f"--{boundary}--\r\n".encode())
            data = b"".join(parts)
            headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        if xsrf:
            headers["X-Atlassian-Token"] = xsrf
        code, raw = self.transport(method, url, headers, data)
        if code not in ok:
            text = raw[:400].decode("utf-8", "replace")
            raise AtlassianError(f"{method} {path}: HTTP {code}: {text}")
        return code, (json.loads(raw) if raw.strip() else None)


class Confluence:
    def __init__(self, api: Api):
        self.api = api

    def find_page(self, space: str, title: str) -> dict[str, Any] | None:
        _, data = self.api.call("GET", "/rest/api/content", params={
            "spaceKey": space, "title": title, "type": "page", "expand": "version",
        })
        results = (data or {}).get("results") or []
        return results[0] if results else None

    def create_page(self, space: str, title: str, body: str, parent_id: str | None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "page", "title": title, "space": {"key": space},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        return self.api.call("POST", "/rest/api/content", body=payload)[1]

    def update_page(self, page: dict[str, Any], body: str) -> dict[str, Any]:
        payload = {
            "id": page["id"], "type": "page", "title": page["title"],
            "version": {"number": page["version"]["number"] + 1,
                        "message": "Published by Keel"},
            "body": {"storage": {"value": body, "representation": "storage"}},
        }
        return self.api.call("PUT", f"/rest/api/content/{page['id']}", body=payload)[1]

    def put_attachment(self, page_id: str, name: str, content: bytes) -> None:
        _, data = self.api.call(
            "GET", f"/rest/api/content/{page_id}/child/attachment", params={"filename": name},
        )
        existing = (data or {}).get("results") or []
        files = {"file": (name, content, "image/png")}
        if existing:
            self.api.call(
                "POST", f"/rest/api/content/{page_id}/child/attachment/{existing[0]['id']}/data",
                files=files, xsrf="nocheck",
            )
        else:
            self.api.call(
                "POST", f"/rest/api/content/{page_id}/child/attachment",
                files=files, xsrf="nocheck",
            )

    def url_of(self, page: dict[str, Any]) -> str:
        links = page.get("_links") or {}
        webui = links.get("webui") or f"/pages/viewpage.action?pageId={page['id']}"
        return (links.get("base") or self.api.base) + webui


class Jira:
    def __init__(self, api: Api):
        self.api = api

    def find_issue(self, project: str, label: str) -> dict[str, Any] | None:
        jql = f'project = "{project}" AND labels = "{label}"'
        params = {"jql": jql, "fields": "summary,attachment", "maxResults": 2}
        try:
            _, data = self.api.call("GET", "/rest/api/2/search/jql", params=params)
        except AtlassianError as e:
            if "HTTP 404" not in str(e) and "HTTP 405" not in str(e):
                raise
            _, data = self.api.call("GET", "/rest/api/2/search", params=params)
        issues = (data or {}).get("issues") or []
        if len(issues) > 1:
            keys = ", ".join(i["key"] for i in issues)
            raise AtlassianError(f"label {label} is on more than one issue ({keys}); remove it from all but one")
        return issues[0] if issues else None

    def create_issue(self, fields: dict[str, Any]) -> str:
        return self.api.call("POST", "/rest/api/2/issue", body={"fields": fields})[1]["key"]

    def update_issue(self, key: str, fields: dict[str, Any]) -> None:
        self.api.call("PUT", f"/rest/api/2/issue/{key}", body={"fields": fields})

    def attachments(self, key: str) -> list[dict[str, Any]]:
        _, data = self.api.call("GET", f"/rest/api/2/issue/{key}", params={"fields": "attachment"})
        return ((data or {}).get("fields") or {}).get("attachment") or []

    def put_attachment(self, key: str, name: str, content: bytes) -> None:
        # Jira cannot replace an attachment in place. Only Keel's own pictures, by their
        # name, are removed before the new one goes up; nothing else on the issue is touched.
        for a in self.attachments(key):
            if a.get("filename") == name:
                self.api.call("DELETE", f"/rest/api/2/attachment/{a['id']}")
        self.api.call(
            "POST", f"/rest/api/2/issue/{key}/attachments",
            files={"file": (name, content, "image/png")}, xsrf="no-check",
        )

    def url_of(self, key: str) -> str:
        return f"{self.api.base}/browse/{key}"
