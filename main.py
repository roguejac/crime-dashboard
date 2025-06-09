from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from collections import defaultdict
import uuid

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Report(BaseModel):
    area: str
    crime_type: str
    date: str
    time: str
    description: str

# In-memory DB (for example)
CRIME_DATA = []
USER_ACTIVITY = []

@app.get("/get-stats")
def get_stats(area: str = "All"):
    data = [x for x in CRIME_DATA if x['area'] == area] if area != "All" else CRIME_DATA
    total = len(data)
    time_of_day = defaultdict(int)
    weekday = defaultdict(int)
    weekend_time = defaultdict(int)

    for d in data:
        hour = int(d['time'].split(':')[0])
        dt = datetime.strptime(d['date'], "%Y-%m-%d")
        wday = dt.strftime('%A')
        weekday[wday] += 1

        if 5 <= hour < 12:
            time_of_day['Morning'] += 1
            if wday in ['Saturday', 'Sunday']: weekend_time['Morning'] += 1
        elif 12 <= hour < 18:
            time_of_day['Day'] += 1
            if wday in ['Saturday', 'Sunday']: weekend_time['Day'] += 1
        else:
            time_of_day['Night'] += 1
            if wday in ['Saturday', 'Sunday']: weekend_time['Night'] += 1

    return {
        "totalCrimes": total,
        "avgCrimesPerDay": round(total / 30, 2),
        "timeOfDay": time_of_day,
        "dailyTrend": weekday,
        "weekendTime": weekend_time
    }

@app.post("/submit-report")
def submit_report(report: Report, request: Request):
    entry = report.dict()
    entry['id'] = str(uuid.uuid4())
    CRIME_DATA.append(entry)
    
    user_ip = request.client.host
    USER_ACTIVITY.append({
        "user": user_ip,
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
        "area": report.area
    })

    # Dummy prediction
    risk = "High" if report.crime_type.lower() in ["murder", "robbery"] else "Medium"
    return {"message": "Report submitted", "risk_prediction": risk}

@app.get("/admin-stats")
def admin_stats():
    users = set()
    area_count = defaultdict(int)
    date_count = defaultdict(int)

    for log in USER_ACTIVITY:
        users.add(log['user'])
        area_count[log['area']] += 1
        date_count[log['timestamp']] += 1

    return {
        "totalUsers": len(users),
        "totalReports": len(CRIME_DATA),
        "reportsByArea": [{"area": k, "count": v} for k, v in area_count.items()],
        "submissionsOverTime": [{"date": k, "count": v} for k, v in sorted(date_count.items())]
    }
