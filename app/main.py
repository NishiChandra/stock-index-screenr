from fastapi import FastAPI, HTTPException
from app.database import get_db_connection
from app.models import BuildIndexRequest , ExportDataRequest
from app.build_index import build_index_logic, get_index_performance, get_index_composition, get_composition_changes
from fastapi.responses import StreamingResponse
from io import BytesIO
import pandas as pd

app = FastAPI()
conn = get_db_connection()

@app.get("/")
def root():
    return {"message": "App is working!"}

@app.post("/build-index")
def build_index(req: BuildIndexRequest):
    try:
        end_date = req.end_date or req.start_date
        results = build_index_logic(conn, req.start_date, end_date)
        return {"status": "success", "records": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/indexperformance")
def index_performance(start_date: str, end_date: str):
    return get_index_performance(conn, start_date, end_date)

@app.get("/index-composition")
def index_composition(date: str):
    return get_index_composition(conn, date)

@app.get("/compositionchanges")
def composition_changes(start_date: str, end_date: str):
    return get_composition_changes(conn, start_date, end_date)

@app.post("/export-data")
def export_data(req: ExportDataRequest):
    try:
        end_date = req.end_date or req.start_date

        # Fetch all required data
        index_perf = get_index_performance(conn, req.start_date, end_date)
        composition_changes = get_composition_changes(conn, req.start_date, end_date)
        all_compositions = []

        # Fetch compositions for each business day
        for d in pd.date_range(req.start_date, end_date, freq="B"):
            day_composition = get_index_composition(conn, str(d.date()))
            for entry in day_composition:
                entry["date"] = str(d.date())
                all_compositions.append(entry)

        # Create Excel in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.DataFrame(index_perf).to_excel(writer, index=False, sheet_name="Index Performance")
            pd.DataFrame(all_compositions).to_excel(writer, index=False, sheet_name="Daily Compositions")
            pd.DataFrame(composition_changes).to_excel(writer, index=False, sheet_name="Composition Changes")

        output.seek(0)
        filename = f"export_{req.start_date}_to_{end_date}.xlsx"

        return StreamingResponse(output,
                                 media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                 headers={"Content-Disposition": f"attachment; filename={filename}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
