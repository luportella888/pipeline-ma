import sqlite3

# Palavras que ELIMINAM a empresa
EXCLUIR_NOMES = [
    # Cartórios e serventias
    "TABELIAO", "TABELIONATO", "OFICIO DE NOTAS", "OFICIO DE REGISTRO",
    "OFICIO DO REGISTRO", "REGISTRO CIVIL", "REGISTRO DE IMOVEIS",
    "REGISTRO DE TITULOS", "PROTESTO DE LETRAS", "SERVENTIA",
    "2o OFICIO", "1o OFICIO", "3o OFICIO", "4o OFICIO",
    "1. OFICIO", "2. OFICIO", "1 OFICIO", "2 OFICIO", "CIDADANIA", "ORGANIZACOES POLITIC", "-SCP", "SCP"

    # Políticos e partidários
    "PARTIDO", "DIRETORIO", "PMDB", "PSDB", "PT -", "PDT",
    "PSD", "PSL", "PODEMOS", "SOLIDARIEDADE", "HUMANISTA",
    "PROGRESSISTA", "TRABALHISTA NACIONAL", "DEMOCRATICO BRASILEIRO",
    "LIBERAL -", "SOCIALISTA", "COMUNISTA", "COMISSAO PROVISORIA",
    "COMISSAO MUNICIPAL", "COMISSAO PROVIS", "ORGAO PROVIS",
    "DIRETORIO MUNICIPAL", "MOVIMENTO DEMOCRATICO", "REDE SUSTENTABILIDADE",

    # Militares
    "BATALHAO", "ARTILHARIA", "INFANTARIA", "BRIGADA MILITAR",
    "LOGISTICO MILITAR" "REGIMENTO DE CAVALARIA", "SHOOT COMERCIAL", "IMOBILIARIOS SPE",

    # Religiosos
    "IGREJA", "TEMPLO", "PAROQUIA", "DIOCESE",
    "COMUNIDADE BATISTA", "COMUNIDADE CRISTA",
    "RESTAURACAO EM CRISTO", "ASSEMBLEIA DE DEUS",

    # Esporte
    "ESPORTE CLUBE", "FUTEBOL CLUBE", "CLUBE ATLETICO",
    "CLUBE ESPORTIVO", "ASSOCIACAO ATLETICA",
    "DE MAIO ESPORTE", "DE MAIO FUTEBOL",
    "QUINZE DE NOVEMBRO",

    # Escoteiros
    "ESCOTEIRO", "GRUPO ESCOTEIRO",

    # Fundos e veículos financeiros
    "FUNDO DE INVESTIMENTO", "FUNDO IMOBILIARIO",
    "FUNDO MULTIMERCADO", "FIDC", " FII ",
    "FUNDO EM ACOES", "FUNDO FINANCEIRO",

    # Órgãos públicos
    "PREFEITURA", "CAMARA MUNICIPAL", "TRIBUNAL",
    "SECRETARIA MUNICIPAL", "CONSELHO COMUNITARIO",
    "CONSELHO TUTELAR", "SEGURANCA PUBLICA",
    "CIRCUNSCRICAO",

    # Associações e entidades
    "ASSOCIACAO", "FUNDACAO", "SINDICATO",
    "COOPERATIVA", "COOP ", "INSTITUTO ",
    "ESCOLA ESTADUAL", "ESCOLA MUNICIPAL",
    "POSTO DE SAUDE", "ADMINISTRADORA DE BENEFICIOS",

    # Imobiliárias SPE (veículos de propósito específico)
    "EMPREENDIMENTOS IMOBILIARIOS LTDA - ",
    "EMPREENDIMENTOS IMOBILIARIOS LTDA-",
    " SCP - ", " SCP-",
]

# Empresas que SÓ têm "PARTICIPACOES" no nome sem atividade real
# são holdings sem operação — menos relevantes para M&A
SUSPEITOS = [
    "PARTICIPACOES LTDA",
    "PARTICIPACOES S.A",
    "PARTICIPACOES SA",
    "EMPREENDIMENTOS E PARTICIPACOES",
    "ADMINISTRACAO E PARTICIPACOES",
    "INVESTIMENTOS E PARTICIPACOES",
]

def limpar_banco():
    conn = sqlite3.connect("pipeline.db")
    cursor = conn.cursor()

    total_antes = cursor.execute(
        "SELECT COUNT(*) FROM empresas"
    ).fetchone()[0]
    print(f"Empresas antes da limpeza: {total_antes}\n")

    # Remove por palavras ruins
    removidos = 0
    for palavra in EXCLUIR_NOMES:
        cursor.execute(
            "DELETE FROM empresas WHERE nome LIKE ?",
            (f"%{palavra}%",)
        )
        qtd = cursor.rowcount
        if qtd > 0:
            print(f"  -{qtd} '{palavra}'")
            removidos += qtd
    conn.commit()
    print(f"\nRemovidas por nome: {removidos}")

    # Remove holdings puras (só participações, sem atividade)
    removidos_holding = 0
    for palavra in SUSPEITOS:
        cursor.execute(
            "DELETE FROM empresas WHERE nome LIKE ? AND cnae_descricao LIKE '%holding%'",
            (f"%{palavra}%",)
        )
        qtd = cursor.rowcount
        if qtd > 0:
            print(f"  -{qtd} holding '{palavra}'")
            removidos_holding += qtd
    conn.commit()
    print(f"Holdings puras removidas: {removidos_holding}")

    # Remove duplicatas pelo nome
    cursor.execute("""
        DELETE FROM empresas
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM empresas
            GROUP BY nome
        )
    """)
    dup_nome = cursor.rowcount
    conn.commit()
    print(f"Duplicatas por nome: {dup_nome}")

    # Remove duplicatas pelo CNPJ
    cursor.execute("""
        DELETE FROM empresas
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM empresas
            GROUP BY cnpj
        )
    """)
    dup_cnpj = cursor.rowcount
    conn.commit()
    print(f"Duplicatas por CNPJ: {dup_cnpj}")

    total_depois = cursor.execute(
        "SELECT COUNT(*) FROM empresas"
    ).fetchone()[0]
    print(f"\nEmpresas após limpeza: {total_depois}")

    # Mostra 15 exemplos aleatórios para conferir
    print("\n--- 15 exemplos aleatórios do que sobrou ---")
    exemplos = cursor.execute("""
        SELECT nome, uf, cnae_descricao, data_abertura
        FROM empresas
        ORDER BY RANDOM()
        LIMIT 15
    """).fetchall()
    for e in exemplos:
        setor = (e[2] or "")[:35]
        print(f"  {e[0][:45]} | {e[1]} | {setor} | {(e[3] or '')[:4]}")

    conn.close()

limpar_banco()