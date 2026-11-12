"""Stable fixture ids: instruction family + first 16 hex digits of sha256 over (id, kwargs, response, extra)."""
import hashlib
import json


def fid(iid, kwargs, response, extra=""):
    blob = json.dumps([iid, kwargs, response, extra], ensure_ascii=False, sort_keys=True).encode("utf-8")
    return iid.split(":")[1] + ":" + hashlib.sha256(blob).hexdigest()[:16]
