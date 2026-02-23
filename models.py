"""
Deja Protocol - Data Models
Define la estructura de las observaciones que los agentes reportan y consultan.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ObservationType(str, Enum):
    """Tipos de observación que un agente puede reportar."""
    TRANSACTION_FAILED = "transaction_failed"       # Transacción falló
    TRANSACTION_SUCCESS = "transaction_success"     # Transacción exitosa (para validar)
    GAS_DEVIATION = "gas_deviation"                 # Gas real ≠ gas estimado
    RPC_ISSUE = "rpc_issue"                         # Problema con un RPC endpoint
    CONTRACT_BEHAVIOR = "contract_behavior"         # Comportamiento inesperado de contrato
    RETRY_PATTERN = "retry_pattern"                 # Agente tuvo que reintentar operación
    SIMULATION_MISMATCH = "simulation_mismatch"     # Simulación ≠ ejecución real
    INFRA_ISSUE = "infra_issue"                     # Problema con indexer, oracle, etc.


class Severity(str, Enum):
    """Severidad del problema encontrado."""
    LOW = "low"           # Inconveniente menor
    MEDIUM = "medium"     # Afecta rendimiento/coste
    HIGH = "high"         # Operación falla
    CRITICAL = "critical" # Pérdida de fondos posible


# --- Lo que un agente ENVÍA al reportar una observación ---

class ObservationReport(BaseModel):
    """
    Lo que un agente envía cuando reporta algo que le ha pasado.
    El SDK genera esto automáticamente - el desarrollador no toca esto.
    """
    agent_id: str = Field(..., description="ID único del agente que reporta")
    chain: str = Field(..., description="Chain donde ocurrió (ej: 'taiko', 'ethereum')")
    observation_type: ObservationType
    severity: Severity = Severity.MEDIUM

    # Contexto de la operación
    contract_address: Optional[str] = Field(None, description="Contrato involucrado")
    method_name: Optional[str] = Field(None, description="Método/función llamada")
    operation_description: str = Field(..., description="Qué intentaba hacer el agente")

    # Qué pasó
    expected_result: Optional[str] = Field(None, description="Qué esperaba que pasara")
    actual_result: str = Field(..., description="Qué pasó realmente")
    error_message: Optional[str] = Field(None, description="Mensaje de error si hubo")

    # Datos técnicos
    gas_estimated: Optional[int] = Field(None, description="Gas estimado antes de ejecutar")
    gas_actual: Optional[int] = Field(None, description="Gas real consumido")
    rpc_endpoint: Optional[str] = Field(None, description="RPC usado")
    block_number: Optional[int] = Field(None, description="Bloque donde ocurrió")

    # Solución (si la encontró)
    workaround: Optional[str] = Field(None, description="Solución que el agente encontró")
    resolved: bool = Field(False, description="Si el agente logró resolver el problema")


# --- Lo que se almacena en la base de datos ---

class StoredObservation(ObservationReport):
    """Observación almacenada con metadatos del sistema."""
    id: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confirmations: int = Field(0, description="Cuántos agentes han confirmado esto")
    relevance_score: float = Field(1.0, description="Puntuación de relevancia")


# --- Lo que un agente PIDE cuando consulta ---

class KnowledgeQuery(BaseModel):
    """
    Consulta que un agente hace antes de ejecutar una operación.
    '¿Alguien ya intentó esto? ¿Qué debería saber?'
    """
    chain: str = Field(..., description="Chain donde va a operar")
    contract_address: Optional[str] = Field(None, description="Contrato con el que va a interactuar")
    method_name: Optional[str] = Field(None, description="Método que va a llamar")
    operation_description: str = Field(..., description="Qué quiere hacer")


# --- Lo que Deja responde a una consulta ---

class KnowledgeResponse(BaseModel):
    """Lo que Deja devuelve cuando un agente consulta."""
    query: KnowledgeQuery
    observations_found: int
    warnings: List[dict] = Field(default_factory=list, description="Problemas conocidos relevantes")
    recommendations: List[str] = Field(default_factory=list, description="Recomendaciones basadas en experiencia colectiva")
    avg_gas_real: Optional[float] = Field(None, description="Gas promedio real para esta operación")
