from vbcua.audio_features import analyze_filler_words
from vbcua.semantic import lexical_similarity, tokenize
from vbcua.text_analysis import analyze_sentiment


def test_filler_word_analysis_counts_single_and_phrase_fillers():
    stats = analyze_filler_words(
        "Um, machine learning is, you know, like a way to learn from data."
    )

    assert stats.filler_word_count == 3
    assert stats.occurrences["um"] == 1
    assert stats.occurrences["you know"] == 1
    assert stats.occurrences["like"] == 1
    assert stats.total_words > stats.filler_word_count


def test_lexical_similarity_is_higher_for_related_text():
    reference = "cloud computing provides scalable servers and storage over the internet"
    related = "cloud services offer internet storage and scalable server resources"
    unrelated = "photosynthesis converts light energy into chemical energy in plants"

    assert lexical_similarity(reference, related) > lexical_similarity(reference, unrelated)


def test_tokenize_preserves_technical_terms():
    assert "c++" in tokenize("C++ and Python are programming languages.")


def test_sentiment_analysis_has_local_fallback_shape():
    sentiment = analyze_sentiment("This is a clear and confident explanation.")

    assert sentiment.label in {"Positive", "Neutral", "Negative"}
    assert -1 <= sentiment.compound_score <= 1
