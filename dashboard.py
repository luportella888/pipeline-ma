import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="Pipeline M&A",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main { background-color: #0f1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3d);
        border: 1px solid #2d3250;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 700;
        color: #4f8ef7;
        margin: 0;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #8892b0;
        margin: 4px 0 0 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .score-badge-alto {
        background: #1a3a2a;
        color: #4caf87;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .score-badge-medio {
        background: #3a2e1a;
        color: #f0a500;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .score-badge-baixo {
        background: #2a1a1a;
        color: #e05252;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .header-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0;
    }
    .header-sub {
        color: #8892b0;
        font-size: 0.9rem;
        margin-top: 4px;
    }
    div[data-testid="stSidebar"] {
        background: #1e2130;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def carregar_dados():
    conn = sqlite3.connect("pipeline.db")
    df = pd.read_sql_query("""
        SELECT
            nome        AS Empresa,
            uf          AS UF,
            municipio   AS Cidade,
            cnae_descricao AS Setor,
            capital_social AS Capital,
            data_abertura  AS Fundacao,
            natureza_juridica AS Tipo,
            score       AS Score
        FROM empresas
        WHERE score > 0
        ORDER BY score DESC
    """, conn)
    conn.close()

    # Formata capital
    df["Capital Formatado"] = df["Capital"].apply(
        lambda x: f"R${x:,.0f}" if x and x > 0 else "n/d"
    )

    # Calcula idade
    from datetime import datetime
    ano_atual = datetime.now().year
    df["Idade"] = df["Fundacao"].apply(
        lambda x: f"{ano_atual - int(x[:4])} anos" if x and len(x) >= 4 else "n/d"
    )

    # Categoria do score
    def categoria(s):
        if s >= 70: return "🟢 Alto"
        if s >= 50: return "🟡 Médio"
        return "🔴 Baixo"
    df["Prioridade"] = df["Score"].apply(categoria)

    return df

# ── SIDEBAR ──────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 Filtros")
    st.markdown("---")

    ufs = ["Todos"] + sorted(carregar_dados()["UF"].dropna().unique().tolist())
    uf_sel = st.selectbox("📍 Estado", ufs)

    setores_disponiveis = ["Todos"] + sorted(
        carregar_dados()["Setor"].dropna().unique().tolist()
    )
    setor_sel = st.selectbox("🏭 Setor", setores_disponiveis)

    score_min = st.slider("⭐ Score mínimo", 0, 100, 40)

    prioridade_sel = st.multiselect(
        "🎯 Prioridade",
        ["🟢 Alto", "🟡 Médio", "🔴 Baixo"],
        default=["🟢 Alto", "🟡 Médio"]
    )

    st.markdown("---")
    st.markdown("**Sobre o pipeline**")
    st.caption("Dados coletados via brasil.io e BrasilAPI. Atualização mensal.")

# ── HEADER ───────────────────────────────────────────
st.markdown('<p class="header-title">📊 Pipeline de Prospecção M&A</p>', unsafe_allow_html=True)
st.markdown('<p class="header-sub">Middle market brasileiro · SP, RJ e MG · Atualizado automaticamente</p>', unsafe_allow_html=True)
st.markdown("---")

# ── DADOS FILTRADOS ───────────────────────────────────
df = carregar_dados()
df_f = df[df["Score"] >= score_min]
if uf_sel != "Todos":
    df_f = df_f[df_f["UF"] == uf_sel]
if setor_sel != "Todos":
    df_f = df_f[df_f["Setor"] == setor_sel]
if prioridade_sel:
    df_f = df_f[df_f["Prioridade"].isin(prioridade_sel)]

# ── MÉTRICAS ─────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric("Total de targets", len(df_f))
with c2:
    alto = len(df_f[df_f["Prioridade"] == "🟢 Alto"])
    st.metric("🟢 Score alto (≥70)", alto)
with c3:
    medio = len(df_f[df_f["Prioridade"] == "🟡 Médio"])
    st.metric("🟡 Score médio (50-69)", medio)
with c4:
    capital_valido = df_f[df_f["Capital"] > 0]["Capital"]
    media = f"R${capital_valido.mean():,.0f}" if len(capital_valido) > 0 else "n/d"
    st.metric("Capital médio", media)
with c5:
    score_medio = f"{df_f['Score'].mean():.0f}" if len(df_f) > 0 else "0"
    st.metric("Score médio", score_medio)

st.markdown("---")

# ── TABELA PRINCIPAL ──────────────────────────────────
st.markdown(f"### 🏆 Targets qualificados — {len(df_f)} empresas")

tabela = df_f[[
    "Empresa", "UF", "Setor", "Capital Formatado",
    "Idade", "Prioridade", "Score"
]].rename(columns={"Capital Formatado": "Capital"})

st.dataframe(
    tabela,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score",
            min_value=0,
            max_value=100,
            format="%d"
        ),
        "Empresa": st.column_config.TextColumn("Empresa", width="large"),
        "Setor": st.column_config.TextColumn("Setor", width="large"),
    }
)

st.markdown("---")

# ── GRÁFICOS ─────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📈 Distribuição de scores")
    score_dist = df_f["Score"].value_counts().sort_index().reset_index()
    score_dist.columns = ["Score", "Quantidade"]
    st.bar_chart(score_dist.set_index("Score"))

with col2:
    st.markdown("### 🗺️ Targets por estado")
    uf_dist = df_f["UF"].value_counts().reset_index()
    uf_dist.columns = ["Estado", "Quantidade"]
    st.bar_chart(uf_dist.set_index("Estado"))

st.markdown("---")

# ── TOP 10 ────────────────────────────────────────────
st.markdown("### 🥇 Top 10 targets")
top10 = df_f.head(10)[["Empresa", "UF", "Setor", "Capital Formatado", "Idade", "Score"]]
top10 = top10.rename(columns={"Capital Formatado": "Capital"})

for i, row in top10.iterrows():
    with st.expander(f"#{list(top10.index).index(i)+1} — {row['Empresa']} | Score: {row['Score']}"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Estado", row["UF"])
        c2.metric("Capital", row["Capital"])
        c3.metric("Idade", row["Idade"])
        c4.metric("Score", row["Score"])
        st.caption(f"Setor: {row['Setor']}")