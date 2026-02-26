from fastapi import FastAPI

app = FastAPI(
    title="Gemelo Cognitivo API",
    description="API para el MVP de la aplicación pedagógica (Gemelo Digital)",
    version="0.1.0"
)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Gemelo Cognitivo"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
