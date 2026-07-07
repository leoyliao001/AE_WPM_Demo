"""
Dify 文件信息提取（仅 extract_file_info 一个对外接口）。

配置（项目根目录 .env）:
    url      — Dify API 地址
    api_key  — 应用 API Key

用法:
    from backend.api.views.dify import extract_file_info

    text = extract_file_info("report.xlsx")
    text = extract_file_info("scan.pdf", "请提取全部信息")
"""

from __future__ import annotations

import json
import mimetypes
import shutil
import tempfile
import time
from pathlib import Path

import requests

_ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
_DEFAULT_QUERY = "请阅读这份文档，提取其中的关键信息并做结构化总结。"
_DEFAULT_USER = "demo-user"


def extract_file_info(
    file_path: str | Path,
    query: str = _DEFAULT_QUERY,
    *,
    max_pdf_pages: int = 3,
) -> str:
    """上传文件并让 Dify 提取信息，返回模型回答文本。

    自动处理：图片(Vision)、Excel/文本 PDF(document)、扫描 PDF(转 JPEG + Vision)。
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"文件不存在: {path}")

    base_url, api_key = _load_config()
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {api_key}"

    # 扫描件 PDF 直接走转图路径（Vision 不读 PDF）
    if path.suffix.lower() == ".pdf" and _is_scanned_pdf(path):
        chat = _chat_with_scanned_pdf(session, base_url, path, query, max_pdf_pages)
        return chat.get("answer", "")

    # 常规：上传原文件
    upload = _upload_file(session, base_url, path)
    file_ref = _file_ref(upload, _file_kind(path))
    chat, _ = _chat(session, base_url, query, files=[file_ref])

    if _attachment_ok(chat, path):
        return chat.get("answer", "")

    # 备用：document 附件失败时本地提文本
    if _file_kind(path) != "image":
        extracted = _extract_local_text(path)
        local_query = (
            f"{query}\n\n"
            f"以下是从附件「{path.name}」提取的文本内容，请基于此分析：\n\n"
            f"---\n{extracted}\n---"
        )
        chat, _ = _chat(session, base_url, local_query)
        return chat.get("answer", "")

    return chat.get("answer", "")


# ---------------------------------------------------------------------------
# 内部实现
# ---------------------------------------------------------------------------


def _load_config() -> tuple[str, str]:
    env: dict[str, str] = {}
    if _ENV_PATH.exists():
        for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip("'\"")

    base_url = (env.get("url") or env.get("DIFY_API_URL") or "").rstrip("/")
    api_key = env.get("api_key") or env.get("DIFY_API_KEY") or ""
    if not base_url:
        raise ValueError(f"未在 {_ENV_PATH} 中找到 url")
    if not api_key:
        raise ValueError(f"未在 {_ENV_PATH} 中找到 api_key")
    return base_url, api_key


def _file_kind(path: Path) -> str:
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        return "image"
    return "document"


def _file_ref(upload: dict, kind: str) -> dict:
    return {
        "type": kind,
        "transfer_method": "local_file",
        "upload_file_id": upload["id"],
    }


def _upload_file(session: requests.Session, base_url: str, path: Path) -> dict:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    with path.open("rb") as f:
        r = session.post(
            f"{base_url}/files/upload",
            files={"file": (path.name, f, mime)},
            data={"user": _DEFAULT_USER},
            timeout=120,
        )
    r.raise_for_status()
    return r.json()


def _chat(
    session: requests.Session,
    base_url: str,
    query: str,
    *,
    files: list[dict] | None = None,
    timeout: int = 120,
    retries: int = 0,
) -> tuple[dict, dict]:
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "user": _DEFAULT_USER,
    }
    if files:
        payload["files"] = files

    last_err: requests.HTTPError | None = None
    for attempt in range(retries + 1):
        r = session.post(
            f"{base_url}/chat-messages",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        if r.ok:
            return r.json(), payload
        detail = r.text
        try:
            detail = json.dumps(r.json(), ensure_ascii=False)
        except ValueError:
            pass
        last_err = requests.HTTPError(f"{r.status_code} {r.reason}\n{detail}", response=r)
        if r.status_code in {502, 503, 504} and attempt < retries:
            time.sleep(2 ** attempt)
            continue
        raise last_err
    raise last_err  # pragma: no cover


def _attachment_ok(chat: dict, path: Path) -> bool:
    tokens = chat.get("metadata", {}).get("usage", {}).get("prompt_tokens", 0)
    answer = (chat.get("answer") or "").strip()
    if _file_kind(path) == "image":
        return tokens >= 250 or len(answer) > 200
    return tokens >= 500


def _pdf_text(path: Path) -> str:
    import fitz

    doc = fitz.open(path)
    text = "\n".join(page.get_text() for page in doc).strip()
    doc.close()
    return text


def _is_scanned_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf" and len(_pdf_text(path)) < 50


def _pdf_to_jpegs(path: Path, max_pages: int) -> tuple[list[Path], Path, int]:
    import fitz

    doc = fitz.open(path)
    total = len(doc)
    tmp = Path(tempfile.mkdtemp(prefix="dify_pdf_"))
    images: list[Path] = []
    for i in range(min(total, max_pages)):
        page = doc.load_page(i)
        pix = page.get_pixmap(dpi=100)
        if max(pix.width, pix.height) > 1600:
            s = 1600 / max(pix.width, pix.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(s, s))
        out = tmp / f"{path.stem}_p{i + 1}.jpg"
        pix.save(out, jpg_quality=85)
        images.append(out)
    doc.close()
    return images, tmp, total


def _chat_with_scanned_pdf(
    session: requests.Session,
    base_url: str,
    path: Path,
    query: str,
    max_pages: int,
) -> dict:
    images, tmp, total = _pdf_to_jpegs(path, max_pages)
    refs: list[dict] = []
    try:
        for img in images:
            refs.append(_file_ref(_upload_file(session, base_url, img), "image"))
        scan_query = (
            f"{query}\n\n"
            f"附件为扫描件 PDF「{path.name}」，共 {total} 页，"
            f"已上传前 {len(images)} 页图片，请逐页 OCR 并汇总。"
        )
        chat, _ = _chat(session, base_url, scan_query, files=refs, timeout=300, retries=2)
        return chat
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _extract_local_text(path: Path, max_chars: int = 40000) -> str:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm", ".xls"}:
        import pandas as pd

        wb = pd.ExcelFile(path)
        parts = []
        for name in wb.sheet_names:
            parts.append(f"## Sheet: {name}")
            parts.append(pd.read_excel(wb, sheet_name=name).to_csv(index=False))
        text = "\n".join(parts)
    elif suffix == ".csv":
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix in {".txt", ".md", ".json"}:
        text = path.read_text(encoding="utf-8", errors="replace")
    elif suffix == ".pdf":
        text = _pdf_text(path)
        if not text:
            raise ValueError("PDF 无文本层，请确认是扫描件")
    else:
        raise ValueError(f"不支持本地解析: {suffix}")
    return text[:max_chars] + ("\n...(截断)" if len(text) > max_chars else "")




