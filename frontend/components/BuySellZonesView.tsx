import { formatPrice } from "@/lib/format";
import type { BuySellZones, PriceZone, ZoneName } from "@/lib/types";

/** Semantic accent per band: buys are positive, hold neutral, sells negative. */
const ZONE_STYLES: Record<
  ZoneName,
  { dot: string; activeBorder: string; activeBg: string; text: string }
> = {
  STRONG_BUY: {
    dot: "bg-positive",
    activeBorder: "border-positive/50",
    activeBg: "bg-positive/10",
    text: "text-positive",
  },
  BUY: {
    dot: "bg-positive/70",
    activeBorder: "border-positive/40",
    activeBg: "bg-positive/5",
    text: "text-positive",
  },
  HOLD: {
    dot: "bg-warning",
    activeBorder: "border-warning/50",
    activeBg: "bg-warning/10",
    text: "text-warning",
  },
  SELL: {
    dot: "bg-negative/70",
    activeBorder: "border-negative/40",
    activeBg: "bg-negative/5",
    text: "text-negative",
  },
  STRONG_SELL: {
    dot: "bg-negative",
    activeBorder: "border-negative/50",
    activeBg: "bg-negative/10",
    text: "text-negative",
  },
};

/** Human-readable price range for a band, e.g. `Below Rs 300` / `Rs 300 – Rs 360`. */
function rangeLabel(zone: PriceZone): string {
  if (zone.lower == null) return `Below ${formatPrice(zone.upper)}`;
  if (zone.upper == null) return `Above ${formatPrice(zone.lower)}`;
  return `${formatPrice(zone.lower)} – ${formatPrice(zone.upper)}`;
}

function ZoneRow({ zone }: { zone: PriceZone }) {
  const style = ZONE_STYLES[zone.name];
  const border = zone.is_current ? style.activeBorder : "border-border";
  const background = zone.is_current ? style.activeBg : "bg-surface";

  return (
    <div
      className={`flex items-center justify-between gap-4 rounded-lg border ${border} ${background} px-4 py-3`}
    >
      <div className="flex items-center gap-3">
        <span className={`h-2.5 w-2.5 rounded-full ${style.dot}`} />
        <span className={`text-sm font-semibold ${style.text}`}>
          {zone.label}
        </span>
        {zone.is_current ? (
          <span className="rounded-full border border-border bg-surface-2 px-2 py-0.5 text-xs text-text-muted">
            Current price
          </span>
        ) : null}
      </div>
      <span className="text-sm font-medium tabular-nums text-text">
        {rangeLabel(zone)}
      </span>
    </div>
  );
}

export function BuySellZonesView({ zones }: { zones: BuySellZones }) {
  const hasZones = zones.zones.length > 0;

  return (
    <section id="zones" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Buy & sell zones</h2>
        <span className="text-sm text-text-muted">
          Price bands from intrinsic value
        </span>
      </div>

      {!hasZones ? (
        <p className="mt-6 text-sm text-text-muted">
          Buy and sell zones will appear once an intrinsic value can be
          estimated for this company.
        </p>
      ) : (
        <>
          <div className="mt-6 space-y-2">
            {zones.zones.map((zone) => (
              <ZoneRow key={zone.name} zone={zone} />
            ))}
          </div>
          <p className="mt-3 text-xs text-text-muted">
            Bands are derived from an intrinsic value of{" "}
            {formatPrice(zones.intrinsic_value)} using a margin-of-safety scale
            (Strong Buy ≥ 25% below, Strong Sell &gt; 25% above fair value).
          </p>
        </>
      )}
    </section>
  );
}
