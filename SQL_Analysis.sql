-- Ride Sharing Analytics | SQLite-compatible queries
-- Source tables: ride_sharing.db (cleaned text/date parsing, source rows preserved)
-- Grain: Rides=RideID, Payments=PaymentID, SupportTickets=TicketID. Aggregate child facts before joining.
-- Fixed reporting date: 2026-11-22. Users.UserID is NOT unique in supplied source.

-- 1 Users joined in 2024 and referred
SELECT * FROM Users WHERE strftime('%Y',JoinDate)='2024' AND upper(ReferralUsed)='YES';
-- 2 Long completed Wallet rides
SELECT * FROM Rides WHERE Distance_km>30 AND PaymentMethod='Wallet' AND Status='Completed';
-- 3 Ride count per driver
SELECT DriverID,COUNT(*) RideCount FROM Rides GROUP BY DriverID ORDER BY RideCount DESC;
-- 4 Drivers with no completed ride in last 60 days as of 2026-11-22
SELECT d.DriverID,d.Name FROM Drivers d LEFT JOIN Rides r ON r.DriverID=d.DriverID AND r.Status='Completed' AND r.RideDate>=date('2026-11-22','-60 day') GROUP BY d.DriverID,d.Name HAVING COUNT(r.RideID)=0;
-- 5 Unresolved tickets with user and ride context; user join may fan out due duplicate IDs
SELECT t.TicketID,t.Status,u.Name,r.RideDate,t.IssueType FROM SupportTickets t LEFT JOIN Users u ON u.UserID=t.UserID LEFT JOIN Rides r ON r.RideID=t.RideID WHERE t.Status<>'Resolved';
-- 6 Average fare per driver vehicle type
SELECT d.VehicleType,AVG(r.Fare) AvgFare FROM Rides r JOIN Drivers d USING(DriverID) GROUP BY d.VehicleType;
-- 7 Completed ride count per method and city
SELECT Start_Location City,PaymentMethod,COUNT(*) CompletedRides FROM Rides WHERE Status='Completed' GROUP BY Start_Location,PaymentMethod;
-- 8 Average distance and duration per driver
SELECT DriverID,AVG(Distance_km) AvgDistance,AVG(Duration_min) AvgDuration FROM Rides GROUP BY DriverID;
-- 9 Drivers ranked by mean tip/fare ratio
SELECT DriverID,AVG(Tip/NULLIF(Fare,0)) AvgTipFareRatio FROM Rides GROUP BY DriverID ORDER BY AvgTipFareRatio DESC;
-- 10 Ticket volume by issue type and city (city based on ride origin)
SELECT t.IssueType,r.Start_Location City,COUNT(*) Tickets FROM SupportTickets t LEFT JOIN Rides r USING(RideID) GROUP BY t.IssueType,r.Start_Location;
-- 11 Rank drivers within home city by completed ride volume
WITH x AS (SELECT d.DriverID,d.City,COUNT(CASE WHEN r.Status='Completed' THEN 1 END) CompletedRides FROM Drivers d LEFT JOIN Rides r USING(DriverID) GROUP BY d.DriverID,d.City) SELECT *,RANK() OVER(PARTITION BY City ORDER BY CompletedRides DESC) CityRank FROM x;
-- 12 Cumulative ride revenue per user by date
SELECT UserID,RideDate,RideID,Fare+Tip Revenue,SUM(Fare+Tip) OVER(PARTITION BY UserID ORDER BY RideDate,RideID ROWS UNBOUNDED PRECEDING) CumulativeRevenue FROM Rides;
-- 13 Last ride per user
SELECT UserID,MAX(RideDate) LastRideDate FROM Rides GROUP BY UserID;
-- 14 Running average fare per user through each ride
SELECT UserID,RideDate,RideID,AVG(Fare) OVER(PARTITION BY UserID ORDER BY RideDate,RideID ROWS UNBOUNDED PRECEDING) RunningAvgFare FROM Rides;
-- 15 Ticket users who never tipped
SELECT DISTINCT t.UserID FROM SupportTickets t WHERE NOT EXISTS(SELECT 1 FROM Rides r WHERE r.UserID=t.UserID AND r.Tip>0);
-- 16 Drivers with strictly rising monthly rating averages for their last three observed months
WITH monthly AS (SELECT DriverID,strftime('%Y-%m',RideDate) Month,AVG(Rating) AvgRating FROM Rides GROUP BY DriverID,Month), ranked AS (SELECT *,ROW_NUMBER() OVER(PARTITION BY DriverID ORDER BY Month DESC) rn FROM monthly), last3 AS (SELECT DriverID,MAX(CASE WHEN rn=1 THEN AvgRating END) m1,MAX(CASE WHEN rn=2 THEN AvgRating END) m2,MAX(CASE WHEN rn=3 THEN AvgRating END) m3,COUNT(*) n FROM ranked WHERE rn<=3 GROUP BY DriverID) SELECT DriverID,m3,m2,m1 FROM last3 WHERE n=3 AND m1>m2 AND m2>m3;
-- 17 Top three cities by total fare+tip (subquery)
SELECT * FROM (SELECT Start_Location City,SUM(Fare+Tip) Revenue FROM Rides GROUP BY Start_Location) ORDER BY Revenue DESC LIMIT 3;
-- 18 Driver rides starting in their home city
SELECT d.DriverID,d.City,COUNT(r.RideID) HomeCityRides FROM Drivers d LEFT JOIN Rides r ON r.DriverID=d.DriverID AND r.Start_Location=d.City GROUP BY d.DriverID,d.City;
-- 19 Most common vehicle among drivers whose master TotalRides exceeds 1000
SELECT VehicleType,COUNT(*) Drivers FROM Drivers WHERE TotalRides>1000 GROUP BY VehicleType ORDER BY Drivers DESC LIMIT 1;
-- 20 More than five rides and no successful payment
SELECT r.UserID,COUNT(DISTINCT r.RideID) RideCount FROM Rides r GROUP BY r.UserID HAVING COUNT(DISTINCT r.RideID)>5 AND NOT EXISTS(SELECT 1 FROM Rides rr JOIN Payments p USING(RideID) WHERE rr.UserID=r.UserID AND p.Status='Success');
-- 21 Highest average fare per minute for rides >10km
SELECT DriverID,AVG(Fare/NULLIF(Duration_min,0)) AvgFarePerMinute FROM Rides WHERE Distance_km>10 GROUP BY DriverID ORDER BY AvgFarePerMinute DESC;

-- Additional validation queries for Excel findings
SELECT Status,COUNT(*) RideCount FROM Rides GROUP BY Status;
SELECT PaymentMethod,SUM(Fare) Fare FROM Rides GROUP BY PaymentMethod ORDER BY Fare DESC;
SELECT COUNT(*) Rows,COUNT(DISTINCT UserID) DistinctUserIDs FROM Users;
SELECT PromoApplied,Status,COUNT(*) Transactions FROM Payments GROUP BY PromoApplied,Status;
