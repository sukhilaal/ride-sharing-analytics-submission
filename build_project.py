from pathlib import Path
import pandas as pd, numpy as np, sqlite3, json
from datetime import date
from xlsxwriter.utility import xl_col_to_name

ROOT=Path.cwd(); SRC=Path(r'C:\Users\omsri\Downloads\RIDE_SHARING_DATA.xlsx'); ASOF=pd.Timestamp('2026-11-22')
tabs={s:pd.read_excel(SRC,sheet_name=s) for s in ['Rides','Drivers','Users','Payments','SupportTickets']}
for d in tabs.values():
    for c in d.select_dtypes('object').columns: d[c]=d[c].astype('string').str.strip()
r,d,u,p,t=[tabs[x] for x in ['Rides','Drivers','Users','Payments','SupportTickets']]
r['RideDate']=pd.to_datetime(r.RideDate); d['JoinDate']=pd.to_datetime(d.JoinDate); u['JoinDate']=pd.to_datetime(u.JoinDate); p['PaymentDate']=pd.to_datetime(p.PaymentDate); t['OpenDate']=pd.to_datetime(t.OpenDate); t['CloseDate']=pd.to_datetime(t.CloseDate)
r['TotalRevenue']=r.Fare+r.Tip; r['FarePerKm']=r.Fare/r.Distance_km.replace(0,np.nan); r['TipPct']=r.Tip/r.Fare.replace(0,np.nan); r['LowRatingFlag']=np.where(r.Rating<3,'Investigate','OK'); r['FareValue']=np.select([r.Fare>500,r.Fare>=200],['High Value','Medium'],default='Low Value'); r['LongDuration']=r.Duration_min>60; r['RatingBand']=pd.cut(r.Rating,[0,2,3,4,5],labels=['1-2','2-3','3-4','4-5'],include_lowest=True,right=True).astype('string'); r['RideMonth']=r.RideDate.dt.month_name(); r['DaysSinceRide']=(ASOF-r.RideDate).dt.days
drivers=d[['DriverID','Name','City','VehicleType','AvgRating','IsActive','JoinDate']].rename(columns={'Name':'DriverName','City':'DriverCity','AvgRating':'DriverMasterRating'}); r=r.merge(drivers,on='DriverID',how='left',validate='many_to_one')
u['FirstName']=u.Name.str.split().str[0]; u['LastName']=u.Name.str.split().str[-1];u['CustomerTag']=u.FirstName.str[:3].str.upper()+u.UserID.str.replace(r'\D','',regex=True);u['DummyEmail']=(u.FirstName+u.LastName).str.lower()+'@riderapp.com';u['TenureDays']=(ASOF-u.JoinDate).dt.days
p['PromoApplied']=p.PromoApplied.str.upper();
for c in ['Status','PaymentMethod','IssueType','City','VehicleType','ReferralUsed']: 
    if c in r: r[c]=r[c].astype('string').str.strip()

# Analyses
payrev=r.groupby('PaymentMethod',dropna=False).agg(Rides=('RideID','count'),Fare=('Fare','sum'),Tips=('Tip','sum'),Revenue=('TotalRevenue','sum')).reset_index().sort_values('Revenue',ascending=False)
veh=d.merge(r.groupby('DriverID').agg(RideCount=('RideID','count'),Fare=('Fare','sum'),Tips=('Tip','sum')),on='DriverID',how='left').groupby('VehicleType').agg(Fare=('Fare','sum'),Tips=('Tips','sum'),RideCount=('RideCount','sum')).reset_index();
ctip=r.groupby(['DriverCity','VehicleType']).Tip.mean().reset_index(name='AverageTip')
driveractivity=r.groupby(['DriverID','DriverName','DriverCity','VehicleType']).agg(Rides=('RideID','count'),Completed=('Status',lambda s:(s=='Completed').sum()),AvgRating=('Rating','mean'),Fare=('Fare','sum'),Tip=('Tip','sum')).reset_index()
ratingdist=r.groupby('RatingBand',dropna=False).size().reset_index(name='RideCount')
promopay=p.groupby(['PromoApplied','Status']).agg(Transactions=('PaymentID','count'),Amount=('Amount','sum'),AvgAmount=('Amount','mean')).reset_index()
userduplicates=u.groupby('UserID').agg(Rows=('UserID','size'),Names=('Name','nunique'),JoinDates=('JoinDate','nunique'),Cities=('City','nunique')).reset_index(); userduplicates=userduplicates[userduplicates.Rows>1]
monthly=r.groupby(r.RideDate.dt.to_period('M').astype(str)).agg(Rides=('RideID','count'),Fare=('Fare','sum'),Tips=('Tip','sum')).reset_index()
ticketissues=t.groupby(['IssueType','Status']).size().unstack(fill_value=0).reset_index()
promo_behavior=p.merge(r[['RideID','UserID','Tip','Fare','Status']],on='RideID',how='left').groupby('PromoApplied').agg(PaymentRows=('PaymentID','count'),AvgPayment=('Amount','mean'),Successful=('Status_x',lambda x:(x=='Success').sum())).reset_index() if False else p.groupby('PromoApplied').agg(PaymentRows=('PaymentID','count'),AvgPayment=('Amount','mean'),SuccessRate=('Status',lambda s:(s=='Success').mean())).reset_index()
joined=d.merge(driveractivity[['DriverID','Rides','Completed','AvgRating']],on='DriverID',how='left');joined['RideCompletionRate']=joined.Completed/joined.Rides
city_cancel=r.assign(Cancel=(r.Status=='Cancelled').astype(int)).groupby('Start_Location').agg(Rides=('RideID','count'),Cancelled=('Cancel','sum')).reset_index();city_cancel['CancellationRate']=city_cancel.Cancelled/city_cancel.Rides
routes=r.groupby(['Start_Location','End_Location']).agg(Rides=('RideID','count'),AvgDistance=('Distance_km','mean'),AvgDuration=('Duration_min','mean'),AvgFare=('Fare','mean')).reset_index();routes['DurationPerKm']=routes.AvgDuration/routes.AvgDistance
ticket_perf=t.assign(ResolutionDays=(t.CloseDate-t.OpenDate).dt.days).groupby('IssueType').agg(Tickets=('TicketID','count'),AvgResolutionDays=('ResolutionDays','mean'),Unresolved=('Status',lambda s:(s!='Resolved').sum())).reset_index()
pay_methods=p.groupby('PaymentMethod').agg(Transactions=('PaymentID','count'),Failed=('Status',lambda s:(s=='Failed').sum())).reset_index();pay_methods['FailureRate']=pay_methods.Failed/pay_methods.Transactions
promo_r=p.merge(r[['RideID','Tip','Fare']],on='RideID',how='left').groupby('PromoApplied').agg(Payments=('PaymentID','count'),AvgAmount=('Amount','mean'),AvgFare=('Fare','mean'),AvgTip=('Tip','mean')).reset_index()

# Excel workbook
out=ROOT/'Ride_Sharing_Submission.xlsx'
with pd.ExcelWriter(out,engine='xlsxwriter',datetime_format='yyyy-mm-dd',date_format='yyyy-mm-dd') as w:
    wb=w.book; navy='#17365D'; teal='#0F6B78'; fmt=wb.add_format({'bold':True,'font_color':'white','bg_color':navy,'text_wrap':True,'valign':'vcenter'}); money=wb.add_format({'num_format':'₹#,##0.00'}); pct=wb.add_format({'num_format':'0.0%'}); datefmt=wb.add_format({'num_format':'yyyy-mm-dd'})
    def put(name,df):
        df.to_excel(w,sheet_name=name,index=False); sh=w.sheets[name]; sh.freeze_panes(1,0); sh.autofilter(0,0,len(df),max(len(df.columns)-1,0));sh.set_row(0,30,fmt)
        for i,col in enumerate(df.columns):
            vals=df[col].astype(str).head(100); width=min(max(12,len(str(col))+2,*(len(x)+1 for x in vals)),32); sh.set_column(i,i,width)
        return sh
    intro=pd.DataFrame({'Section':['Purpose','As-of date','Source','Cleaning policy','Model grain','Important caveat'], 'Notes':['End-to-end ride-sharing analytics; findings are calculated from supplied synthetic workbook.','2026-11-22 (fixed for reproducibility).','RIDE_SHARING_DATA.xlsx; raw source sheets retained below.','Trim text; parse dates; preserve source rows; add derived fields. No source records removed.','Rides one row per RideID; Payments one row per PaymentID; tickets one row per TicketID. Link via keys and aggregate child tables before joining.','Users has 1,200 rows but only 602 distinct UserIDs; 349 IDs have conflicting attributes. Do not treat Users.UserID as a unique dimension until deduplication rules are supplied. Dates span 2025-01-30 to 2025-07-31, so current year/last 30 days as of 2026-11-22 are not represented.']});put('Read Me',intro)
    for n,df in tabs.items(): put('Raw_'+n,df)
    sh=put('Rides_Analysis',r); sh.conditional_format(1,r.columns.get_loc('Rating'),len(r),r.columns.get_loc('Rating'),{'type':'cell','criteria':'<','value':3,'format':wb.add_format({'bg_color':'#FFC7CE','font_color':'#9C0006'})});sh.conditional_format(1,r.columns.get_loc('Fare'),len(r),r.columns.get_loc('Fare'),{'type':'3_color_scale'});sh.conditional_format(1,r.columns.get_loc('Duration_min'),len(r),r.columns.get_loc('Duration_min'),{'type':'icon_set','icon_style':'3_arrows'});sh.conditional_format(1,r.columns.get_loc('TipPct'),len(r),r.columns.get_loc('TipPct'),{'type':'cell','criteria':'>','value':0.2,'format':wb.add_format({'bg_color':'#FFEB9C','font_color':'#9C6500'})})
    for n,df in [('Users_Analysis',u),('Revenue by Method',payrev),('Vehicle Summary',veh),('City Vehicle Tips',ctip),('Driver Activity',driveractivity),('Rating Distribution',ratingdist),('Promo Payments',promopay),('Duplicate User IDs',userduplicates),('Monthly Summary',monthly),('Ticket Issues',ticketissues),('City Cancellations',city_cancel),('Route Analysis',routes),('Ticket Resolution',ticket_perf),('Payment Reliability',pay_methods),('Promo Impact',promo_r)]: put(n,df)
    sh=w.sheets['Duplicate User IDs']; sh.conditional_format(1,0,len(userduplicates),0,{'type':'3_color_scale'})
    # key pivots/charts
    sh=w.sheets['Revenue by Method']; chart=wb.add_chart({'type':'column'});chart.add_series({'name':'Fare','categories':['Revenue by Method',1,0,len(payrev),0],'values':['Revenue by Method',1,2,len(payrev),2],'fill':{'color':teal}});chart.set_title({'name':'Fare by payment method'}); chart.set_y_axis({'name':'Fare (₹)'});sh.insert_chart('G2',chart,{'x_scale':1.25,'y_scale':1.2})
    sh=w.sheets['Vehicle Summary']; chart=wb.add_chart({'type':'bar'});chart.add_series({'name':'Fare','categories':['Vehicle Summary',1,0,len(veh),0],'values':['Vehicle Summary',1,1,len(veh),1]});chart.set_title({'name':'Fare by vehicle type'});sh.insert_chart('G2',chart)
    findings=[]
    def obs(label,value,meaning):findings.append({'Finding':label,'Evidence':value,'Interpretation / follow-up':meaning})
    obs('Ride status mix',f"{(r.Status=='Completed').mean():.1%} completed ({(r.Status=='Cancelled').sum():,} cancelled; {(r.Status=='No-show').sum():,} no-show) across {len(r):,} rides.",'Completion rate denominator is all recorded rides; cancellation analysis should be separate from no-shows.')
    obs('Revenue by payment channel',f"{payrev.iloc[0].PaymentMethod} leads at ₹{payrev.iloc[0].Fare:,.0f} fare; highest channel is {(payrev.iloc[0].Fare/payrev.Fare.sum()):.1%} of fare.",'Validate payment channel and completed-only revenue before changing gateway allocation.')
    obs('Customer master key quality',f"{u.UserID.nunique():,} distinct IDs across {len(u):,} rows; {len(userduplicates):,} IDs repeated, {int((userduplicates.Names>1).sum())} repeated IDs have multiple names.",'Resolve canonical customer mapping before user-level retention or referral claims.')
    obs('Payment reliability',f"Payment transaction failure rate is {p.Status.eq('Failed').mean():.1%} over {len(p):,} transactions; method range {pay_methods.FailureRate.min():.1%}–{pay_methods.FailureRate.max():.1%}.",'Transaction grain differs from ride grain; compare failure rates by method and investigate payment tickets.')
    obs('Promotions',f"Successful promo payments: {int(((p.PromoApplied=='YES')&(p.Status=='Success')).sum()):,} of {len(p):,} payment rows.",'Promo association is descriptive; promotional assignment is not randomized.')
    obs('Vehicle efficiency',f"Highest mean fare/km is {r.groupby('VehicleType').FarePerKm.mean().idxmax()}.",'Long-haul synthetic records may dominate fare/km; inspect distance distribution and outliers.')
    obs('Calendar coverage',f"Ride dates span {r.RideDate.min():%Y-%m-%d} through {r.RideDate.max():%Y-%m-%d}; no rides in 2026.",'Current-year repeat-user and recent-30-day driver KPIs are zero/undefined for this snapshot.')
    obs('Ratings',f"Mean ride rating {r.Rating.mean():.2f}; low ratings (<3) on {(r.Rating<3).sum():,} rides ({(r.Rating<3).mean():.1%}).",'Ride rating validity range 1–5; investigate low ratings alongside tickets and driver samples.')
    put('Excel Findings',pd.DataFrame(findings))

# SQLite cleaned tables, child facts remain separate
db=ROOT/'ride_sharing.db'
with sqlite3.connect(db) as c:
    for name,df in {'Rides':r,'Drivers':d,'Users':u,'Payments':p,'SupportTickets':t}.items(): df.to_sql(name,c,index=False,if_exists='replace')
    for name,df in {'RidePaymentSummary':p.groupby('RideID').agg(PaymentCount=('PaymentID','count'),PaymentAmount=('Amount','sum')).reset_index(),'RideTicketSummary':t.groupby('RideID').agg(TicketCount=('TicketID','count')).reset_index()}.items(): df.to_sql(name,c,index=False,if_exists='replace')

# reusable DAX and report metadata
print('BUILT',out,db)
