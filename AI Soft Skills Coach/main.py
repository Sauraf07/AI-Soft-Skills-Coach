from fastapi import FastAPI
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Ai Soft Skill coach"}