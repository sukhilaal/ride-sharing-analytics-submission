# Power BI implementation pack

## Model and relationships

Use the cleaned tables in `ride_sharing.db` or the corresponding `Raw_*` workbook tabs. Keep the analytical model at separate fact grains; never merge Payments or SupportTickets directly into Rides at row level because multiple child rows can multiply ride values.

Recommended model:

- `Rides` is the ride fact table (one row per RideID).
- `Drivers` and a deduplicated, reviewed `Users_Dim` are dimensions.
- `Payments` and `SupportTickets` remain separate fact tables at transaction and ticket grain.
- Add a Date table and optional Location/PaymentMethod dimensions. Link dimensions one-to-many to facts with single-direction filtering.
- Do not create an active Users relationship until the duplicate UserID mapping is resolved. A many-to-many relationship can inflate customer counts and should not be used as a workaround.

`Users_Dim` cannot be safely created by keeping an arbitrary first row: 349 of the repeated IDs have conflicting attributes. Resolve against a trusted source or apply an explicitly approved canonicalization rule first.

## Power Query preparation

1. Import five sheets/tables; set IDs and categorical fields to Text, dates to Date, distance/duration/fare/tip/ratings to Decimal/Whole Number as appropriate, and IsActive to True/False.
2. Trim text values, standardize ReferralUsed/PromoApplied to uppercase, and check date parse errors.
3. Preserve source records and create a duplicate-ID audit for Users. Do not remove duplicates silently.
4. Add these calculated columns to Rides:

```DAX
Fare per km = DIVIDE(Rides[Fare], Rides[Distance_km])
Total revenue = Rides[Fare] + Rides[Tip]
Ride value = SWITCH(TRUE(), Rides[Fare] > 500, "High Value", Rides[Fare] >= 200, "Medium", "Low Value")
Long duration = Rides[Duration_min] > 60
Tip % = DIVIDE(Rides[Tip], Rides[Fare])
```

## Measures

```DAX
Ride Count = DISTINCTCOUNT(Rides[RideID])
Completed Rides = CALCULATE([Ride Count], Rides[Status] = "Completed")
Completion Rate = DIVIDE([Completed Rides], [Ride Count])
Average Fare = AVERAGE(Rides[Fare])
Total Revenue = SUMX(FILTER(Rides, Rides[Status] = "Completed"), Rides[Fare] + Rides[Tip])
Average Tip % = AVERAGEX(Rides, DIVIDE(Rides[Tip], Rides[Fare]))
Failed Transactions = CALCULATE(DISTINCTCOUNT(Payments[PaymentID]), Payments[Status] = "Failed")
Payment Failure Rate = DIVIDE([Failed Transactions], DISTINCTCOUNT(Payments[PaymentID]))
Active Drivers Last 30 Days =
VAR Cutoff = TODAY() - 30
RETURN CALCULATE(DISTINCTCOUNT(Rides[DriverID]), Rides[Status] = "Completed", Rides[RideDate] > Cutoff, Drivers[IsActive] = TRUE())
```

The revenue measure sums fare and tip at ride grain, avoiding accidental multiplication from payment or ticket rows.

## Report pages and visuals

1. **Overview:** KPI cards for ride count, completion rate, completed revenue, payment failure rate; slicers for start city, vehicle type and payment method; monthly ride trend.
2. **Operations:** route matrix (Start_Location × End_Location, ride count), cancellation rate by origin city, hour/day demand, long-duration share.
3. **Drivers:** top-five drivers by ride-level average rating with city, vehicle, completed ride volume; driver revenue; active-driver KPI. Use the ride-level rating for rankings and show driver master AvgRating separately.
4. **Customer & support:** issue type ticket count with ticket/ride/user detail drill-through; average resolution days by issue; unresolved/escalated ticket counts. Clearly flag user-level findings as provisional until UserID deduplication is addressed.
5. **Revenue & promotions:** fare per km by vehicle, fare-distance scatter with RideID/DriverName/City tooltip, promo YES/NO payment amount and ride-tip comparison.

## Date-sensitive measures and limitations

The supplied rides cover 2025-01-30 through 2025-07-31. With the fixed analysis date 2026-11-22, a current-year repeat-user measure and last-30-day active-driver measure return zero because no rides fall in those windows. For demonstrating those visuals, use a user-selected period within the data coverage and label it clearly; do not claim it is the current year. Promotion/payment data is synthetic and observational, so observed differences are associations rather than causal effects.

This folder contains the Power BI model and report specification; a `.pbix` file has not been generated in this environment.
