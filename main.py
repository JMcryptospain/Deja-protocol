"""
Deja Protocol - API Server
El "mostrador" central donde los agentes reportan y consultan conocimiento.

Para arrancarlo: python3 main.py
Después puedes ver la documentación en: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from models import ObservationReport, KnowledgeQuery, KnowledgeResponse
from database import init_database, store_observation, query_knowledge, get_stats

# --- Crear la aplicación ---

app = FastAPI(
    title="Deja Protocol",
    description="Shared operational memory for on-chain agents. Your agent already lived this — through others.",
    version="0.1.0"
)


# --- Inicializar base de datos al arrancar ---

@app.on_event("startup")
def startup():
    init_database()
    print("""
    ╔══════════════════════════════════════════╗
    ║           DEJA PROTOCOL v0.1             ║
    ║   Shared Memory for On-Chain Agents      ║
    ║                                          ║
    ║   API docs: http://localhost:8000/docs   ║
    ╚══════════════════════════════════════════╝
    """)


# --- ENDPOINTS ---

@app.get("/")
def root():
    """Endpoint raíz - confirma que el servidor está vivo."""
    return {
        "protocol": "Deja",
        "version": "0.1.0",
        "tagline": "Your agent already lived this — through others.",
        "endpoints": {
            "report": "POST /report - Reportar una observación",
            "query": "POST /query - Consultar conocimiento antes de operar",
            "stats": "GET /stats - Estadísticas de la red",
            "docs": "GET /docs - Documentación interactiva"
        }
    }


@app.post("/report", response_model=dict)
def report_observation(report: ObservationReport):
    """
    Un agente reporta algo que le ha pasado.
    Esto se llama AUTOMÁTICAMENTE por el SDK después de cada operación.

    El agente no necesita hacer nada especial - el SDK captura
    el resultado de la operación y lo reporta aquí.
    """
    observation_id = store_observation(report)
    return {
        "status": "recorded",
        "observation_id": observation_id,
        "message": f"Observation recorded. The network thanks agent {report.agent_id}."
    }


@app.post("/query", response_model=KnowledgeResponse)
def query_before_executing(query: KnowledgeQuery):
    """
    Un agente consulta ANTES de ejecutar una operación.
    '¿Alguien ya intentó esto? ¿Qué debería saber?'

    Esto se llama AUTOMÁTICAMENTE por el SDK antes de cada operación.
    Si hay warnings, el agente puede decidir ajustar su estrategia.
    """
    response = query_knowledge(query)
    return response


@app.post("/confirm/{observation_id}")
def confirm_observation(observation_id: int):
    """
    Un agente confirma que una observación es correcta.
    'Yo también experimenté esto.'

    Esto incrementa la fiabilidad de la observación.
    """
    from database import get_connection
    conn = get_connection()

    # Verificar que existe
    row = conn.execute(
        "SELECT id FROM observations WHERE id = ?", (observation_id,)
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Observation not found")

    conn.execute(
        "UPDATE observations SET confirmations = confirmations + 1 WHERE id = ?",
        (observation_id,)
    )
    conn.commit()
    conn.close()

    return {"status": "confirmed", "observation_id": observation_id}


@app.get("/stats")
def network_stats():
    """
    Estadísticas generales de la red Deja.
    Cuántas observaciones, cuántos agentes, por chain, etc.
    """
    return get_stats()


# --- Arrancar servidor ---

if __name__ == "__main__":
    import uvicorn
    import os; port = int(os.environ.get("PORT", 8000)); uvicorn.run(app, host="0.0.0.0", port=port)
