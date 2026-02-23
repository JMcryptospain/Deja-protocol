"""
Deja Protocol - SDK
Esto es lo que un desarrollador de agentes integra.
Hace TODO automático: reportar y consultar sin que el desarrollador haga nada extra.

USO BÁSICO (3 líneas):
    from sdk import DejaSDK
    deja = DejaSDK(agent_id="mi-agente-001", chain="taiko")
    resultado = deja.execute(mi_funcion_original, args, kwargs)

Eso es todo. El SDK automáticamente:
1. Consulta Deja ANTES de ejecutar → "¿alguien ya intentó esto?"
2. Ejecuta la operación original
3. Reporta el resultado DESPUÉS → para que otros aprendan
"""

import time
import traceback
from typing import Callable, Any, Optional
from datetime import datetime

# En producción esto usaría requests/httpx para llamar a la API
# Para la demo, importamos directamente
from models import ObservationReport, KnowledgeQuery, ObservationType, Severity
from database import store_observation, query_knowledge


class DejaSDK:
    """
    SDK de Deja Protocol.
    Wrappea las operaciones de un agente para capturar conocimiento automáticamente.
    """

    def __init__(
        self,
        agent_id: str,
        chain: str = "taiko",
        deja_server: str = "http://localhost:8000",
        verbose: bool = True
    ):
        self.agent_id = agent_id
        self.chain = chain
        self.deja_server = deja_server
        self.verbose = verbose
        self._operations_count = 0
        self._errors_avoided = 0

        if self.verbose:
            print(f"🔮 Deja SDK initialized for agent '{agent_id}' on {chain}")
            print(f"   Connected to: {deja_server}")

    def _log(self, message: str):
        """Log interno del SDK."""
        if self.verbose:
            print(f"   [Deja] {message}")

    def consult(
        self,
        operation_description: str,
        contract_address: Optional[str] = None,
        method_name: Optional[str] = None
    ) -> dict:
        """
        Consulta la red Deja ANTES de ejecutar una operación.
        Devuelve warnings y recomendaciones basadas en experiencia de otros agentes.
        """
        query = KnowledgeQuery(
            chain=self.chain,
            contract_address=contract_address,
            method_name=method_name,
            operation_description=operation_description
        )

        response = query_knowledge(query)

        if response.warnings:
            self._log(f"⚠️  {len(response.warnings)} warning(s) from other agents!")
            for w in response.warnings:
                self._log(f"   → [{w['severity']}] {w['description']}")
        else:
            self._log(f"✅ No known issues for this operation")

        if response.recommendations:
            self._log(f"💡 Recommendations:")
            for r in response.recommendations:
                self._log(f"   → {r}")

        if response.avg_gas_real:
            self._log(f"⛽ Average real gas for this operation: {response.avg_gas_real:.0f}")

        return {
            "has_warnings": len(response.warnings) > 0,
            "warnings": response.warnings,
            "recommendations": response.recommendations,
            "avg_gas": response.avg_gas_real,
            "observations_found": response.observations_found
        }

    def report(
        self,
        observation_type: ObservationType,
        operation_description: str,
        actual_result: str,
        severity: Severity = Severity.MEDIUM,
        contract_address: Optional[str] = None,
        method_name: Optional[str] = None,
        expected_result: Optional[str] = None,
        error_message: Optional[str] = None,
        gas_estimated: Optional[int] = None,
        gas_actual: Optional[int] = None,
        rpc_endpoint: Optional[str] = None,
        workaround: Optional[str] = None,
        resolved: bool = False
    ) -> int:
        """
        Reporta una observación a la red Deja.
        Normalmente el SDK llama esto automáticamente, pero se puede llamar manualmente.
        """
        report = ObservationReport(
            agent_id=self.agent_id,
            chain=self.chain,
            observation_type=observation_type,
            severity=severity,
            contract_address=contract_address,
            method_name=method_name,
            operation_description=operation_description,
            expected_result=expected_result,
            actual_result=actual_result,
            error_message=error_message,
            gas_estimated=gas_estimated,
            gas_actual=gas_actual,
            rpc_endpoint=rpc_endpoint,
            workaround=workaround,
            resolved=resolved
        )

        observation_id = store_observation(report)
        self._log(f"📝 Observation #{observation_id} recorded → {observation_type.value}")
        return observation_id

    def execute(
        self,
        operation_fn: Callable,
        operation_description: str,
        contract_address: Optional[str] = None,
        method_name: Optional[str] = None,
        gas_estimated: Optional[int] = None,
        rpc_endpoint: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        MÉTODO PRINCIPAL - Wrappea la ejecución de una operación.

        1. Consulta Deja antes de ejecutar
        2. Ejecuta la operación original
        3. Reporta el resultado (éxito o fallo)

        Uso:
            result = deja.execute(
                operation_fn=mi_funcion_swap,
                operation_description="Swap 100 USDC to ETH on DEX",
                contract_address="0x1234...",
                method_name="swap"
            )
        """
        self._operations_count += 1
        self._log(f"━━━ Operation #{self._operations_count}: {operation_description} ━━━")

        # PASO 1: Consultar Deja antes de ejecutar
        self._log("🔍 Consulting Deja network...")
        intel = self.consult(
            operation_description=operation_description,
            contract_address=contract_address,
            method_name=method_name
        )

        # PASO 2: Ejecutar la operación original
        self._log("🚀 Executing operation...")
        start_time = time.time()

        try:
            result = operation_fn(**kwargs)
            elapsed = time.time() - start_time

            # PASO 3a: Reportar éxito
            self._log(f"✅ Operation succeeded in {elapsed:.2f}s")
            self.report(
                observation_type=ObservationType.TRANSACTION_SUCCESS,
                operation_description=operation_description,
                actual_result=f"Success: {str(result)[:200]}",
                severity=Severity.LOW,
                contract_address=contract_address,
                method_name=method_name,
                gas_estimated=gas_estimated,
                rpc_endpoint=rpc_endpoint,
                resolved=True
            )

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            error_trace = traceback.format_exc()

            # PASO 3b: Reportar fallo
            self._log(f"❌ Operation FAILED after {elapsed:.2f}s: {error_msg}")
            self.report(
                observation_type=ObservationType.TRANSACTION_FAILED,
                operation_description=operation_description,
                actual_result=f"Failed: {error_msg}",
                expected_result="Successful execution",
                error_message=error_msg,
                severity=Severity.HIGH,
                contract_address=contract_address,
                method_name=method_name,
                gas_estimated=gas_estimated,
                rpc_endpoint=rpc_endpoint,
                resolved=False
            )

            # Re-lanzar la excepción para que el agente la maneje
            raise

    def get_my_stats(self) -> dict:
        """Estadísticas de este agente en la red Deja."""
        return {
            "agent_id": self.agent_id,
            "chain": self.chain,
            "operations_executed": self._operations_count,
            "errors_avoided": self._errors_avoided
        }
