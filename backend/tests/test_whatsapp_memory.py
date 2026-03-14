from app.db.memory import get_whatsapp_media, store_whatsapp_media


def test_whatsapp_media_round_trip():
    media_id = store_whatsapp_media(b"demo-audio", "audio/wav", ttl_seconds=60)
    payload = get_whatsapp_media(media_id)

    assert payload is not None
    assert payload["content"] == b"demo-audio"
    assert payload["content_type"] == "audio/wav"
