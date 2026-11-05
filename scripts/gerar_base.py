"""
gerar_base.py
Gera a base FICTÍCIA de contratos usada pelo dashboard.

Saídas:
  data/contratos.csv  separador ";" e números em pt-BR (como viria de uma extração)
  data/contratos.js   mesma base em JSON, carregada pela página (funciona até abrindo o HTML direto do disco)

Uso:
  python scripts/gerar_base.py

Nenhum dado aqui corresponde a empresa, fornecedor ou contrato real.
"""

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

# PONTO CRÍTICO: semente fixa = base sempre igual a cada execução (demo reproduzível)
random.seed(42)

# Data de referência fixa. Em produção seria um parâmetro, nunca date.today(),
# senão os indicadores mudam sozinhos de um dia para o outro sem a base mudar
DATA_REFERENCIA = date(2026, 11, 4)

RAIZ = Path(__file__).resolve().parent.parent
PASTA_DADOS = RAIZ / "data"

CATEGORIAS = {
    "Manutenção industrial": ["Granito Manutenção", "Alfa Serviços Industriais", "Torno Fino Usinagem"],
    "Logística e frete": ["Boreal Logística", "Faro Transportes", "Rota Sul Cargas"],
    "Serviços de TI": ["Cervo Tecnologia", "Horizonte TI"],
    "Materiais de consumo": ["Delta Suprimentos", "Lince Distribuidora", "Pampa Embalagens"],
    "Facilities": ["Estrela Facilities", "Vale Verde Limpeza"],
}

QTD_CONTRATOS = 36


def somar_meses(d: date, meses: int) -> date:
    """Soma meses mantendo o dia (ajusta para o último dia válido do mês)."""
    ano = d.year + (d.month - 1 + meses) // 12
    mes = (d.month - 1 + meses) % 12 + 1
    for dia in (d.day, 30, 29, 28):
        try:
            return date(ano, mes, dia)
        except ValueError:
            continue
    raise ValueError("data inválida")


def gerar_contrato(seq: int) -> dict:
    categoria = random.choice(list(CATEGORIAS))
    fornecedor = random.choice(CATEGORIAS[categoria])

    inicio = date(2025, 1, 1) + timedelta(days=random.randint(0, 640))
    duracao_meses = random.choice([12, 12, 18, 24, 24, 36])
    fim = somar_meses(inicio, duracao_meses) - timedelta(days=1)

    # Valor contratado: distribuição assimétrica (muitos pequenos, poucos grandes)
    valor = round(random.lognormvariate(11.8, 0.8) / 1000) * 1000
    valor = max(15_000, min(valor, 1_800_000))

    # % do prazo já decorrido na data de referência
    prazo_total = (fim - inicio).days + 1
    decorrido = min(max((DATA_REFERENCIA - inicio).days, 0), prazo_total)
    pct_prazo = decorrido / prazo_total

    # Consumo segue o prazo com ruído; alguns contratos aceleram, outros ficam parados
    perfil = random.choices(["ritmo", "acelerado", "parado"], weights=[6, 2, 2])[0]
    if perfil == "acelerado":
        pct_consumo = pct_prazo + random.uniform(0.18, 0.40)
    elif perfil == "parado":
        pct_consumo = pct_prazo * random.uniform(0.15, 0.55)
    else:
        pct_consumo = pct_prazo + random.uniform(-0.08, 0.08)
    pct_consumo = min(max(pct_consumo, 0), 1.05)  # até 5% acima = aditivo pendente

    consumido = round(valor * pct_consumo, 2)

    return {
        "contrato": f"46{seq:08d}",
        "fornecedor": fornecedor,
        "categoria": categoria,
        "inicio": inicio.isoformat(),
        "fim": fim.isoformat(),
        "valor_contratado": float(valor),
        "valor_consumido": consumido,
    }


def main() -> None:
    contratos = [gerar_contrato(1001 + i) for i in range(QTD_CONTRATOS)]
    PASTA_DADOS.mkdir(exist_ok=True)

    # CSV no "jeito SAP": ; como separador, data dd.mm.aaaa e vírgula decimal
    with open(PASTA_DADOS / "contratos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Contrato", "Fornecedor", "Categoria", "Data_Inicio", "Data_Fim",
                    "Valor_Contratado", "Valor_Consumido"])
        for c in contratos:
            w.writerow([
                c["contrato"], c["fornecedor"], c["categoria"],
                date.fromisoformat(c["inicio"]).strftime("%d.%m.%Y"),
                date.fromisoformat(c["fim"]).strftime("%d.%m.%Y"),
                f'{c["valor_contratado"]:.2f}'.replace(".", ","),
                f'{c["valor_consumido"]:.2f}'.replace(".", ","),
            ])

    # JS com a base embutida: evita fetch(), que falha ao abrir o HTML direto do disco
    payload = {"data_referencia": DATA_REFERENCIA.isoformat(), "contratos": contratos}
    with open(PASTA_DADOS / "contratos.js", "w", encoding="utf-8") as f:
        f.write("// Base fictícia gerada por scripts/gerar_base.py. Não editar à mão.\n")
        f.write("window.BASE_CONTRATOS = ")
        json.dump(payload, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"{len(contratos)} contratos gerados em {PASTA_DADOS}")


if __name__ == "__main__":
    main()
