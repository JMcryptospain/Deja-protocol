"""
Deja Protocol - Database
Almacena y busca observaciones en SQLite.
SQLite = base de datos en un solo archivo, cero configuración.
"""

import sqlite3
import json
from typing import List, Optional
from models import ObservationReport, StoredObservation, KnowledgeQuery, KnowledgeResponse


DATABASE_FILE = "deja.db"


def get_connection():
    """Crea conexión a la base de datos."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn


def init_database():
    """
    Crea la tabla de observaciones si no existe.
    Se ejecuta al arrancar el servidor.
    """
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            chain TEXT NOT NULL,
            observation_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            contract_address TEXT,
            method_name TEXT,
            operation_description TEXT NOT NULL,
            expected_result TEXT,
            actual_result TEXT NOT NULL,
            error_message TEXT,
            gas_estimated INTEGER,
            gas_actual INTEGER,
            rpc_endpoint TEXT,
            block_number INTEGER,
            workaround TEXT,
            resolved INTEGER DEFAULT 0,
            confirmations INTEGER DEFAULT 0,
            relevance_score REAL DEFAULT 1.0
        )
    """)

    # Índices para búsquedas rápidas
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chain ON observations(chain)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_contract ON observations(contract_address)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON observations(observation_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON observations(timestamp)")

    conn.commit()
    conn.close()
    print("✅ Base de datos Deja inicializada")


def store_observation(report: ObservationReport) -> int:
    """
    Almacena una nueva observación de un agente.
    Devuelve el ID asignado.
    """
    conn = get_connection()
    from datetime import datetime
    timestamp = datetime.utcnow().isoformat()

    cursor = conn.execute("""
        INSERT INTO observations (
            timestamp, agent_id, chain, observation_type, severity,
            contract_address, method_name, operation_description,
            expected_result, actual_result, error_message,
            gas_estimated, gas_actual, rpc_endpoint, block_number,
            workaround, resolved
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp, report.agent_id, report.chain,
        report.observation_type, report.severity,
        report.contract_address, report.method_name,
        report.operation_description,
        report.expected_result, report.actual_result,
        report.error_message,
        report.gas_estimated, report.gas_actual,
        report.rpc_endpoint, report.block_number,
        report.workaround, int(report.resolved)
    ))

    observation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return observation_id


def query_knowledge(query: KnowledgeQuery) -> KnowledgeResponse:
    """
    Busca observaciones relevantes para lo que un agente quiere hacer.
    Esto es el corazón de Deja: '¿alguien ya pasó por aquí?'
    """
    conn = get_connection()

    # Construir búsqueda según lo que sabemos
    conditions = ["chain = ?"]
    params = [query.chain]

    if query.contract_address:
        conditions.append("contract_address = ?")
        params.append(query.contract_address)

    if query.method_name:
        conditions.append("method_name = ?")
        params.append(query.method_name)

    where_clause = " AND ".join(conditions)

    # Buscar observaciones relevantes, más recientes primero
    rows = conn.execute(f"""
        SELECT * FROM observations
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT 20
    """, params).fetchall()

    conn.close()

    # Construir respuesta
    warnings = []
    recommendations = []
    gas_values = []

    for row in rows:
        # Si fue un fallo o problema, es un warning
        if row["observation_type"] in ("transaction_failed", "simulation_mismatch", "rpc_issue", "infra_issue"):
            warnings.append({
                "type": row["observation_type"],
                "severity": row["severity"],
                "description": row["actual_result"],
                "error": row["error_message"],
                "when": row["timestamp"],
                "confirmations": row["confirmations"]
            })

        # Si tiene workaround, es una recomendación
        if row["workaround"]:
            recommendations.append(row["workaround"])

        # Recoger datos de gas real
        if row["gas_actual"]:
            gas_values.append(row["gas_actual"])

    # Calcular gas promedio si tenemos datos
    avg_gas = sum(gas_values) / len(gas_values) if gas_values else None

    return KnowledgeResponse(
        query=query,
        observations_found=len(rows),
        warnings=warnings,
        recommendations=list(set(recommendations)),  # Eliminar duplicados
        avg_gas_real=avg_gas
    )


def get_stats() -> dict:
    """Estadísticas generales de la base de conocimiento."""
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
    by_chain = conn.execute(
        "SELECT chain, COUNT(*) as count FROM observations GROUP BY chain"
    ).fetchall()
    by_type = conn.execute(
        "SELECT observation_type, COUNT(*) as count FROM observations GROUP BY observation_type"
    ).fetchall()
    unique_agents = conn.execute(
        "SELECT COUNT(DISTINCT agent_id) FROM observations"
    ).fetchone()[0]

    conn.close()

    return {
        "total_observations": total,
        "unique_agents": unique_agents,
        "by_chain": {row["chain"]: row["count"] for row in by_chain},
        "by_type": {row["observation_type"]: row["count"] for row in by_type}
    }
