import sqlite3
from datetime import datetime

ANO_ATUAL = datetime.now().year

SETORES_SAUDE = [
    "odontol", "médic", "medic", "clínica", "clinica",
    "hospital", "farmac", "laborator", "saúde", "saude",
    "enfermagem", "fisioterapia", "psicolog"
]

SETORES_TECH = [
    "software", "tecnologia", "informática", "informatica",
    "sistemas", "telecom", "dados", "digital", "ti "
]

SETORES_INDUSTRIA = [
    "fabricaç", "fabricac", "indústria", "industria",
    "manufatur", "produç", "produc", "metalúrg", "metalurg",
    "químic", "quimic", "plástic", "plastic"
]

SETORES_LOGISTICA = [
    "transporte", "logística", "logistica", "frete",
    "armazén", "armazen", "distribuiç", "distribuic",
    "carga", "frota"
]

SETORES_EDUCACAO = [
    "educaç", "educac", "ensino", "escola", "colégio",
    "colegio", "universidade", "faculdade", "treinamento",
    "capacitaç", "capacitac"
]

SETORES_ALIMENTOS = [
    "aliment", "bebida", "restaurante", "food",
    "agrícol", "agricol", "agropecuár", "agropecuar",
    "café", "cafe", "laticín", "laticin"
]

SETORES_PENALIDADE = [
    "organização política", "organizacao politica",
    "organiz", "cartório", "cartorio", "serventia",
    "assistência social", "assistencia social",
    "aluguel de imóveis próprios", "aluguel de imoveis proprios",
    "loteamento", "incorporação de empreendimentos",
    "incorporacao de empreendimentos",
    "holding de institui"
]

def calcular_score(empresa):
    setor = (empresa.get("cnae_descricao") or "").lower()

    # Penalidade — setor irrelevante para M&A
    for palavra in SETORES_PENALIDADE:
        if palavra in setor:
            return 0

    score = 0

    # Antiguidade
    data = empresa.get("data_abertura") or ""
    if data and len(data) >= 4:
        try:
            idade = ANO_ATUAL - int(data[:4])
            if idade >= 25:   score += 35
            elif idade >= 15: score += 25
            elif idade >= 10: score += 15
        except:
            pass

    # Capital social
    capital = empresa.get("capital_social") or 0
    if capital >= 10_000_000:  score += 30
    elif capital >= 2_000_000: score += 20
    elif capital >= 500_000:   score += 10

    # Setor
    if any(p in setor for p in SETORES_SAUDE):        score += 20
    elif any(p in setor for p in SETORES_TECH):       score += 20
    elif any(p in setor for p in SETORES_INDUSTRIA):  score += 15
    elif any(p in setor for p in SETORES_LOGISTICA):  score += 15
    elif any(p in setor for p in SETORES_EDUCACAO):   score += 15
    elif any(p in setor for p in SETORES_ALIMENTOS):  score += 10

    return min(score, 100)

def rodar_scoring():
    conn = sqlite3.connect("pipeline.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    empresas = cursor.execute("SELECT * FROM empresas").fetchall()
    print(f"Calculando score para {len(empresas)} empresas...")

    for e in empresas:
        score = calcular_score(dict(e))
        cursor.execute(
            "UPDATE empresas SET score = ? WHERE cnpj = ?",
            (score, e["cnpj"])
        )

    conn.commit()

    # Top 15
    top = cursor.execute("""
        SELECT nome, uf, cnae_descricao, capital_social, data_abertura, score
        FROM empresas
        WHERE score > 0
        ORDER BY score DESC
        LIMIT 15
    """).fetchall()

    print(f"\n--- TOP 15 TARGETS ---")
    for i, e in enumerate(top, 1):
        capital = f"R${e['capital_social']:,.0f}" if e['capital_social'] else "n/d"
        idade = ANO_ATUAL - int((e['data_abertura'] or "2020")[:4])
        print(f"{i}. {e['nome'][:45]}")
        print(f"   {e['uf']} | {(e['cnae_descricao'] or '')[:40]} | {capital} | {idade} anos | Score: {e['score']}")
        print()

    conn.close()

rodar_scoring()