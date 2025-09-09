import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import io
from datetime import datetime, time
from database import criar_tabela, inserir_participacao
from utils import calcular_duracao

# Lista de alunos
ALUNOS = ["ALICIA", "DIONE", "EDJANE", "HOSLANDIA", "JANILCE", "PEDRO", "SAYANE", "UESLLEI"]

# Usuários e senhas (login simples)
USUARIOS = {
    "ALICIA": {"senha": "1234", "tipo": "aluno"},
    "DIONE": {"senha": "1234", "tipo": "aluno"},
    "EDJANE": {"senha": "1234", "tipo": "aluno"},
    "HOSLANDIA": {"senha": "1234", "tipo": "aluno"},
    "JANILCE": {"senha": "1234", "tipo": "aluno"},
    "PEDRO": {"senha": "1234", "tipo": "aluno"},
    "SAYANE": {"senha": "1234", "tipo": "aluno"},
    "UESLLEI": {"senha": "1234", "tipo": "aluno"},
    "ADM": {"senha": "admin", "tipo": "admin"},
}

st.set_page_config(page_title="Curso de Mediação", layout="wide")
st.title("📚 Refistro Atividades do Curso de Mediação")

# Sessão de login
if "usuario" not in st.session_state:
    with st.form("login"):
        st.subheader("🔐 Login")
        usuario = st.selectbox("Usuário", list(USUARIOS.keys()))
        senha = st.text_input("Senha", type="password")
        login = st.form_submit_button("Entrar")

        if login:
            if USUARIOS.get(usuario) and USUARIOS[usuario]["senha"] == senha:
                st.session_state["usuario"] = usuario
                st.session_state["tipo"] = USUARIOS[usuario]["tipo"]
                st.rerun()

            else:
                st.error("Usuário ou senha incorretos.")
    st.stop()

# Variáveis de sessão
usuario = st.session_state["usuario"]
tipo_usuario = st.session_state["tipo"]
st.sidebar.success(f"👤 Usuário: {usuario} ({tipo_usuario})")

# Botão sair
if st.sidebar.button("🚪 Sair"):
    st.session_state.clear()
    st.rerun()


# Criar tabela se necessário
criar_tabela()

# ABAS
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Registro",
    "📊 Relatório",
    "📤 Exportação Total de Horas",
    "📒 Planilha Geral"
])


# -----------------------------
# 📋 REGISTRO DE PARTICIPAÇÃO
# -----------------------------
with tab1:
    if "mostrar_co" not in st.session_state:
        st.session_state["mostrar_co"] = False

    with st.form("registro_form"):
        st.subheader("Preencher participação")

        data = st.date_input("Data da atividade")
        hora_inicio = st.time_input("Hora inicial", time(9, 0))
        hora_fim = st.time_input("Hora final", time(13, 0))
        tipo = st.selectbox("Tipo de atividade", ["Mediação", "Co-mediação", "Observação"])

        col1, col2, col3 = st.columns([1, 1, 5])
        with col1:
            if st.form_submit_button("➕"):
                st.session_state["mostrar_co"] = True
        with col2:
            if st.form_submit_button("➖"):
                st.session_state["mostrar_co"] = False
        with col3:
            st.markdown("ℹ️ Clique em '➕' para adicionar um co-mediador **apenas se a atividade for Co-mediação**.")

        outro_comediador = ""
        if st.session_state["mostrar_co"]:
            outro_comediador = st.selectbox(
                "Outro co-mediador",
                options=[a for a in ALUNOS if a != usuario]
            )

        observadores_lista = []
        if tipo in ["Mediação", "Co-mediação"]:
            observadores_lista = st.multiselect("Quem observou essa atividade?", [a for a in ALUNOS if a != usuario])
        observadores = ", ".join(observadores_lista)

        enviado = st.form_submit_button("Salvar participação")

        if enviado:
            duracao = calcular_duracao(hora_inicio, hora_fim)

            if duracao <= 0:
                st.error("⚠️ Hora final deve ser maior que a hora inicial.")
            else:
                inserir_participacao(
                    usuario, data, hora_inicio, hora_fim,
                    tipo, observadores, outro_comediador, duracao
                )
                st.success(f"✅ Participação registrada com sucesso! ({duracao} horas)")
                st.session_state["mostrar_co"] = False


with tab2:
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM participacoes", conn)
    conn.close()

    if df.empty:
        st.warning("Nenhuma participação registrada ainda.")
        st.stop()

    df["data"] = pd.to_datetime(df["data"])
    df["hora_inicio"] = pd.to_datetime(df["hora_inicio"], format="%H:%M:%S").dt.time
    df["hora_fim"] = pd.to_datetime(df["hora_fim"], format="%H:%M:%S").dt.time

    # Se for aluno, filtra os dados
    if tipo_usuario == "aluno":
        df = df[df["aluno"] == usuario]

    st.subheader("📅 Filtros")
    col1, col2 = st.columns(2)
    with col1:
        aluno_filtro = st.multiselect("Filtrar por aluno(s)", options=sorted(df["aluno"].unique()))
    with col2:
        tipo_filtro = st.multiselect("Filtrar por tipo de atividade", options=sorted(df["tipo_atividade"].unique()))

    df_filtrado = df.copy()
    if aluno_filtro:
        df_filtrado = df_filtrado[df_filtrado["aluno"].isin(aluno_filtro)]
    if tipo_filtro:
        df_filtrado = df_filtrado[df_filtrado["tipo_atividade"].isin(tipo_filtro)]

    st.dataframe(df_filtrado.sort_values(by="data", ascending=False), use_container_width=True)
    # -----------------------------
# 📊 RELATÓRIO E GRÁFICOS
# -----------------------------
 # 📊 Gráfico por tipo
    st.subheader("⏱️ Total de horas por aluno e tipo de atividade")
    grafico_df = df.groupby(["aluno", "tipo_atividade"])["duracao_horas"].sum().reset_index()
    pivot = grafico_df.pivot(index="aluno", columns="tipo_atividade", values="duracao_horas").fillna(0)
    st.bar_chart(pivot)

    # 🎯 Gráfico com meta
    st.subheader("🎯 Acompanhamento por aluno vs Meta (60h por tipo)")
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in pivot.columns:
        ax.bar(pivot.index, pivot[col], label=col)
    ax.axhline(y=60, color='red', linestyle='--', label='Meta 60h')
    ax.set_ylabel("Horas")
    ax.set_title("Horas acumuladas por tipo de atividade")
    ax.legend()
    st.pyplot(fig)

    # 🔽 Exportar para Excel
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_filtrado.to_excel(writer, index=False, sheet_name="Participações")
        writer.close()

    st.download_button(
        label="📥 Baixar Excel",
        data=buffer.getvalue(),
        file_name="relatorio_participacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
with tab3:
    st.subheader("📤 Gerar planilha individual de horas")

    aluno_export = st.selectbox("Selecione o aluno", ALUNOS)

    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT * FROM participacoes WHERE aluno = ?", conn, params=(aluno_export,))
    conn.close()

    if df.empty:
        st.info("Este aluno ainda não possui registros.")
        st.stop()

    df["data"] = pd.to_datetime(df["data"])
    df = df.sort_values(by="data")

    df_export = pd.DataFrame()
    df_export["DATA"] = df["data"].dt.strftime("%d/%m/%Y")
    df_export["ENTRADA"] = pd.to_datetime(df["hora_inicio"], format="%H:%M:%S").dt.strftime("%H:%M")
    df_export["SAÍDA"] = pd.to_datetime(df["hora_fim"], format="%H:%M:%S").dt.strftime("%H:%M")
    df_export["TOTAL DE HORAS"] = df["duracao_horas"]

    # Cabeçalhos e informações iniciais (alinhadas corretamente nas colunas)
    header_info = [
        ["CONTROLE DE ESTÁGIO MEDIADOR EM FORMAÇÃO", "", "", ""],
        ["", "", "", ""],
        [f"NOME DO(A) MEDIADOR(A): {aluno_export}", "", "", ""],
        ["", "", "", ""],
        ["DATA", "ENTRADA", "SAÍDA", "TOTAL DE HORAS"]
    ]
    header_df = pd.DataFrame(header_info, columns=["DATA", "ENTRADA", "SAÍDA", "TOTAL DE HORAS"])

    # Linha de total
    linha_total = pd.DataFrame(
        [["", "", "TOTAL", df["duracao_horas"].sum()]],
        columns=df_export.columns
    )

    # Juntar tudo: cabeçalho + dados + total
    final_df = pd.concat([header_df, df_export, linha_total], ignore_index=True)

    # Exportar para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, header=False, sheet_name="Página1")

    st.download_button(
        label="📥 Baixar planilha formatada",
        data=output.getvalue(),
        file_name=f"contagem_{aluno_export.lower()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

with tab4:
    st.subheader("📒 Gerar planilha geral com todos os alunos")

    gerar = st.button("📥 Gerar planilha geral")

    if gerar:
        conn = sqlite3.connect("database.db")
        df = pd.read_sql_query("SELECT * FROM participacoes", conn)
        conn.close()

        if df.empty:
            st.warning("Nenhum dado encontrado no banco.")
            st.stop()

        df["data"] = pd.to_datetime(df["data"])
        df = df.sort_values(by=["aluno", "data"])

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            for aluno in ALUNOS:
                df_aluno = df[df["aluno"] == aluno]

                if df_aluno.empty:
                    continue

                df_export = pd.DataFrame()
                df_export["DATA"] = df_aluno["data"].dt.strftime("%d/%m/%Y")
                df_export["ENTRADA"] = pd.to_datetime(df_aluno["hora_inicio"], format="%H:%M:%S").dt.strftime("%H:%M")
                df_export["SAÍDA"] = pd.to_datetime(df_aluno["hora_fim"], format="%H:%M:%S").dt.strftime("%H:%M")
                df_export["TOTAL DE HORAS"] = df_aluno["duracao_horas"]

                # Cabeçalho formatado
                header_info = [
                    ["CONTROLE DE ESTÁGIO MEDIADOR EM FORMAÇÃO", "", "", ""],
                    ["", "", "", ""],
                    [f"NOME DO(A) MEDIADOR(A): {aluno}", "", "", ""],
                    ["", "", "", ""],
                    ["DATA", "ENTRADA", "SAÍDA", "TOTAL DE HORAS"]
                ]
                header_df = pd.DataFrame(header_info, columns=["DATA", "ENTRADA", "SAÍDA", "TOTAL DE HORAS"])

                # Linha de total
                linha_total = pd.DataFrame(
                    [["", "", "TOTAL", df_aluno["duracao_horas"].sum()]],
                    columns=df_export.columns
                )

                # Junta tudo
                final_df = pd.concat([header_df, df_export, linha_total], ignore_index=True)

                # Grava na aba do Excel
                final_df.to_excel(writer, index=False, header=False, sheet_name=aluno)

        st.success("✅ Planilha gerada com sucesso!")

        st.download_button(
            label="📄 Baixar Planilha Geral",
            data=output.getvalue(),
            file_name="planilha_geral_participacoes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )




   



# import streamlit as st
# from datetime import datetime, time
# from database import criar_tabela, inserir_participacao
# from utils import calcular_duracao

# # Lista de alunos
# ALUNOS = ["ALICIA", "DIONE", "EDJANE", "HOSLANDIA", "JANILCE", "PEDRO", "SAYANE", "UESLLEI"]

# st.set_page_config(page_title="Registro de Participação", layout="centered")

# st.title("📋 Registro de Participação no Curso de Mediação")

# # Criar tabela se ainda não existir
# criar_tabela()

# # Inicialização da flag para mostrar campo extra
# if "mostrar_co" not in st.session_state:
#     st.session_state["mostrar_co"] = False

# # --- FORMULÁRIO ---
# with st.form("registro_form"):
#     st.subheader("Preencher participação")

#     aluno = st.selectbox("Quem está preenchendo?", ALUNOS)
#     data = st.date_input("Data da atividade")
#     hora_inicio = st.time_input("Hora inicial", time(9, 0))
#     hora_fim = st.time_input("Hora final", time(13, 0))
#     tipo = st.selectbox("Tipo de atividade", ["Mediação", "Co-mediação", "Observação"])

#     # Botões "Mais" e "Menos" lado a lado com instrução
#     col1, col2, col3 = st.columns([1, 1, 5])
#     with col1:
#         if st.form_submit_button("➕"):
#             st.session_state["mostrar_co"] = True
#     with col2:
#         if st.form_submit_button("➖"):
#             st.session_state["mostrar_co"] = False
#     with col3:
#         st.markdown("ℹ️ Clique em '➕' para adicionar um co-mediador **apenas se a atividade for Co-mediação**.")

#     outro_comediador = ""
#     if st.session_state["mostrar_co"]:
#         outro_comediador = st.selectbox(
#             "Outro co-mediador",
#             options=[a for a in ALUNOS if a != aluno]
#         )

#     observadores = ""
#     if tipo in ["Mediação", "Co-mediação"]:
#         observadores_lista = st.multiselect("Quem observou essa atividade?", [a for a in ALUNOS if a != aluno])
#         observadores = ", ".join(observadores_lista)

#     enviado = st.form_submit_button("Salvar participação")

#     if enviado:
#         duracao = calcular_duracao(hora_inicio, hora_fim)

#         if duracao <= 0:
#             st.error("⚠️ Hora final deve ser maior que a hora inicial.")
#         else:
#             # Inclui o co-mediador na descrição se necessário
#             if tipo == "Co-mediação" and outro_comediador:
#                 observadores = f"{observadores} | Co-mediador: {outro_comediador}".strip(" |")

#             inserir_participacao(aluno, data, hora_inicio, hora_fim, tipo, observadores, outro_comediador, duracao)
#             st.success(f"✅ Participação registrada com sucesso! ({duracao} horas)")
#             st.session_state["mostrar_co"] = False