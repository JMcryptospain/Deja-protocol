"""
Deja Protocol - DEMO
====================
Este script simula el "momento wow" del hackathon:

1. Agent A intenta una operación → FALLA → Deja captura el error
2. Agent A encuentra workaround → ÉXITO → Deja captura la solución
3. Agent B intenta LA MISMA operación → Deja le ADVIERTE antes → B lo hace bien a la primera

Ejecutar: python3 demo.py
"""

import time
from database import init_database
from sdk import DejaSDK
from models import ObservationType, Severity


# ════════════════════════════════════════════════════════════
#  SIMULACIONES DE OPERACIONES ON-CHAIN
#  (En producción serían llamadas reales a contratos)
# ════════════════════════════════════════════════════════════

SWAP_CONTRACT = "0x7d2F14c6A5C66e1CF30B0e71b7E3e04F3c1dA879"
RPC_MAIN = "https://rpc.mainnet.taiko.xyz"
RPC_BACKUP = "https://rpc.ankr.com/taiko"


def simulate_swap_with_bad_slippage(**kwargs):
    """Simula un swap que falla por slippage mal configurado."""
    raise Exception(
        "execution reverted: INSUFFICIENT_OUTPUT_AMOUNT - "
        "slippage tolerance 0.5% too low for current pool liquidity"
    )


def simulate_swap_with_fixed_slippage(**kwargs):
    """Simula un swap exitoso con slippage corregido."""
    return {
        "tx_hash": "0xabc123...def456",
        "amount_in": "100 USDC",
        "amount_out": "0.041 ETH",
        "gas_used": 185000,
        "slippage_used": "2.0%"
    }


def simulate_rpc_timeout(**kwargs):
    """Simula un timeout del RPC principal."""
    raise Exception(
        f"HTTPSConnectionPool: Read timed out (timeout=10s) - {RPC_MAIN}"
    )


def simulate_swap_success_backup_rpc(**kwargs):
    """Simula swap exitoso usando RPC de backup."""
    return {
        "tx_hash": "0x789abc...123def",
        "amount_in": "50 USDC",
        "amount_out": "0.020 ETH",
        "gas_used": 178000,
        "rpc_used": RPC_BACKUP
    }


# ════════════════════════════════════════════════════════════
#  DEMO
# ════════════════════════════════════════════════════════════

def main():
    # Inicializar base de datos limpia
    init_database()

    print("\n")
    print("═" * 60)
    print("  🔮 DEJA PROTOCOL - LIVE DEMO")
    print("  'Your agent already lived this — through others.'")
    print("═" * 60)

    # ──────────────────────────────────────────────────────
    # ACTO 1: Agent Alpha opera SIN conocimiento previo
    # ──────────────────────────────────────────────────────

    print("\n\n" + "─" * 60)
    print("  ACT 1: Agent Alpha - First Explorer")
    print("  No prior knowledge. Learning the hard way.")
    print("─" * 60)
    time.sleep(1)

    alpha = DejaSDK(agent_id="alpha-trading-bot", chain="taiko")

    # Alpha intenta swap → FALLA por slippage
    print("\n📍 Alpha attempts a USDC→ETH swap on Taiko DEX...\n")
    time.sleep(1)

    try:
        alpha.execute(
            operation_fn=simulate_swap_with_bad_slippage,
            operation_description="Swap 100 USDC to ETH on Taiko DEX",
            contract_address=SWAP_CONTRACT,
            method_name="swapExactTokensForTokens",
            gas_estimated=150000,
            rpc_endpoint=RPC_MAIN
        )
    except Exception:
        pass  # Alpha maneja el error

    time.sleep(1)

    # Alpha descubre el workaround y reporta
    print("\n📍 Alpha investigates, finds the fix, and tries again...\n")
    time.sleep(1)

    # Reportar el workaround encontrado
    alpha.report(
        observation_type=ObservationType.TRANSACTION_FAILED,
        operation_description="Swap USDC to ETH on Taiko DEX",
        actual_result="Failed with 0.5% slippage due to low pool liquidity",
        severity=Severity.HIGH,
        contract_address=SWAP_CONTRACT,
        method_name="swapExactTokensForTokens",
        error_message="INSUFFICIENT_OUTPUT_AMOUNT",
        gas_estimated=150000,
        workaround="Use minimum 2% slippage for USDC/ETH pair on Taiko. Pool liquidity is thin - 0.5% default will fail consistently.",
        resolved=True
    )

    # Alpha también descubre problema con RPC
    print("\n📍 Alpha also encounters an RPC issue...\n")
    time.sleep(1)

    try:
        alpha.execute(
            operation_fn=simulate_rpc_timeout,
            operation_description="Swap 50 USDC to ETH on Taiko DEX",
            contract_address=SWAP_CONTRACT,
            method_name="swapExactTokensForTokens",
            rpc_endpoint=RPC_MAIN
        )
    except Exception:
        pass

    time.sleep(1)

    # Alpha reporta el workaround del RPC
    alpha.report(
        observation_type=ObservationType.RPC_ISSUE,
        operation_description="Any transaction on Taiko mainnet",
        actual_result=f"RPC {RPC_MAIN} timing out frequently",
        severity=Severity.HIGH,
        rpc_endpoint=RPC_MAIN,
        error_message="Read timed out (timeout=10s)",
        workaround=f"Use backup RPC: {RPC_BACKUP} - more reliable, ~20ms slower but consistent",
        resolved=True
    )

    print("\n\n" + "─" * 60)
    print("  ⏳ Time passes... Agent Alpha's pain becomes collective wisdom.")
    print("─" * 60)
    time.sleep(2)

    # ──────────────────────────────────────────────────────
    # ACTO 2: Agent Beta llega NUEVO y consulta Deja
    # ──────────────────────────────────────────────────────

    print("\n\n" + "─" * 60)
    print("  ACT 2: Agent Beta - Standing on Shoulders")
    print("  Brand new agent. Same operation. Different outcome.")
    print("─" * 60)
    time.sleep(1)

    beta = DejaSDK(agent_id="beta-defi-agent", chain="taiko")

    # Beta quiere hacer el MISMO swap que Alpha
    print("\n📍 Beta wants to swap USDC→ETH on the same DEX...\n")
    print("   But first, Deja checks what others have experienced:\n")
    time.sleep(1)

    # Beta consulta Deja ANTES de ejecutar
    intel = beta.consult(
        operation_description="Swap USDC to ETH on Taiko DEX",
        contract_address=SWAP_CONTRACT,
        method_name="swapExactTokensForTokens"
    )

    time.sleep(1)

    if intel["has_warnings"]:
        print(f"\n   🛡️  Beta received {len(intel['warnings'])} warnings BEFORE executing!")
        print(f"   🛡️  Beta adjusts strategy based on Alpha's experience.")
        print(f"   🛡️  Setting slippage to 2% and using backup RPC.\n")
    time.sleep(1)

    # Beta ejecuta CON el conocimiento de Alpha → ÉXITO
    print("📍 Beta executes with adjusted parameters...\n")
    time.sleep(1)

    result = beta.execute(
        operation_fn=simulate_swap_with_fixed_slippage,
        operation_description="Swap 100 USDC to ETH on Taiko DEX (adjusted params)",
        contract_address=SWAP_CONTRACT,
        method_name="swapExactTokensForTokens",
        gas_estimated=150000,
        rpc_endpoint=RPC_BACKUP
    )

    # ──────────────────────────────────────────────────────
    # ACTO 3: Resultados
    # ──────────────────────────────────────────────────────

    print("\n\n" + "═" * 60)
    print("  📊 RESULTS")
    print("═" * 60)

    print(f"""
    Agent Alpha (without Deja knowledge):
    ├── Attempts needed:     3 (2 failures + 1 success)
    ├── Gas wasted on fails: ~300,000 gas
    ├── Time lost:           investigating errors, finding workarounds
    └── Result:              Eventually succeeded, but at a cost

    Agent Beta (with Deja knowledge):
    ├── Attempts needed:     1 (direct success)
    ├── Gas wasted on fails: 0
    ├── Time lost:           0 (consulted Deja in milliseconds)
    └── Result:              Succeeded first try with optimized params

    💰 Savings for Beta:     ~300,000 gas + time + frustration
    """)

    # Estadísticas de la red
    from database import get_stats
    stats = get_stats()

    print("─" * 60)
    print("  🔮 DEJA NETWORK STATUS")
    print("─" * 60)
    print(f"""
    Total observations:      {stats['total_observations']}
    Unique agents:           {stats['unique_agents']}
    Observations by chain:   {stats.get('by_chain', {})}
    Observations by type:    {stats.get('by_type', {})}
    """)

    print("═" * 60)
    print("  Every agent that connects makes the network smarter.")
    print("  Every error shared is an error others won't repeat.")
    print("  This is Deja Protocol.")
    print("═" * 60)
    print()


if __name__ == "__main__":
    main()
