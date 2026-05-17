from app.rag.chunker import chunk_text


def test_chunker_respects_overlap() -> None:
    text = " ".join([f"token{i}" for i in range(1, 31)])
    chunks = chunk_text(text=text, chunk_size_words=10, chunk_overlap_words=2)

    assert len(chunks) >= 3
    assert chunks[0].split()[-2:] == chunks[1].split()[:2]


def test_chunker_raises_for_invalid_overlap() -> None:
    try:
        chunk_text(text="a b c", chunk_size_words=3, chunk_overlap_words=3)
    except ValueError as exc:
        assert "smaller" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid overlap")
