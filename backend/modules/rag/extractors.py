import re
import shutil
import subprocess
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from backend.modules.rag.schemas import RAGDocument
from backend.modules.rag.source_normalizers import normalize_text
from backend.modules.rag.translation import RussianTranslator


class LocalRagBaseExtractor:
    def __init__(self, translator: RussianTranslator | None = None) -> None:
        self.translator = translator or RussianTranslator()

    def extract_file(self, path: Path) -> RAGDocument | None:
        suffix = path.suffix.lower()
        if suffix in {".htm", ".html"}:
            return self._extract_html(path)
        if suffix == ".pdf":
            return self._extract_pdf(path)
        return None

    def _extract_html(self, path: Path) -> RAGDocument | None:
        raw_html = path.read_text(encoding="utf-8", errors="ignore")
        title = self._extract_title(raw_html) or path.stem
        url = self._extract_canonical(raw_html) or path.resolve().as_uri()
        published_at = self._extract_published_at(raw_html)
        article_blocks = self._extract_richtext_blocks(raw_html)
        article_text = "\n\n".join(block for block in article_blocks if block)
        normalized_article = normalize_text(article_text)
        if not normalized_article:
            normalized_article = normalize_text(raw_html)

        translated_text = self.translator.translate_to_russian(normalized_article)
        country = self._extract_labeled_value(raw_html, "Country:")
        risk_type = self._map_failory_cause(self._extract_labeled_value(raw_html, "Cause:"))

        return RAGDocument(
            external_id=path.stem,
            url=url,
            title=title,
            content=translated_text or normalized_article,
            source_key="failory_html_ru",
            source_type="failure_case",
            risk_type=risk_type,
            country=country,
            language="ru",
            published_at=published_at,
            trust_score=0.72,
            doc_type="html_article",
            metadata={
                "file_name": path.name,
                "local_path": str(path),
                "original_language": "en",
                "translated_to": "ru",
                "original_text": normalized_article,
                "cause": self._extract_labeled_value(raw_html, "Cause:"),
                "category": self._extract_labeled_value(raw_html, "Category:"),
                "company_name": self._extract_company_name(raw_html),
            },
        )

    def _extract_pdf(self, path: Path) -> RAGDocument | None:
        text = self._extract_pdf_text(path)
        if not text:
            return None

        normalized = normalize_text(text)
        if not normalized:
            return None

        title = self._extract_pdf_title(normalized, path.stem)
        source_type, risk_type, trust_score = self._infer_pdf_metadata(path.name, normalized)
        language = "ru" if self._looks_cyrillic(normalized) else "en"

        return RAGDocument(
            external_id=path.stem,
            url=path.resolve().as_uri(),
            title=title,
            content=normalized,
            source_key="rag_base_pdf",
            source_type=source_type,
            risk_type=risk_type,
            language=language,
            published_at=None,
            trust_score=trust_score,
            doc_type="pdf_document",
            metadata={
                "file_name": path.name,
                "local_path": str(path),
            },
        )

    def _extract_pdf_text(self, path: Path) -> str:
        pdftotext = shutil.which("pdftotext")
        if pdftotext:
            try:
                result = subprocess.run(
                    [pdftotext, "-layout", str(path), "-"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="ignore",
                    check=False,
                )
                text = (result.stdout or "").strip()
                if text:
                    return text
            except Exception:
                pass

        try:
            from pypdf import PdfReader  # type: ignore

            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception:
            return ""

    def _extract_title(self, raw_html: str) -> str | None:
        match = re.search(r"<title>(.*?)</title>", raw_html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return normalize_text(unescape(match.group(1)))

    def _extract_canonical(self, raw_html: str) -> str | None:
        match = re.search(
            r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"',
            raw_html,
            flags=re.IGNORECASE,
        )
        return unescape(match.group(1)) if match else None

    def _extract_published_at(self, raw_html: str) -> datetime | None:
        match = re.search(
            r'"datePublished"\s*:\s*"([^"]+)"',
            raw_html,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        raw_value = match.group(1).strip()
        for fmt in ("%b %d, %Y", "%Y-%m-%d", "%B %d, %Y"):
            try:
                return datetime.strptime(raw_value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    def _extract_richtext_blocks(self, raw_html: str) -> list[str]:
        matches = re.findall(
            r'<div class="content-black-rich-text w-richtext">(.*?)</div>',
            raw_html,
            flags=re.IGNORECASE | re.DOTALL,
        )
        blocks: list[str] = []
        for block in matches:
            clean = re.sub(r"<script.*?</script>", " ", block, flags=re.IGNORECASE | re.DOTALL)
            clean = re.sub(r"<style.*?</style>", " ", clean, flags=re.IGNORECASE | re.DOTALL)
            clean = re.sub(r"<br\s*/?>", "\n", clean, flags=re.IGNORECASE)
            clean = re.sub(r"</p>", "\n\n", clean, flags=re.IGNORECASE)
            clean = re.sub(r"</h[1-6]>", "\n\n", clean, flags=re.IGNORECASE)
            clean = re.sub(r"</li>", "\n", clean, flags=re.IGNORECASE)
            clean = re.sub(r"<li[^>]*>", "- ", clean, flags=re.IGNORECASE)
            clean = re.sub(r"<[^>]+>", " ", clean)
            normalized = normalize_text(unescape(clean))
            if normalized:
                blocks.append(normalized)
        return blocks

    def _extract_labeled_value(self, raw_html: str, label: str) -> str | None:
        pattern = (
            r'<div class="cemetery-page-data-category">\s*'
            + re.escape(label)
            + r'\s*</div>\s*<div class="cemetery-page-data-information">(.*?)</div>'
        )
        match = re.search(pattern, raw_html, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        return normalize_text(unescape(match.group(1)))

    def _extract_company_name(self, raw_html: str) -> str | None:
        match = re.search(r'<h1 class="cemetery-page-name">(.*?)</h1>', raw_html, flags=re.IGNORECASE | re.DOTALL)
        return normalize_text(unescape(match.group(1))) if match else None

    def _extract_pdf_title(self, text: str, fallback: str) -> str:
        for line in text.splitlines():
            clean = line.strip()
            if len(clean) >= 20:
                return clean[:220]
        return fallback

    def _infer_pdf_metadata(self, file_name: str, text: str) -> tuple[str, str | None, float]:
        lowered_name = file_name.lower()
        lowered_text = text.lower()
        if "consultation" in lowered_name or "consultation paper" in lowered_text:
            return ("regulatory_paper", "regulation", 0.95)
        if "prikaz" in lowered_name or "приказ" in lowered_text:
            return ("regulatory_order", "regulation", 0.98)
        if "analytic" in lowered_name or "аналит" in lowered_text:
            return ("analytics_report", "market", 0.88)
        return ("pdf_document", "general", 0.8)

    def _map_failory_cause(self, cause: str | None) -> str | None:
        if not cause:
            return "failure_case"
        normalized = cause.lower()
        if "legal" in normalized:
            return "regulation"
        if "competition" in normalized:
            return "competition"
        if "business model" in normalized:
            return "unit_economics"
        if "poor product" in normalized:
            return "weak_demand"
        return "failure_case"

    def _looks_cyrillic(self, text: str) -> bool:
        cyrillic = len(re.findall(r"[А-Яа-яЁё]", text))
        latin = len(re.findall(r"[A-Za-z]", text))
        return cyrillic >= latin
