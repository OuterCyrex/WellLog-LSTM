from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from backend.predictor import predictor

app = FastAPI(title="WellLog Prediction Service")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "model_ready": predictor.ready,
    }


@app.post("/api/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File is required.")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = predictor.predict_bytes(content)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result["model_name"] = "WellLog-LSTM"
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.predict_service:app", host="127.0.0.1", port=8000, reload=False)
