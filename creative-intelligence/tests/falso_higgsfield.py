"""CLI FALSA da Higgsfield para testes: imita os comandos usados pelo adaptador, sem rede e sem créditos.
Modos (FALSO_HIGGSFIELD_MODO): ok, sem_login, falha. FALSO_HIGGSFIELD_CUSTO = custo devolvido por `generate cost`."""
import json
import os
import sys

args = sys.argv[1:]
modo = os.environ.get("FALSO_HIGGSFIELD_MODO", "ok")
log = os.environ.get("FALSO_HIGGSFIELD_LOG")
if log:
    with open(log, "a", encoding="utf-8") as f:
        f.write(" ".join(args) + "\n")

if args[:1] == ["version"]:
    print("higgsfield 1.1.2 (falso)")
    sys.exit(0)
if modo == "sem_login" and args[:1] != ["version"]:
    print("Error: Not authenticated. Run `higgsfield auth login`.", file=sys.stderr)
    sys.exit(1)
if args[:2] == ["account", "status"]:
    print(json.dumps({"plan": "creator", "credits": 42, "email": "pessoa@exemplo.com", "token": "SEGREDO-NAO-PODE-SAIR"}))
    sys.exit(0)
if args[:3] == ["generate", "cost", "brain_activity"]:
    custo = os.environ.get("FALSO_HIGGSFIELD_CUSTO")
    if custo:
        print(json.dumps({"cost": float(custo), "unit": "credits"}))
        sys.exit(0)
    print("Error: missing required flag --video", file=sys.stderr)
    sys.exit(2)
if args[:3] == ["generate", "create", "brain_activity"]:
    if modo == "falha":
        print("Error: HTTP 503 Service Unavailable", file=sys.stderr)
        sys.exit(3)
    print(json.dumps({"id": "job-123", "status": "completed",
                      "result": {"hook_score": 71, "attention_score": 64, "peak_attention_s": 2.3,
                                 "report_url": "https://higgsfield.ai/report/job-123", "credits_used": 2,
                                 "access_token": "SEGREDO-NAO-PODE-SAIR"}}))
    sys.exit(0)
print(f"comando não simulado: {args}", file=sys.stderr)
sys.exit(9)
