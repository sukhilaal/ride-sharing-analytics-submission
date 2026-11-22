"""Render the repository summary graphic from ride_sharing.db using Pillow."""
from pathlib import Path
import sqlite3
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "assets" / "analytics-overview.png"
OUT.parent.mkdir(exist_ok=True)
db = sqlite3.connect(ROOT / "ride_sharing.db")

status = db.execute("SELECT Status, COUNT(*) FROM Rides GROUP BY Status ORDER BY CASE Status WHEN 'Completed' THEN 1 WHEN 'Cancelled' THEN 2 ELSE 3 END").fetchall()
payments = db.execute("SELECT PaymentMethod, 100.0*SUM(CASE WHEN Status='Failed' THEN 1 ELSE 0 END)/COUNT(*), COUNT(*), SUM(CASE WHEN Status='Failed' THEN 1 ELSE 0 END) FROM Payments GROUP BY PaymentMethod ORDER BY 2 DESC").fetchall()
ratings = db.execute("SELECT CASE WHEN Rating<2 THEN '1 to <2' WHEN Rating<3 THEN '2 to <3' WHEN Rating<4 THEN '3 to <4' ELSE '4 to 5' END, COUNT(*) FROM Rides GROUP BY 1 ORDER BY MIN(Rating)").fetchall()
low_ratings = db.execute("SELECT COUNT(*) FROM Rides WHERE Rating<3").fetchone()[0]
user_rows, unique_users, repeated_ids, conflicting = db.execute("""
SELECT (SELECT COUNT(*) FROM Users), (SELECT COUNT(DISTINCT UserID) FROM Users),
 (SELECT COUNT(*) FROM (SELECT UserID FROM Users GROUP BY UserID HAVING COUNT(*)>1)),
 (SELECT COUNT(*) FROM (SELECT UserID FROM Users GROUP BY UserID HAVING COUNT(DISTINCT Name)>1 OR COUNT(DISTINCT City)>1))
""").fetchone()
db.close()

W, H = 1600, 1180
im = Image.new("RGB", (W, H), "#F4F7FA")
d = ImageDraw.Draw(im)
font_dir = Path(r"C:\Windows\Fonts")
def font(name, size):
    path = font_dir / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()

regular = font("segoeui.ttf", 24)
small = font("segoeui.ttf", 19)
bold = font("segoeuib.ttf", 27)
title = font("segoeuib.ttf", 43)
big = font("segoeuib.ttf", 44)
navy, teal, orange, red = "#17324D", "#087E8B", "#E49B36", "#D45D5D"
muted, grid, white = "#5C6B78", "#E4EAF0", "#FFFFFF"

d.text((70, 48), "Ride-sharing operations | dataset snapshot", font=title, fill=navy)
d.text((72, 110), "5,200 rides · 2,200 payment transactions · 1,200 user records", font=regular, fill=muted)

kpis = [("RIDE COMPLETION", f"{next(n for s,n in status if s=='Completed')/sum(n for _,n in status):.1%}"),
        ("PAYMENT FAILURES", f"{sum(x[3] for x in payments)/sum(x[2] for x in payments):.1%}"),
        ("RATINGS BELOW 3", f"{low_ratings/sum(n for _,n in ratings):.1%}"),
        ("DISTINCT USER IDs", f"{unique_users:,} / {user_rows:,}")]
kw, gap = 348, 28
for i,(label,value) in enumerate(kpis):
    x=70+i*(kw+gap); y=165
    d.rounded_rectangle((x,y,x+kw,y+135), radius=16, fill=white, outline=grid, width=2)
    d.text((x+22,y+19),label,font=small,fill=muted)
    d.text((x+22,y+58),value,font=big,fill=teal if i<2 else (orange if i==2 else red))

panels=[(70,340,760,705),(820,340,1530,705),(70,745,760,1090),(820,745,1530,1090)]
for box in panels: d.rounded_rectangle(box, radius=16, fill=white, outline=grid, width=2)

def panel_title(x,y,text,sub):
    d.text((x+26,y+20),text,font=bold,fill=navy); d.text((x+26,y+60),sub,font=small,fill=muted)

x,y=70,340; panel_title(x,y,"Ride outcomes","Share of all recorded rides")
total=sum(n for _,n in status); startx=x+205; maxw=420
for label,n in status:
    yy=y+130+status.index((label,n))*68; frac=n/total
    d.text((x+28,yy+5),label,font=regular,fill=navy)
    d.rounded_rectangle((startx,yy,startx+maxw,yy+33),radius=8,fill="#EDF1F5")
    color=teal if label=="Completed" else (orange if label=="Cancelled" else red)
    d.rounded_rectangle((startx,yy,startx+max(4,int(maxw*frac)),yy+33),radius=8,fill=color)
    d.text((startx+maxw+12,yy+1),f"{n:,}  ({frac:.1%})",font=small,fill=navy)

x,y=820,340; panel_title(x,y,"Payment reliability","Failed transactions by method")
maxv=max(v for _,v,_,_ in payments); startx=x+175; maxw=390
for j,(method,rate,n,failed) in enumerate(payments):
    yy=y+124+j*52
    d.text((x+28,yy+4),method,font=regular,fill=navy)
    d.rounded_rectangle((startx,yy,startx+maxw,yy+28),radius=7,fill="#EDF1F5")
    d.rounded_rectangle((startx,yy,startx+max(4,int(maxw*rate/maxv)),yy+28),radius=7,fill=orange if method==payments[0][0] else teal)
    d.text((startx+maxw+12,yy+1),f"{rate:.1f}%  ({failed}/{n})",font=small,fill=navy)
d.text((x+28,y+315),"Overall transaction failure rate: 4.0%",font=small,fill=muted)

x,y=70,745; panel_title(x,y,"Customer ratings","Ride-level rating distribution (1–5)")
maxn=max(n for _,n in ratings); startx=x+175; maxw=400
for j,(score,n) in enumerate(ratings):
    yy=y+116+j*48
    d.text((x+28,yy+1),score,font=small,fill=navy)
    d.rounded_rectangle((startx,yy,startx+maxw,yy+26),radius=7,fill="#EDF1F5")
    d.rounded_rectangle((startx,yy,startx+int(maxw*n/maxn),yy+26),radius=7,fill=red if score in ("1 to <2","2 to <3") else teal)
    d.text((startx+maxw+12,yy),f"{n:,}",font=small,fill=navy)
d.text((x+28,y+315),"Low ratings (<3): 48.7% of rides",font=small,fill=muted)

x,y=820,745; panel_title(x,y,"Customer ID quality","The user key is not unique in the supplied master")
vals=[("Rows in Users sheet",f"{user_rows:,}"),("Distinct UserIDs",f"{unique_users:,}"),("IDs appearing more than once",f"{repeated_ids:,}"),("Repeated IDs with conflicting names/cities",f"{conflicting:,}")]
for j,(label,value) in enumerate(vals):
    yy=y+120+j*48
    d.text((x+30,yy),label,font=regular,fill=navy)
    d.text((x+675,yy),value,font=bold,fill=red if j>=2 else teal,anchor="ra")
d.text((x+28,y+318),"Resolve identity mapping before customer-level conclusions.",font=small,fill=muted)

d.text((70,1135),"Source: supplied synthetic practice workbook · Dates: 2025-01-30 to 2025-07-31 · Analysis snapshot: 2026-11-22",font=small,fill=muted)
im.save(OUT, optimize=True)
print(OUT)
