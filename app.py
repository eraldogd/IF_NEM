import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json
import random
from datetime import datetime
import io

# ─── CONFIGURAÇÃO DA PÁGINA ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Gestão de Percursos 2026",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CSS CUSTOMIZADO ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Header */
.main-header {
    background: linear-gradient(135deg, #1a73e8 0%, #0d47a1 100%);
    color: white;
    padding: 16px 24px;
    border-radius: 12px;
    margin-bottom: 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

/* Cards de cursos */
.curso-card {
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    border: 2px solid #a5d6a7;
    border-radius: 10px;
    padding: 10px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    min-height: 80px;
}
.curso-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.curso-card.lotado {
    background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 100%);
    border-color: #f48fb1;
}
.curso-card.selected {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    border: 3px solid #1a73e8;
    box-shadow: 0 4px 12px rgba(26,115,232,0.3);
}
.card-vagas {
    font-size: 20px;
    font-weight: 700;
    color: #2e7d32;
}
.card-vagas.lotado { color: #c62828; }

/* Badges de status */
.badge-ok {
    background: #e8f5e9;
    color: #2e7d32;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.badge-transf {
    background: #fce4ec;
    color: #c62828;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}
.badge-pending {
    background: #fff3e0;
    color: #e65100;
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

/* Métricas customizadas */
.metric-box {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.metric-value {
    font-size: 28px;
    font-weight: 700;
    color: #1a73e8;
}
.metric-label {
    font-size: 12px;
    color: #666;
    margin-top: 2px;
}

/* Trilha buttons */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}

/* Tabela de alunos */
.aluno-row-ok { background-color: #e8f5e9 !important; }
.aluno-row-transf { background-color: #fce4ec !important; text-decoration: line-through; color: #999; }

/* Sidebar limpa */
section[data-testid="stSidebar"] {
    background: #f8f9fa;
}

/* Ocultar menu padrão do Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTES ───────────────────────────────────────────────────────────────
VAGAS_MAX = 35
SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ─── CONEXÃO GOOGLE SHEETS ────────────────────────────────────────────────────
@st.cache_resource(ttl=0)
def get_gspread_client():
    """Retorna cliente autenticado do gspread usando secrets do Streamlit."""
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"❌ Erro na autenticação: {e}")
        st.info("Configure as credenciais em `.streamlit/secrets.toml`")
        return None


def get_spreadsheet():
    client = get_gspread_client()
    if not client:
        return None
    try:
        sheet_id = st.secrets["sheet_id"]
        return client.open_by_key(sheet_id)
    except Exception as e:
        st.error(f"❌ Erro ao abrir planilha: {e}")
        return None


# ─── LEITURA DE DADOS ─────────────────────────────────────────────────────────
@st.cache_data(ttl=15)
def carregar_alunos():
    ss = get_spreadsheet()
    if not ss:
        return pd.DataFrame()
    try:
        ws = ss.worksheet("Planilha1")
        dados = ws.get_all_values()
        if len(dados) < 2:
            return pd.DataFrame(columns=["matricula","nome","turma","mencao","ranking","escolha","prof_terca","prof_quarta","tr"])
        # Lê por índice de coluna (A=0, B=1, C=2, D=3, E=4, F=5, G=6, H=7, I=8)
        # Funciona independente do total de colunas na planilha
        rows = []
        for row in dados[1:]:
            while len(row) < 9:
                row.append("")
            rows.append({
                "matricula":  str(row[0]).strip(),
                "nome":       str(row[1]).strip(),
                "turma":      str(row[2]).strip(),
                "mencao":     str(row[3]).strip(),
                "ranking":    str(row[4]).strip(),
                "escolha":    str(row[5]).strip(),
                "prof_terca": str(row[6]).strip(),
                "prof_quarta":str(row[7]).strip(),
                "tr":         str(row[8]).strip(),
            })
        df = pd.DataFrame(rows)
        df = df[df["matricula"] != ""]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar alunos: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=30)
def carregar_cursos():
    ss = get_spreadsheet()
    if not ss:
        return pd.DataFrame()
    try:
        ws = ss.worksheet("Planilha2")
        dados = ws.get_all_values()
        if len(dados) < 2:
            return pd.DataFrame()
        # Colunas: tr(0), codigo(1), nome(2), ..., prof_terca(7), prof_quarta(8)
        rows = []
        for row in dados[1:]:
            while len(row) < 9:
                row.append("")
            if row[1].strip() and not row[1].startswith("#"):
                rows.append({
                    "tr": row[0].strip().upper(),
                    "codigo": row[1].strip(),
                    "nome": row[2].strip() or row[1].strip(),
                    "prof_terca": row[7].strip(),
                    "prof_quarta": row[8].strip(),
                })
        return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Erro ao carregar cursos: {e}")
        return pd.DataFrame()


def invalidar_cache():
    carregar_alunos.clear()
    carregar_cursos.clear()


# ─── FUNÇÕES DE ESCRITA ───────────────────────────────────────────────────────
def matricular_aluno(matricula, codigo_curso):
    """Matricula aluno em um curso na planilha."""
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão com a planilha"
    try:
        ws = ss.worksheet("Planilha1")
        p2 = ss.worksheet("Planilha2")
        
        # Busca professores do curso
        cursos_raw = p2.get_all_values()
        prof_terca, prof_quarta = "", ""
        for row in cursos_raw[1:]:
            while len(row) < 9:
                row.append("")
            if row[1].strip() == codigo_curso:
                prof_terca = row[7].strip()
                prof_quarta = row[8].strip()
                break
        
        # Encontra linha do aluno
        matriculas = ws.col_values(1)
        try:
            idx = next(i for i, m in enumerate(matriculas) if str(m).strip() == str(matricula).strip())
            linha = idx + 1
        except StopIteration:
            return False, f"Matrícula {matricula} não encontrada"
        
        # Atualiza colunas F, G, H
        ws.update(f"F{linha}:H{linha}", [[codigo_curso, prof_terca, prof_quarta]])
        invalidar_cache()
        return True, {"prof_terca": prof_terca, "prof_quarta": prof_quarta}
    except Exception as e:
        return False, str(e)


def limpar_matricula_aluno(matricula):
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão"
    try:
        ws = ss.worksheet("Planilha1")
        matriculas = ws.col_values(1)
        try:
            idx = next(i for i, m in enumerate(matriculas) if str(m).strip() == str(matricula).strip())
            linha = idx + 1
        except StopIteration:
            return False, "Matrícula não encontrada"
        ws.update(f"F{linha}:H{linha}", [["", "", ""]])
        invalidar_cache()
        return True, "Limpo com sucesso"
    except Exception as e:
        return False, str(e)


def marcar_transferido(matricula, desfazer=False):
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão"
    try:
        ws = ss.worksheet("Planilha1")
        matriculas = ws.col_values(1)
        turmas = ws.col_values(3)
        try:
            idx = next(i for i, m in enumerate(matriculas) if str(m).strip() == str(matricula).strip())
            linha = idx + 1
        except StopIteration:
            return False, "Matrícula não encontrada"
        
        turma_atual = turmas[idx] if idx < len(turmas) else ""
        if desfazer:
            nova_turma = turma_atual.replace("-TRANSF", "")
            ws.update_cell(linha, 3, nova_turma)
        else:
            if "-TRANSF" not in turma_atual:
                ws.update_cell(linha, 3, turma_atual + "-TRANSF")
            ws.update(f"F{linha}:H{linha}", [["", "", ""]])
        
        invalidar_cache()
        return True, "OK"
    except Exception as e:
        return False, str(e)


def excluir_aluno(matricula):
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão"
    try:
        ws = ss.worksheet("Planilha1")
        matriculas = ws.col_values(1)
        try:
            idx = next(i for i, m in enumerate(matriculas) if str(m).strip() == str(matricula).strip())
            linha = idx + 1
        except StopIteration:
            return False, "Matrícula não encontrada"
        ws.delete_rows(linha)
        invalidar_cache()
        return True, "Excluído com sucesso"
    except Exception as e:
        return False, str(e)


def adicionar_aluno(matricula, nome, turma, mencao, ranking, tr):
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão"
    try:
        ws = ss.worksheet("Planilha1")
        matriculas = ws.col_values(1)
        if str(matricula).strip() in [str(m).strip() for m in matriculas]:
            return False, f"Matrícula {matricula} já existe"
        ws.append_row([matricula, nome, turma, mencao, ranking, "", "", "", tr])
        invalidar_cache()
        return True, f"Aluno {nome} adicionado com sucesso!"
    except Exception as e:
        return False, str(e)


def editar_aluno(matricula_antiga, matricula_nova, nome, turma, mencao, tr):
    ss = get_spreadsheet()
    if not ss:
        return False, "Sem conexão"
    try:
        ws = ss.worksheet("Planilha1")
        matriculas = ws.col_values(1)
        try:
            idx = next(i for i, m in enumerate(matriculas) if str(m).strip() == str(matricula_antiga).strip())
            linha = idx + 1
        except StopIteration:
            return False, "Matrícula não encontrada"
        ws.update_cell(linha, 1, matricula_nova)
        ws.update_cell(linha, 2, nome)
        ws.update_cell(linha, 3, turma)
        ws.update_cell(linha, 4, mencao)
        ws.update_cell(linha, 9, tr)
        invalidar_cache()
        return True, "Aluno editado com sucesso!"
    except Exception as e:
        return False, str(e)


def realizar_sorteio(alunos_df, cursos_df):
    """Sorteia cursos para alunos sem escolha, priorizando turmas menos cheias."""
    sem_escolha = alunos_df[
        (alunos_df["escolha"].str.strip() == "") & 
        (~alunos_df["turma"].str.contains("TRANSF", na=False))
    ]
    
    if sem_escolha.empty:
        return 0, "Todos os alunos já têm curso"
    
    # Conta vagas ocupadas
    contagem = alunos_df[alunos_df["escolha"].str.strip() != ""]["escolha"].value_counts().to_dict()
    cursos_com_vagas = []
    for _, c in cursos_df.iterrows():
        ocupadas = contagem.get(c["codigo"], 0)
        if ocupadas < VAGAS_MAX:
            cursos_com_vagas.append({"codigo": c["codigo"], "ocupadas": ocupadas})
    
    if not cursos_com_vagas:
        return 0, "Nenhum curso com vagas disponíveis"
    
    sorteados = 0
    for _, aluno in sem_escolha.iterrows():
        if not cursos_com_vagas:
            break
        
        # Peso inversamente proporcional à ocupação
        pool = []
        for c in cursos_com_vagas:
            peso = max(1, 35 - c["ocupadas"])
            pool.extend([c["codigo"]] * peso)
        
        curso_sorteado = random.choice(pool)
        ok, _ = matricular_aluno(aluno["matricula"], curso_sorteado)
        if ok:
            sorteados += 1
            # Atualiza contagem local
            for c in cursos_com_vagas:
                if c["codigo"] == curso_sorteado:
                    c["ocupadas"] += 1
                    if c["ocupadas"] >= VAGAS_MAX:
                        cursos_com_vagas.remove(c)
                    break
    
    return sorteados, f"{sorteados} aluno(s) sorteado(s) com sucesso!"


# ─── GERAÇÃO DE LISTAS ────────────────────────────────────────────────────────
def gerar_lista_turma(alunos_df, turma):
    df = alunos_df[alunos_df["turma"] == turma].sort_values("nome").reset_index(drop=True)
    df.index += 1
    return df[["nome", "escolha", "prof_terca", "prof_quarta"]].rename(columns={
        "nome": "Nome", "escolha": "Trilha/Curso", "prof_terca": "Prof. Terça", "prof_quarta": "Prof. Quarta"
    })


def gerar_lista_professor(alunos_df, professor):
    df_terca = alunos_df[alunos_df["prof_terca"].str.startswith(professor, na=False)].sort_values("nome")
    df_quarta = alunos_df[alunos_df["prof_quarta"].str.startswith(professor, na=False)].sort_values("nome")
    return df_terca, df_quarta


# ─── INTERFACE PRINCIPAL ──────────────────────────────────────────────────────
def main():
    # Estado da sessão
    if "trilha_atual" not in st.session_state:
        st.session_state.trilha_atual = None
    if "curso_filtro" not in st.session_state:
        st.session_state.curso_filtro = None
    if "busca" not in st.session_state:
        st.session_state.busca = ""
    if "aba" not in st.session_state:
        st.session_state.aba = "painel"

    # ── CABEÇALHO ──
    col_titulo, col_nav = st.columns([3, 2])
    with col_titulo:
        st.markdown("### 🎓 Gestão de Percursos 2026")
    with col_nav:
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📊 Painel", use_container_width=True, type="primary" if st.session_state.aba == "painel" else "secondary"):
                st.session_state.aba = "painel"
                st.rerun()
        with col_b:
            if st.button("📋 Listas", use_container_width=True, type="primary" if st.session_state.aba == "listas" else "secondary"):
                st.session_state.aba = "listas"
                st.rerun()
        with col_c:
            if st.button("🔄 Atualizar", use_container_width=True):
                invalidar_cache()
                st.rerun()

    st.divider()

    # ── CARREGA DADOS ──
    with st.spinner("Carregando dados..."):
        df_alunos = carregar_alunos()
        df_cursos = carregar_cursos()

    if df_alunos.empty and df_cursos.empty:
        st.warning("⚠️ Nenhum dado carregado. Verifique a conexão com a planilha.")
        mostrar_instrucoes_config()
        return

    # ── ABA PAINEL ──
    if st.session_state.aba == "painel":
        renderizar_painel(df_alunos, df_cursos)

    # ── ABA LISTAS ──
    elif st.session_state.aba == "listas":
        renderizar_listas(df_alunos, df_cursos)


def renderizar_painel(df_alunos, df_cursos):
    # Métricas gerais
    total_alunos = len(df_alunos[~df_alunos["turma"].str.contains("TRANSF", na=False)])
    com_curso = len(df_alunos[df_alunos["escolha"].str.strip() != ""])
    sem_curso = total_alunos - com_curso
    transferidos = len(df_alunos[df_alunos["turma"].str.contains("TRANSF", na=False)])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👥 Total Alunos", total_alunos)
    with c2:
        st.metric("✅ Com Curso", com_curso, delta=f"{int(com_curso/max(total_alunos,1)*100)}%")
    with c3:
        st.metric("⏳ Sem Curso", sem_curso)
    with c4:
        st.metric("🔄 Transferidos", transferidos)

    st.divider()

    # ── FILTROS ──
    col_trilha, col_busca, col_add, col_sort = st.columns([3, 3, 1, 1])

    with col_trilha:
        st.write("**Filtrar por Trilha:**")
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            if st.button("TODAS", use_container_width=True,
                         type="primary" if st.session_state.trilha_atual is None else "secondary"):
                st.session_state.trilha_atual = None
                st.session_state.curso_filtro = None
                st.rerun()
        with tc2:
            if st.button("TR1", use_container_width=True,
                         type="primary" if st.session_state.trilha_atual == "TR1" else "secondary"):
                st.session_state.trilha_atual = "TR1"
                st.session_state.curso_filtro = None
                st.rerun()
        with tc3:
            if st.button("TR2", use_container_width=True,
                         type="primary" if st.session_state.trilha_atual == "TR2" else "secondary"):
                st.session_state.trilha_atual = "TR2"
                st.session_state.curso_filtro = None
                st.rerun()
        with tc4:
            if st.button("TR3", use_container_width=True,
                         type="primary" if st.session_state.trilha_atual == "TR3" else "secondary"):
                st.session_state.trilha_atual = "TR3"
                st.session_state.curso_filtro = None
                st.rerun()

    with col_busca:
        st.write("**Buscar aluno:**")
        busca = st.text_input("", placeholder="Nome ou matrícula...", key="input_busca", label_visibility="collapsed")

    with col_add:
        st.write("‎")  # espaçador
        if st.button("➕ Aluno", use_container_width=True, type="primary"):
            st.session_state.modal_add = True

    with col_sort:
        st.write("‎")  # espaçador
        if st.session_state.trilha_atual and st.button("🎲 Sortear", use_container_width=True):
            st.session_state.modal_sorteio = True

    # ── CARDS DE CURSOS ──
    if st.session_state.trilha_atual:
        cursos_filtrados = df_cursos[df_cursos["tr"] == st.session_state.trilha_atual]

        if not cursos_filtrados.empty:
            st.write(f"**Cursos - {st.session_state.trilha_atual}** (clique para filtrar alunos)")

            contagem_vagas = df_alunos[df_alunos["escolha"].str.strip() != ""]["escolha"].value_counts().to_dict()

            # Distribui em até 8 colunas
            n_cols = min(8, len(cursos_filtrados) + 1)
            cols = st.columns(n_cols)
            col_idx = 0

            for _, curso in cursos_filtrados.iterrows():
                ocupadas = contagem_vagas.get(curso["codigo"], 0)
                is_lotado = ocupadas >= VAGAS_MAX
                is_selected = st.session_state.curso_filtro == curso["codigo"]

                cor_borda = "#1a73e8" if is_selected else ("#ef5350" if is_lotado else "#66bb6a")
                cor_bg = "#e3f2fd" if is_selected else ("#fce4ec" if is_lotado else "#e8f5e9")
                cor_vagas = "#1a73e8" if is_selected else ("#c62828" if is_lotado else "#2e7d32")

                with cols[col_idx % n_cols]:
                    card_html = f"""
                    <div style="background:{cor_bg}; border:2px solid {cor_borda}; border-radius:8px;
                                padding:8px; text-align:center; margin-bottom:4px; min-height:75px;">
                        <div style="font-size:10px; font-weight:700; color:#333; overflow:hidden;
                                    text-overflow:ellipsis; white-space:nowrap;" title="{curso['nome']}">{curso['codigo']}</div>
                        <div style="font-size:8px; color:#666; margin:2px 0; height:24px; overflow:hidden;">{curso['nome'][:30]}</div>
                        <div style="font-size:18px; font-weight:700; color:{cor_vagas};">{ocupadas}/35</div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    if st.button("sel" if not is_selected else "✓", key=f"card_{curso['codigo']}",
                                 use_container_width=True,
                                 type="primary" if is_selected else "secondary",
                                 help=f"{curso['nome']} | Terça: {curso['prof_terca']} | Quarta: {curso['prof_quarta']}"):
                        if is_selected:
                            st.session_state.curso_filtro = None
                        else:
                            st.session_state.curso_filtro = curso["codigo"]
                        st.rerun()
                col_idx += 1

            # Card Não Enturmados
            nao_enturmados = len(df_alunos[
                (df_alunos["escolha"].str.strip() == "") &
                (~df_alunos["turma"].str.contains("TRANSF", na=False))
            ])
            is_ne_selected = st.session_state.curso_filtro == "NAO_ENTURMADOS"
            with cols[col_idx % n_cols]:
                st.markdown(f"""
                <div style="background:{'#fff9c4' if is_ne_selected else '#fffde7'}; border:2px solid {'#f9a825' if is_ne_selected else '#fdd835'};
                            border-radius:8px; padding:8px; text-align:center; margin-bottom:4px; min-height:75px;">
                    <div style="font-size:9px; font-weight:700; color:#e65100;">SEM CURSO</div>
                    <div style="font-size:8px; color:#666; margin:2px 0;">Não enturmados</div>
                    <div style="font-size:18px; font-weight:700; color:#e65100;">{nao_enturmados}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("sel" if not is_ne_selected else "✓", key="card_nao_enturmados",
                             use_container_width=True,
                             type="primary" if is_ne_selected else "secondary"):
                    st.session_state.curso_filtro = "NAO_ENTURMADOS" if not is_ne_selected else None
                    st.rerun()

    # ── TABELA DE ALUNOS ──
    st.divider()

    # Filtra alunos
    alunos_exibir = df_alunos.copy()

    if st.session_state.trilha_atual:
        alunos_exibir = alunos_exibir[alunos_exibir["tr"].str.upper() == st.session_state.trilha_atual]

    if st.session_state.curso_filtro:
        if st.session_state.curso_filtro == "NAO_ENTURMADOS":
            alunos_exibir = alunos_exibir[
                (alunos_exibir["escolha"].str.strip() == "") &
                (~alunos_exibir["turma"].str.contains("TRANSF", na=False))
            ]
        else:
            alunos_exibir = alunos_exibir[alunos_exibir["escolha"].str.strip() == st.session_state.curso_filtro]

    if busca:
        mask = (
            alunos_exibir["nome"].str.contains(busca, case=False, na=False) |
            alunos_exibir["matricula"].str.contains(busca, case=False, na=False)
        )
        alunos_exibir = alunos_exibir[mask]

    n_exibindo = len(alunos_exibir)
    filtro_desc = ""
    if st.session_state.trilha_atual:
        filtro_desc += f" | {st.session_state.trilha_atual}"
    if st.session_state.curso_filtro:
        filtro_desc += f" | {st.session_state.curso_filtro}"

    st.write(f"**👨‍🎓 Alunos** ({n_exibindo}{filtro_desc})")

    if alunos_exibir.empty:
        st.info("Nenhum aluno encontrado com os filtros aplicados.")
    else:
        # Carrega cursos para o select
        opcoes_cursos = {f"{c['codigo']} - {c['nome']}": c["codigo"]
                        for _, c in df_cursos.iterrows()}
        opcoes_lista = ["-- Selecione --"] + list(opcoes_cursos.keys())

        for _, aluno in alunos_exibir.iterrows():
            matricula = aluno["matricula"]
            is_transf = "TRANSF" in str(aluno["turma"])

            # Linha com cor de fundo
            cor_bg = "#fce4ec" if is_transf else ("#e8f5e9" if aluno["escolha"].strip() else "#fff")
            borda = f"border-left: 4px solid {'#ef5350' if is_transf else ('#4caf50' if aluno['escolha'].strip() else '#ffa726')};"

            with st.container():
                st.markdown(f'<div style="background:{cor_bg}; {borda} border-radius:6px; padding:4px 8px; margin-bottom:2px;">', unsafe_allow_html=True)

                cols_linha = st.columns([0.8, 2.5, 1, 0.8, 0.8, 3, 1.5, 1.5, 0.6, 0.6, 0.6, 0.6])

                with cols_linha[0]:
                    st.caption(f"**{matricula}**")
                with cols_linha[1]:
                    st.caption(f"{'~~' if is_transf else ''}{aluno['nome']}{'~~' if is_transf else ''}")
                with cols_linha[2]:
                    st.caption(aluno["turma"])
                with cols_linha[3]:
                    st.caption(aluno.get("mencao", ""))
                with cols_linha[4]:
                    st.caption(aluno.get("tr", ""))
                with cols_linha[5]:
                    # Select de curso
                    valor_atual = aluno["escolha"].strip()
                    idx_atual = 0
                    if valor_atual:
                        for i, (label, cod) in enumerate(opcoes_cursos.items()):
                            if cod == valor_atual:
                                idx_atual = i + 1
                                break
                    nova_escolha = st.selectbox(
                        "", opcoes_lista, index=idx_atual,
                        key=f"sel_{matricula}", label_visibility="collapsed"
                    )
                with cols_linha[6]:
                    st.caption(aluno.get("prof_terca", ""))
                with cols_linha[7]:
                    st.caption(aluno.get("prof_quarta", ""))
                with cols_linha[8]:
                    if st.button("💾", key=f"save_{matricula}", help="Salvar curso"):
                        if nova_escolha != "-- Selecione --":
                            codigo = opcoes_cursos[nova_escolha]
                            ok, res = matricular_aluno(matricula, codigo)
                            if ok:
                                st.toast(f"✅ Salvo!", icon="✅")
                                st.rerun()
                            else:
                                st.error(res)
                with cols_linha[9]:
                    if st.button("🧹", key=f"limpar_{matricula}", help="Limpar curso"):
                        ok, msg = limpar_matricula_aluno(matricula)
                        if ok:
                            st.toast("Curso limpo!", icon="🧹")
                            st.rerun()
                with cols_linha[10]:
                    label_transf = "↩️" if is_transf else "🔄"
                    help_transf = "Desfazer transferência" if is_transf else "Marcar como transferido"
                    if st.button(label_transf, key=f"transf_{matricula}", help=help_transf):
                        ok, msg = marcar_transferido(matricula, desfazer=is_transf)
                        if ok:
                            st.toast("OK!", icon="✅")
                            st.rerun()
                with cols_linha[11]:
                    if st.button("✏️", key=f"edit_{matricula}", help="Editar aluno"):
                        st.session_state[f"editando_{matricula}"] = True
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

            # Formulário de edição inline
            if st.session_state.get(f"editando_{matricula}"):
                with st.expander(f"✏️ Editando: {aluno['nome']}", expanded=True):
                    ec1, ec2, ec3, ec4, ec5 = st.columns(5)
                    with ec1:
                        e_mat = st.text_input("Matrícula", value=matricula, key=f"emat_{matricula}")
                    with ec2:
                        e_nome = st.text_input("Nome", value=aluno["nome"], key=f"enome_{matricula}")
                    with ec3:
                        e_turma = st.text_input("Turma", value=aluno["turma"].replace("-TRANSF",""), key=f"eturma_{matricula}")
                    with ec4:
                        e_mencao = st.text_input("Menção", value=aluno.get("mencao",""), key=f"emencao_{matricula}")
                    with ec5:
                        e_tr = st.selectbox("TR", ["TR1","TR2","TR3"], 
                                           index=["TR1","TR2","TR3"].index(aluno.get("tr","TR1")) if aluno.get("tr","TR1") in ["TR1","TR2","TR3"] else 0,
                                           key=f"etr_{matricula}")
                    
                    be1, be2, be3 = st.columns([1,1,4])
                    with be1:
                        if st.button("💾 Salvar edição", key=f"salvar_edit_{matricula}", type="primary"):
                            ok, msg = editar_aluno(matricula, e_mat, e_nome, e_turma, e_mencao, e_tr)
                            if ok:
                                st.success(msg)
                                st.session_state.pop(f"editando_{matricula}", None)
                                st.rerun()
                            else:
                                st.error(msg)
                    with be2:
                        if st.button("🗑️ Excluir aluno", key=f"excluir_{matricula}"):
                            st.session_state[f"confirmar_excluir_{matricula}"] = True
                    with be3:
                        if st.button("❌ Cancelar", key=f"cancelar_edit_{matricula}"):
                            st.session_state.pop(f"editando_{matricula}", None)
                            st.rerun()

                    if st.session_state.get(f"confirmar_excluir_{matricula}"):
                        st.warning(f"⚠️ Confirma exclusão de **{aluno['nome']}**?")
                        cx1, cx2 = st.columns(2)
                        with cx1:
                            if st.button("✅ Sim, excluir", key=f"conf_exc_{matricula}", type="primary"):
                                ok, msg = excluir_aluno(matricula)
                                if ok:
                                    st.success("Excluído!")
                                    st.session_state.pop(f"editando_{matricula}", None)
                                    st.session_state.pop(f"confirmar_excluir_{matricula}", None)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        with cx2:
                            if st.button("❌ Cancelar exclusão", key=f"canc_exc_{matricula}"):
                                st.session_state.pop(f"confirmar_excluir_{matricula}", None)
                                st.rerun()

    # ── MODAL ADICIONAR ALUNO ──
    if st.session_state.get("modal_add"):
        with st.expander("➕ Adicionar Novo Aluno", expanded=True):
            ac1, ac2, ac3, ac4, ac5, ac6 = st.columns(6)
            with ac1:
                n_mat = st.text_input("Matrícula *", key="add_mat")
            with ac2:
                n_nome = st.text_input("Nome *", key="add_nome")
            with ac3:
                n_turma = st.text_input("Turma *", key="add_turma")
            with ac4:
                n_mencao = st.text_input("Menção", key="add_mencao")
            with ac5:
                n_ranking = st.text_input("Ranking", key="add_ranking")
            with ac6:
                n_tr = st.selectbox("TR *", ["TR1","TR2","TR3"],
                                    index=["TR1","TR2","TR3"].index(st.session_state.trilha_atual) 
                                    if st.session_state.trilha_atual in ["TR1","TR2","TR3"] else 0,
                                    key="add_tr")
            
            ba1, ba2 = st.columns([1, 5])
            with ba1:
                if st.button("💾 Adicionar", type="primary", key="btn_add_confirm"):
                    if n_mat and n_nome and n_turma:
                        ok, msg = adicionar_aluno(n_mat, n_nome, n_turma, n_mencao, n_ranking, n_tr)
                        if ok:
                            st.success(msg)
                            st.session_state.modal_add = False
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Preencha os campos obrigatórios (*)")
            with ba2:
                if st.button("❌ Fechar", key="btn_add_fechar"):
                    st.session_state.modal_add = False
                    st.rerun()

    # ── MODAL SORTEIO ──
    if st.session_state.get("modal_sorteio"):
        with st.expander("🎲 Sorteio Automático", expanded=True):
            sem_escolha = df_alunos[
                (df_alunos["escolha"].str.strip() == "") &
                (~df_alunos["turma"].str.contains("TRANSF", na=False))
            ]
            if st.session_state.trilha_atual:
                sem_escolha = sem_escolha[sem_escolha["tr"] == st.session_state.trilha_atual]

            contagem = df_alunos[df_alunos["escolha"].str.strip() != ""]["escolha"].value_counts().to_dict()
            cursos_filtros = df_cursos[df_cursos["tr"] == st.session_state.trilha_atual] if st.session_state.trilha_atual else df_cursos
            cursos_com_vagas = sum(1 for _, c in cursos_filtros.iterrows() if contagem.get(c["codigo"], 0) < VAGAS_MAX)

            st.info(f"👥 **{len(sem_escolha)}** aluno(s) sem curso | 📚 **{cursos_com_vagas}** curso(s) com vagas")

            bs1, bs2 = st.columns([1, 5])
            with bs1:
                if st.button("🎲 Sortear agora", type="primary", key="btn_sorteio_confirm"):
                    with st.spinner("Sorteando..."):
                        n, msg = realizar_sorteio(df_alunos, cursos_filtros)
                    st.success(msg)
                    st.session_state.modal_sorteio = False
                    invalidar_cache()
                    st.rerun()
            with bs2:
                if st.button("❌ Fechar", key="btn_sorteio_fechar"):
                    st.session_state.modal_sorteio = False
                    st.rerun()


def renderizar_listas(df_alunos, df_cursos):
    st.subheader("📋 Geração de Listas")

    aba_lista = st.radio("Tipo de lista:", ["Por Turma", "Por Professor"], horizontal=True)

    if aba_lista == "Por Turma":
        turmas_disponiveis = sorted(df_alunos["turma"].unique().tolist())
        turmas_selecionadas = st.multiselect("Selecione a(s) turma(s):", turmas_disponiveis)

        if turmas_selecionadas:
            for turma in turmas_selecionadas:
                st.write(f"### 📚 Turma: {turma}")
                lista = gerar_lista_turma(df_alunos, turma)
                st.dataframe(lista, use_container_width=True, hide_index=False)

                # Botão download CSV
                csv = lista.to_csv(index=True).encode("utf-8")
                st.download_button(
                    f"⬇️ Baixar lista da turma {turma} (.csv)",
                    csv,
                    f"lista_turma_{turma}_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv",
                    key=f"dl_turma_{turma}"
                )

    else:  # Por Professor
        professores = sorted(set(
            list(df_alunos["prof_terca"].str.split(" - ").str[0].dropna().unique()) +
            list(df_alunos["prof_quarta"].str.split(" - ").str[0].dropna().unique())
        ))
        professores = [p for p in professores if p.strip()]

        prof_selecionado = st.selectbox("Selecione o professor:", ["-- Selecione --"] + professores)

        if prof_selecionado and prof_selecionado != "-- Selecione --":
            df_terca, df_quarta = gerar_lista_professor(df_alunos, prof_selecionado)

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"#### 📅 Terça-feira ({len(df_terca)} alunos)")
                if not df_terca.empty:
                    lista_t = df_terca[["nome","turma","escolha"]].rename(
                        columns={"nome":"Nome","turma":"Turma","escolha":"Curso"}
                    ).reset_index(drop=True)
                    lista_t.index += 1
                    st.dataframe(lista_t, use_container_width=True)
                    csv_t = lista_t.to_csv(index=True).encode("utf-8")
                    st.download_button("⬇️ Baixar Terça (.csv)", csv_t,
                                       f"lista_{prof_selecionado}_terca.csv", "text/csv",
                                       key="dl_terca")
                else:
                    st.info("Nenhum aluno na terça")

            with col2:
                st.write(f"#### 📅 Quarta-feira ({len(df_quarta)} alunos)")
                if not df_quarta.empty:
                    lista_q = df_quarta[["nome","turma","escolha"]].rename(
                        columns={"nome":"Nome","turma":"Turma","escolha":"Curso"}
                    ).reset_index(drop=True)
                    lista_q.index += 1
                    st.dataframe(lista_q, use_container_width=True)
                    csv_q = lista_q.to_csv(index=True).encode("utf-8")
                    st.download_button("⬇️ Baixar Quarta (.csv)", csv_q,
                                       f"lista_{prof_selecionado}_quarta.csv", "text/csv",
                                       key="dl_quarta")
                else:
                    st.info("Nenhum aluno na quarta")


def mostrar_instrucoes_config():
    with st.expander("⚙️ Como configurar a conexão com o Google Sheets", expanded=True):
        st.markdown("""
        ### Passo 1 — Crie a Conta de Serviço Google

        1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
        2. Crie um projeto (ou use um existente)
        3. Ative as APIs: **Google Sheets API** e **Google Drive API**
        4. Vá em **IAM e Administrador → Contas de Serviço**
        5. Crie uma conta de serviço e gere uma chave JSON
        6. **Compartilhe** sua planilha com o e-mail da conta de serviço (como Editor)

        ### Passo 2 — Configure os Secrets no Streamlit Cloud

        No painel do seu app em [share.streamlit.io](https://share.streamlit.io), vá em **Settings → Secrets** e cole:

        ```toml
        sheet_id = "ID_DA_SUA_PLANILHA_AQUI"

        [gcp_service_account]
        type = "service_account"
        project_id = "seu-projeto"
        private_key_id = "..."
        private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
        client_email = "sua-conta@projeto.iam.gserviceaccount.com"
        client_id = "..."
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "..."
        ```

        ### Passo 3 — Para testar localmente

        Crie o arquivo `.streamlit/secrets.toml` com o mesmo conteúdo acima.

        ### ID da sua Planilha
        O ID está na URL do Google Sheets:
        `https://docs.google.com/spreadsheets/d/**[ID_AQUI]**/edit`
        """)


if __name__ == "__main__":
    main()
