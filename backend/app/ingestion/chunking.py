def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
	if chunk_size < 1 or not 0 <= chunk_overlap < chunk_size:
		raise ValueError("chunk_overlap must be nonnegative and smaller than chunk_size")
	text = text.strip()
	if not text:
		return []
	step = chunk_size - chunk_overlap
	return [
		text[start : start + chunk_size]
		for start in range(0, len(text), step)
	]
