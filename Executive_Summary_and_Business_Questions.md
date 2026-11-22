# Ride-sharing analytics — executive summary

**Analysis date:** 2026-11-22 · **Source coverage:** rides from 2025-01-30 to 2025-07-31 · **Currency:** ₹ as implied by the assignment.

## Five findings

1. **Customer master integrity is the most urgent analytical risk.** The Users sheet has 1,200 rows but only 602 distinct UserIDs; 349 repeated IDs have conflicting attributes. Customer cohorts, referrals, loyalty, and user support joins may be overstated or misattributed.
2. **The completed ride share is 90.2%.** 4,690 of 5,200 rides are Completed, 354 Cancelled, and 156 No-show. Hyderabad has the highest cancellation share (8.1%); Chennai is lowest (5.5%).
3. **Payment failures vary by channel.** Wallet is highest at 4.8%; Credit Card is lowest at 3.3%. This is a 1.5 percentage-point gap on this synthetic sample, not sufficient evidence to change a vendor contract.
4. **Ratings indicate a substantial experience opportunity.** 48.7% of ride ratings are below 3/5. Driver coaching and complaint follow-up should focus on low-rated trips, while checking whether generated values and rating scale are trustworthy.
5. **Fare per kilometre is tightly clustered across vehicle categories.** Bike averages about ₹22.87/km, Sedan ₹22.83/km, and the lowest listed class about ₹22.56/km. The difference is small; prioritize experience and city-specific economics over a fleet-wide vehicle shift.

## Three recommendations

1. Establish a canonical customer identity rule and resolve conflicting UserID records before publishing retention, referral, or customer lifetime value KPIs.
2. Investigate Wallet failures and Hyderabad cancellations at transaction/ride level; check ticket details and operational context before changing partnerships or incentives.
3. Launch a low-rating recovery workflow, then monitor rating and repeat usage using a consistent time window and validated customer identifiers.

## SQL checkpoint: five observations

- Wallet rides over 30 km that completed successfully can be filtered directly at ride grain; fare method totals in Excel reconcile to SQL when using `Rides.PaymentMethod` and all statuses.
- Driver ride counts average 16.25 in this extract (320 drivers; range 7–31 rides). The Drivers master `TotalRides` field is orders of magnitude larger and does not match the observed ride sample; use ride-level counts for this sample.
- Recent-60-day driver inactivity cannot be meaningfully interpreted as current behavior because all ride dates end July 2025. The SQL query returns no recent activity as of 2026-11-22.
- The top-level payment failure rate is 4.0% (87 failed of 2,200 transactions); Wallet is highest (4.8%). Payment table counts must not be joined raw to ride totals because payment-to-ride multiplicity is not guaranteed.
- Ticket categories are led by Other (64), Driver Misbehavior (50), and Payment Issue (49). There are 57 tickets not marked Resolved. The unmatched/conflicting customer identifiers require caution on customer attribution.

## Stage 5 business questions

The following answers use available fields and explicitly distinguish supported results from unsupported conclusions. “Not estimable” means the source lacks the needed time granularity, trustworthy identity, or event fields; it is not a zero unless stated.

| # | Finding and evidence | Action / limitation |
|---|---|---|
| 1 | Top 5% by observed driver count is about 16 drivers. Rank using ride-level ratings, completion and volume in SQL; master `TotalRides` is inconsistent with this extract. | Recognize high-rated, high-completion drivers and test retention offers. City/vehicle patterns are descriptive and sample sizes are small. |
| 2 | Compare route average duration per km; the supplied route data includes unusually long distances and durations (e.g. 563.4 km, 662 minutes). | Validate route/location semantics before treating these as urban routes; they may be synthetic outliers. Use route percentile flags before dispatch changes. |
| 3 | Promo-linked payment rows show lower average payment amount (₹572 vs ₹575) but slightly higher average tip (₹50.96 vs ₹49.75); linked ride fare averages ₹19,149 vs ₹20,150. | Do not infer promo causality or loyalty: there is no randomized assignment, valid user dimension, or reliable month-by-user promo history. Keep targeted tests. |
| 4 | New-driver success is not testable as written: the dates are frozen in 2025 and driver observed ride records are only 7–31 each, unlike master totals. | Recompute days since join using ride-date windows and a validated activity denominator when operational event history is available. |
| 5 | User activity drop over the last three months cannot be assessed; there are no dates after July 2025. Duplicate/conflicting UserIDs further block user trajectories. | Obtain a recent event extract and canonical IDs; then compare rolling 90-day ride frequency and ticket/rating history. |
| 6 | Failure rates: Wallet 4.8%, Cash 4.6%, UPI 3.9%, Credit Card 3.3%. Payment Issue has 49 tickets; refunds are not identified as a separate ticket type. | Audit Wallet transaction codes and ticket narratives. No gateway partnership decision without controlled diagnosis. |
| 7 | Possible fraud cannot be established: IDs recur with conflicting names and repeated promo flags are not linked to reliable account history. | Treat as a data-quality and audit lead only. Require device/account/payment linkage, policy thresholds and human review before action. |
| 8 | Demand exceeding driver availability cannot be calculated; no timestamp/hour or supply/online driver data are supplied. | Add trip start time and driver availability/acceptance events; then estimate demand-supply by city/time and test incentives. |
| 9 | City revenue per user is unsafe because Users IDs are duplicated/conflicting. Complaint volume can be tabulated, but ticket city is inferred from linked ride origin. | Resolve identity and geographies before allocating city marketing or driver acquisition. |
| 10 | More-than-five rides per month cannot be reliably measured: timestamps are date-only, and the period is just six months in 2025; Users master totals conflict with ride counts. | Produce monthly distinct-user cohorts after identity resolution and clarify whether “more than 5” means per calendar month or average. |
| 11 | Bike has the highest mean fare/km (₹22.87); Sedan is close (₹22.83). Ride rating means are low across classes (about 2.98–3.07/5), with Bike highest at 3.07. | The spread is narrow; compare confidence intervals, completed-only fare and city mix before fleet prioritization. |
| 12 | Unresolved ticket counts: Other 20, Driver Misbehavior 12, Overcharging 10, Ride Cancelled 8, Payment Issue 7. Escalation is not a supplied status. | Prioritize unresolved “Other” for taxonomy cleanup and Driver Misbehavior follow-up. Segment by user frequency only after IDs are fixed. |
| 13 | Long trips and very high duration exist, but driver-specific same-distance residuals are not evidence of driving patterns without traffic/time context. | Compare duration to distance bands and route baseline, then validate with timestamps/traffic data before coaching. |
| 14 | Active drivers with fewer than 10 rides last month cannot be assessed because there are no rides in the last month of the analysis date (2026-11-22). | A current-window report requires fresh ride data; avoid interpreting the empty period as churn. |
| 15 | Referral effectiveness is not robustly estimable: Users has duplicate IDs and no trustworthy customer-level revenue linkage. | Repair IDs and compare matched cohorts on tenure/city before changing referral bonuses. |

## Assumptions and limitations

- “Revenue by payment channel” in the Excel preparation uses ride Fare grouped by the ride’s PaymentMethod, as requested; transaction amount and payment status are analyzed separately from Payments.
- Total ride revenue is Fare + Tip. Payment transaction amounts are not added to ride revenue because that would mix grains and could double count.
- Completion rate is Completed rides divided by all recorded rides. Cancellation rate is Cancelled divided by all recorded rides (No-show remains separate).
- Tip percentage is Tip/Fare; rows with zero fare would be excluded from the ratio.
- Data is synthetic and contains extreme distance/fare values. Revenue average is therefore heavily skewed; inspect medians and percentiles before business use.
- User duplicate IDs are retained in raw and analysis tabs for audit; no record has been deleted or arbitrarily canonicalized.
- Power BI calculations and model instructions are supplied, but no native PBIX is included. See `PowerBI_Implementation_Pack.md`.
