#!/usr/bin/env python3
"""
Синхронизация текущей директории в бакет Yandex Object Storage (S3-совместимый API).
Использование: из корня репо запустить с переменными окружения
  S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET.
"""
import os
import re
from pathlib import Path

import boto3
from botocore.config import Config

EXCLUDE = re.compile(
    r"^\.git(/|$)|^\.env$|\.venv/|venv/|__pycache__/|\.pyc$|\.DS_Store|^\.github/|\.log$"
)


def should_skip(path: str) -> bool:
    return bool(EXCLUDE.search(path.replace("\\", "/")))


def _clean(s: str) -> str:
    """Убрать все пробельные символы по краям и внутри (частая причина SignatureDoesNotMatch)."""
    if not s:
        return ""
    return "".join(s.split())


def main():
    # Секреты из GitHub могут содержать \r\n или пробелы — убираем всё лишнее
    ak = _clean(os.environ.get("S3_ACCESS_KEY_ID") or "")
    sk = _clean(os.environ.get("S3_SECRET_ACCESS_KEY") or "")
    bucket = (os.environ.get("S3_BUCKET") or "").strip()
    if not ak or not sk or not bucket:
        raise SystemExit("Set S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY, S3_BUCKET")

    # Yandex Object Storage: endpoint со слэшем, region ru-central1, path-style, SigV4
    session = boto3.Session(
        aws_access_key_id=ak,
        aws_secret_access_key=sk,
        region_name="ru-central1",
    )
    client = session.client(
        "s3",
        endpoint_url="https://storage.yandexcloud.net/",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
        ),
    )

    root = Path(".").resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        key = str(rel).replace("\\", "/")
        if should_skip(key):
            continue
        content = path.read_bytes()
        client.put_object(Bucket=bucket, Key=key, Body=content)
        print(key)

    # Список ключей в бакете — удалить те, которых нет локально
    paginator = client.get_paginator("list_objects_v2")
    remote_keys = set()
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get("Contents") or []:
            remote_keys.add(obj["Key"])
    local_keys = set()
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root)
            key = str(rel).replace("\\", "/")
            if not should_skip(key):
                local_keys.add(key)
    for key in remote_keys - local_keys:
        client.delete_object(Bucket=bucket, Key=key)
        print(f"deleted {key}")


if __name__ == "__main__":
    main()
