# Trade note: short Venture Global (VG), long Cheniere (LNG)

October 9, 2026 (v15). Prices are October 7 closes: VG $13.05, LNG $272.20. Not investment advice.

## The idea

Both companies export US Gulf Coast LNG and get paid fees over Henry Hub. The difference is how much of their value depends on the uncontracted spread in the 2030s.

- Venture Global: 42% of 2029 is contracted, and that share is falling. Each $1 of long-run fee is worth about $4.10 a share, 31% of the price (`scripts/model_v10.py`). The price needs about $4.49 a year from 2032, above what recent US greenfield plants need to earn 8% over their life ($2.68-3.00 on developers' FID costs; v14). The CME curve (October 7) has $3.80 for 2030 and $2.50 for 2031.
- Cheniere: "90% or more" of output contracted through the mid-2030s (Q2 2026 10-Q), so $1 of long-run margin is worth about $5-11 a share, roughly 2-4% of its price (VG: 31%); pair payoffs are the same at either end (model_v14_addons.py); under 1 Mt of 2026 volume unsold, a $2.50–3.00 long-run margin in its own planning, about 5% a year of buybacks, and plants that already pay out (Cheniere Partners paid $0.82 a unit for Q2 2026).

The pair keeps the part of the thesis that matters and hedges out most of the US LNG sector and the market.

## Sizing

From daily total-return prices since the war began on 27 Feb 2026 (`scripts/pair_v7.py`, `data/prices_vg_lng_spy_daily.csv`):

| | |
|---|---|
| VG volatility | 78% |
| LNG volatility | 33% |
| Correlation | 0.63 |
| Beta of VG on LNG | 1.51 |
| Hedge | $1.51 of LNG long per $1 of VG short |
| Pair volatility, beta-hedged | about 60% |
| Pair volatility, dollar-neutral | about 62% |

The pair still runs about 60% volatility after hedging, because most of it is VG's own risk, and that risk is the bet. Size it as a small, high-volatility position, not as a hedged spread.

## Carry and borrow

- Borrow on VG: 0.41% a year, 10 million shares available at Interactive Brokers (IBorrowDesk, 7 Oct 2026, 4:43 PM).
- Dividends: the short pays VG's $0.16 a year (1.2%). The long receives LNG's $2.22 a year (0.8%) on 1.51 times the notional.
- Net carry: about -0.4% a year per $1 of VG short.

## What makes money, and when

| Date | Catalyst |
|---|---|
| 29 Oct 2026 | Cheniere Q3 results |
| ~31 Oct 2026 | Plaquemines Phase 1 COD |
| 9 Nov 2026 | VG Q3 results. Likely a guidance raise, which is a near-term headwind for the pair. |
| Feb/Mar 2027 | VG Q4 deck: 2029 contracted share (call #236) |
| May 2027 | BP damages hearing |
| 2H 2027 | CP2 first LNG |
| 2027–2028 | Any reported fee on new 2029–31 contracts (call #237) |

## What kills it

1. Management's 2029 framework: about $11bn of EBITDA at a $3 fee. If that holds, VG needs only a $2.32 long-run fee and the short is wrong.
2. VG contracts 2029–31 volume at $4.49 or more for three years or longer. This is J.P. Morgan's bull case.
3. The 2030 JKM strip trades above $12. It's about $10 now.
4. A squeeze. Only the roughly 530 million Class A shares trade, with 8.4% of the float short (43.6 million shares, S&P Global via StockAnalysis, checked October 8).

## Honest edge (model_v13_addons.py)

Of the +25% weighted pair return, about 20 points is simply being long 1.51x Cheniere's expected return and under 1 point is borrow. The VG-specific part is about +5 points over 24 months against roughly 85% two-year volatility. Size it as a small expression of the rating, not as a standalone trade. The Jan-2029 $12.50/$10 put spread costs ~$1.20 at mid and ~$1.55 at the offer (8 Oct quotes) against an expected payoff of ~$1.18 on my weights.

## Expected payoff (model_v12_addons.py)

Per $1 of VG short over 24 months, with Cheniere earning its CAPM return (beta 0.31 since IPO, ~6.6% a year) adjusted for its small long-run-fee exposure, borrow included: bear +66%, base +31%, bull -4%, management framework -47%; weighted (25/45/20/10) +25%. About 21 points of the base case is simply 1.51x Cheniere's expected return. Break-even: VG returns about +20% (~$15.30).

## Alternative: put spread

January 2029 $12.50/$10 put spread: last trades $3.40 (Oct 5) and $2.20 (Oct 7), so about $1.20 for a $2.50 maximum. At the end-2028 scenario values: bear ($6.29) pays $2.50 (+108%), base ($11.27) pays about $1.23 (+3%), bull ($16.24) pays nothing. Re-price at the open; these are last trades, not quotes.

## Review points

- Re-run the model after VG's Q3 deck (`REFRESH_NOV9.md`).
- Rethink the trade if the 2029 contracted share jumps above 50% at fees above $4.49, or if the 2030 JKM strip moves above $12.

## Scoring (ledger #231)

- Entry: the closes before publication.
- Return: total return of (-1 × VG + 1.51 × LNG) as a fraction of the VG notional, over 24 months.
- WIN if that return is positive.


## v14 note

I keep this pair on the record as a low-conviction call and say so in the piece: of the ~+25% weighted return, ~+20 points is 1.51x Cheniere's expected return and only ~+5 points is VG-specific, against ~85% two-year volatility. On 2026 guidance VG trades at 8.9x EV/EBITDA vs Cheniere's 11.6x; the gap is VG's war-year EBITDA, not a mispricing (10.6x on my 2031 EBITDA).


## v15 note

The January 2029 $12.50 put had only 22 contracts of open interest on October 8; treat that leg as illiquid. The full Jan-2029 chain implies about a 45% chance VG is below $8.75 and 24% above $18.75 by expiry (risk-neutral, overstates both tails), median about $9.80. Trailing EV/EBITDA: VG 10.7x, Cheniere 12.0x, Cheniere Partners 9.8x.
