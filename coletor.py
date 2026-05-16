import requests
import sqlite3
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BRASIL_IO_TOKEN")

TODOS_ESTADOS = ["SP", "RJ", "MG"]

def criar_banco():
    conn = sqlite3.connect("cnpjs_raw.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cnpjs (
            cnpj TEXT PRIMARY KEY,
            nome TEXT,
            uf TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("Banco criado.")

def buscar_cnpjs(uf, pagina=1):
    url = "https://brasil.io/api/dataset/socios-brasil/empresas/data/"
    headers = {"Authorization": f"Token {TOKEN}"}
    params = {
        "uf": uf,
        "situacao_cadastral": "ATIVA",
        "page_size": 100,
        "page": pagina
    }
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 429:
            print(f"  Limite atingido — aguardando 30s...")
            time.sleep(30)
            r = requests.get(url, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            return r.json().get("results", [])
    except Exception as e:
        print(f"  Erro: {e}")
    return []

def salvar_cnpjs(empresas):
    conn = sqlite3.connect("cnpjs_raw.db")
    cursor = conn.cursor()
    salvos = 0
    for e in empresas:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO cnpjs (cnpj, nome, uf) VALUES (?, ?, ?)",
                (e.get("cnpj",""), e.get("razao_social",""), e.get("uf",""))
            )
            if cursor.rowcount > 0:
                salvos += 1
        except:
            pass
    conn.commit()
    conn.close()
    return salvos

def rodar_coleta():
    criar_banco()
    total = 0
    for uf in TODOS_ESTADOS:
        print(f"\n=== {uf} ===")
        salvos_uf = 0
        for pagina in range(1, 26):  # 25 páginas = 2500 CNPJs por estado
            resultados = buscar_cnpjs(uf, pagina)
            if not resultados:
                break
            salvos = salvar_cnpjs(resultados)
            salvos_uf += salvos
            total += salvos
            print(f"  Página {pagina}: {salvos} CNPJs salvos")
            time.sleep(0.5)
        print(f"  Total {uf}: {salvos_uf}")
    print(f"\nColeta finalizada! {total} CNPJs no banco cnpjs_raw.db")

rodar_coleta()