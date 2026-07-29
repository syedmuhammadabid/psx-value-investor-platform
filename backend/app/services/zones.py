"""Buy & sell zones service — turns intrinsic value into price bands."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.zones import BuySellZones, PriceZone, ZoneName
from app.services import valuation as valuation_service
from app.valuation import zones as zones_model

_LABELS: dict[ZoneName, str] = {
    ZoneName.STRONG_BUY: "Strong Buy",
    ZoneName.BUY: "Buy",
    ZoneName.HOLD: "Hold",
    ZoneName.SELL: "Sell",
    ZoneName.STRONG_SELL: "Strong Sell",
}


def get_zones(db: Session, symbol: str) -> BuySellZones:
    """Return the five price bands for a company (404 if it does not exist)."""
    valuation = valuation_service.get_valuation(db, symbol)
    intrinsic = valuation.intrinsic_value
    price = valuation.current_price

    if intrinsic is None:
        return BuySellZones(
            symbol=valuation.symbol,
            current_price=price,
            zones=[],
        )

    current = zones_model.classify_zone(intrinsic, price) if price is not None else None
    bands = zones_model.price_bands(intrinsic) or []
    zones = [
        PriceZone(
            name=ZoneName(name),
            label=_LABELS[ZoneName(name)],
            lower=lower,
            upper=upper,
            is_current=name == current,
        )
        for name, lower, upper in bands
    ]

    return BuySellZones(
        symbol=valuation.symbol,
        intrinsic_value=intrinsic,
        current_price=price,
        current_zone=ZoneName(current) if current is not None else None,
        zones=zones,
    )
