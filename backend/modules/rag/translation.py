from backend.modules.agents.common.llm import LLMClient


class RussianTranslator:
    def __init__(self, llm: LLMClient | None = None, *, chunk_size: int = 3500) -> None:
        self.llm = llm or LLMClient()
        self.chunk_size = chunk_size
        self.system_prompt = (
            "Translate the user text into natural Russian. "
            "Keep factual meaning, names, dates, money amounts, and product terms accurate. "
            "Return only the Russian translation without commentary."
        )

    def translate_to_russian(self, text: str) -> str:
        clean_text = (text or "").strip()
        if not clean_text:
            return ""

        chunks = self._split_text(clean_text)
        translated: list[str] = []
        for chunk in chunks:
            translated_chunk = self.llm.generate(
                self.system_prompt,
                chunk,
                fallback=chunk,
            )
            translated.append(translated_chunk.strip() or chunk)
        return "\n\n".join(part for part in translated if part)

    def _split_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            candidate = f"{current}\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue
            if current:
                chunks.append(current)
            if len(paragraph) <= self.chunk_size:
                current = paragraph
                continue
            start = 0
            while start < len(paragraph):
                end = start + self.chunk_size
                chunks.append(paragraph[start:end].strip())
                start = end
            current = ""

        if current:
            chunks.append(current)
        return chunks
