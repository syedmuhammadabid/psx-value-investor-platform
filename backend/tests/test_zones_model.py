"""Unit tests for the buy & sell zone model."""

from __future__ import annotations

import pytest

from app.valuation import zones


class TestZoneBounds:
    def test_returns_four_ascending_boundaries(self) -> None:
        bounds = zones.zone_bounds(400.0)
        assert bounds == pytest.approx((300.0, 360.0, 440.0, 500.0))

    @pytest.mark.parametrize("intrinsic", [0.0, -10.0])
    def test_non_positive_intrinsic_returns_none(self, intrinsic: float) -> None:
        assert zones.zone_bounds(intrinsic) is None


class TestPriceBands:
    def test_returns_five_ordered_bands(self) -> None:
        bands = zones.price_bands(400.0)
        assert bands is not None
        names = [name for name, _, _ in bands]
        assert names == list(zones.ZONE_NAMES)
        # First band is unbounded below, last is unbounded above.
        assert bands[0][1] is None
        assert bands[-1][2] is None
        # Bands are contiguous: each upper equals the next lower.
        for (_, _, upper), (_, lower, _) in zip(bands, bands[1:], strict=False):
            assert upper == lower

    def test_invalid_intrinsic_returns_none(self) -> None:
        assert zones.price_bands(0.0) is None


class TestClassifyZone:
    @pytest.mark.parametrize(
        ("price", "expected"),
        [
            (250.0, "STRONG_BUY"),  # below 300
            (299.99, "STRONG_BUY"),
            (300.0, "BUY"),  # boundary is lower-inclusive
            (350.0, "BUY"),
            (360.0, "HOLD"),
            (420.0, "HOLD"),
            (441.0, "SELL"),
            (480.0, "SELL"),
            (500.0, "STRONG_SELL"),  # boundary is lower-inclusive
            (600.0, "STRONG_SELL"),
        ],
    )
    def test_classifies_price_into_band(self, price: float, expected: str) -> None:
        assert zones.classify_zone(400.0, price) == expected

    def test_invalid_intrinsic_returns_none(self) -> None:
        assert zones.classify_zone(0.0, 100.0) is None
