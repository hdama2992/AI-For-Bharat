import asyncio

from app.routers.mandi import compare_mandi_prices


def test_mandi_compare_returns_recommendation():
    result = asyncio.run(compare_mandi_prices(crop="Soybean", district="Harda"))

    assert result["crop"] == "Soybean"
    assert result["district"] == "Harda"
    assert result["savings_message_en"]
