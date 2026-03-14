from app.services.speech_provider import denormalize_language_code, normalize_language_code


def test_normalize_language_code_maps_short_codes():
    assert normalize_language_code("hi") == "hi-IN"
    assert normalize_language_code("en") == "en-IN"


def test_denormalize_language_code_maps_sarvam_codes():
    assert denormalize_language_code("hi-IN") == "hi"
    assert denormalize_language_code("en-IN") == "en"


def test_unknown_language_code_passes_through():
    assert normalize_language_code("fr") == "fr"
    assert denormalize_language_code("fr-FR") == "fr-FR"
