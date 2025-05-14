lsof -ti:8000 | xargs kill -9
uvicorn api.server:app --reload --port 8000
