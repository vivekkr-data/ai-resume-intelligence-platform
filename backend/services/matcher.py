"""Explainable semantic matching with Sentence Transformers and TF-IDF fallback."""
from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.config import settings

logger = logging.getLogger(__name__)


def _clean_excerpt(text: str, limit: int = 240) -> str:
    clean = re.sub(r"\s+", " ", text).strip(" •-\t")
    return clean if len(clean) <= limit else clean[: limit - 1].rstrip() + "…"


def _chunks(text: str, words_per_chunk: int = 75, max_chunks: int = 45) -> list[str]:
    """Create short, readable chunks that can also be shown as match evidence."""
    lines = [line.strip(" •-\t") for line in text.splitlines() if line.strip()]
    chunks: list[str] = []
    buffer: list[str] = []
    word_count = 0

    for line in lines:
        line_words = line.split()
        looks_like_heading = len(line_words) <= 5 and line.upper() == line and not line.endswith(".")
        if looks_like_heading and buffer:
            chunks.append(" ".join(buffer))
            buffer, word_count = [], 0
        if word_count + len(line_words) > words_per_chunk and buffer:
            chunks.append(" ".join(buffer))
            buffer, word_count = [], 0
        buffer.append(line)
        word_count += len(line_words)
    if buffer:
        chunks.append(" ".join(buffer))

    if not chunks:
        words = text.split()
        chunks = [" ".join(words[index : index + words_per_chunk]) for index in range(0, len(words), words_per_chunk)]
    return [_clean_excerpt(chunk, 520) for chunk in chunks[:max_chunks] if chunk.strip()] or [""]


@lru_cache(maxsize=1)
def _load_sentence_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def _build_evidence(
    pairwise: np.ndarray,
    resume_chunks: list[str],
    job_chunks: list[str],
    limit: int = 5,
) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    ranked: list[tuple[float, int, int]] = []
    for job_index in range(pairwise.shape[0]):
        resume_index = int(np.argmax(pairwise[job_index]))
        ranked.append((float(pairwise[job_index, resume_index]), job_index, resume_index))

    for score, job_index, resume_index in sorted(ranked, reverse=True)[:limit]:
        evidence.append(
            {
                "requirement": _clean_excerpt(job_chunks[job_index]),
                "resume_evidence": _clean_excerpt(resume_chunks[resume_index]),
                "similarity": round(max(0.0, min(1.0, score)) * 100, 2),
            }
        )
    return evidence


def _sentence_transformer_analysis(
    resume_text: str, job_text: str
) -> tuple[float, list[dict[str, object]]]:
    model = _load_sentence_model()
    resume_chunks = _chunks(resume_text, words_per_chunk=75)
    job_chunks = _chunks(job_text, words_per_chunk=55)
    all_chunks = resume_chunks + job_chunks
    embeddings = model.encode(
        all_chunks,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=16,
        convert_to_numpy=True,
    )
    resume_embeddings = np.asarray(embeddings[: len(resume_chunks)])
    job_embeddings = np.asarray(embeddings[len(resume_chunks) :])

    pairwise = job_embeddings @ resume_embeddings.T
    best_per_requirement = np.max(pairwise, axis=1)
    # Give slightly more importance to the weakest important requirements instead of
    # allowing one excellent section to hide several missing requirements.
    requirement_coverage = float(0.7 * np.mean(best_per_requirement) + 0.3 * np.percentile(best_per_requirement, 35))
    overall_similarity = float(
        np.dot(np.mean(resume_embeddings, axis=0), np.mean(job_embeddings, axis=0))
    )
    combined = 0.75 * requirement_coverage + 0.25 * overall_similarity
    score = round(max(0.0, min(1.0, combined)) * 100, 2)
    return score, _build_evidence(pairwise, resume_chunks, job_chunks)


def _tfidf_analysis(
    resume_text: str, job_text: str
) -> tuple[float, list[dict[str, object]]]:
    resume_chunks = _chunks(resume_text, words_per_chunk=75)
    job_chunks = _chunks(job_text, words_per_chunk=55)
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_features=15000,
        sublinear_tf=True,
    )
    try:
        matrix = vectorizer.fit_transform(resume_chunks + job_chunks)
    except ValueError:
        evidence = [{
            "requirement": _clean_excerpt(job_chunks[0]),
            "resume_evidence": _clean_excerpt(resume_chunks[0]),
            "similarity": 0.0,
        }]
        return 0.0, evidence
    resume_matrix = matrix[: len(resume_chunks)]
    job_matrix = matrix[len(resume_chunks) :]
    pairwise = cosine_similarity(job_matrix, resume_matrix)
    best = np.max(pairwise, axis=1)
    raw_score = float(0.75 * np.mean(best) + 0.25 * np.percentile(best, 35))
    calibrated = 0.22 * raw_score + 0.78 * float(np.sqrt(max(raw_score, 0.0)))
    return round(min(100.0, calibrated * 100), 2), _build_evidence(
        pairwise, resume_chunks, job_chunks
    )


def semantic_similarity_detailed(
    resume_text: str, job_text: str
) -> tuple[float, str, list[dict[str, object]]]:
    try:
        score, evidence = _sentence_transformer_analysis(resume_text, job_text)
        return score, settings.embedding_model, evidence
    except Exception as exc:
        logger.warning("Sentence Transformer unavailable; using TF-IDF fallback: %s", exc)
        score, evidence = _tfidf_analysis(resume_text, job_text)
        return score, "TF-IDF fallback", evidence


def semantic_similarity(resume_text: str, job_text: str) -> tuple[float, str]:
    score, model, _ = semantic_similarity_detailed(resume_text, job_text)
    return score, model


def rank_texts(query: str, documents: Iterable[str]) -> tuple[list[float], str]:
    docs = list(documents)
    if not docs:
        return [], settings.embedding_model

    try:
        model = _load_sentence_model()
        embeddings = model.encode(
            [query] + docs,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=16,
            convert_to_numpy=True,
        )
        query_vector = np.asarray(embeddings[0])
        doc_vectors = np.asarray(embeddings[1:])
        scores = np.clip(doc_vectors @ query_vector, 0, 1) * 100
        return [round(float(value), 2) for value in scores], settings.embedding_model
    except Exception as exc:
        logger.warning("Embedding ranking unavailable; using TF-IDF fallback: %s", exc)
        vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), max_features=15000
        )
        try:
            matrix = vectorizer.fit_transform([query] + docs)
        except ValueError:
            return [0.0 for _ in docs], "TF-IDF fallback"
        raw_scores = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        scores = (0.2 * raw_scores + 0.8 * np.sqrt(np.maximum(raw_scores, 0))) * 100
        return [round(float(value), 2) for value in scores], "TF-IDF fallback"
