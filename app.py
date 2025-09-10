import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import io
from datetime import datetime, time, timedelta
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
st.title("📚 Registro Atividades do Curso de Mediação")
st.subheader("Turma Mediadores - Floriano/PI")

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

# ✅ Progresso na barra lateral
st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Progresso (meta: 60h)")

conn = sqlite3.connect("database.db")
df_sidebar = pd.read_sql_query("SELECT aluno, duracao_horas FROM participacoes", conn)
conn.close()

if tipo_usuario == "admin":
    total_por_aluno = df_sidebar.groupby("aluno")["duracao_horas"].sum().sort_values(ascending=False)

    for aluno, horas in total_por_aluno.items():
        if horas >= 60:
            st.sidebar.success(f"{aluno}: {horas:.1f}h ✅")
        else:
            restante = 60 - horas
            st.sidebar.warning(f"{aluno}: {horas:.1f}h ({restante:.1f}h faltam)")
else:
    total_aluno = df_sidebar[df_sidebar["aluno"] == usuario]["duracao_horas"].sum()

    if total_aluno >= 60:
        st.sidebar.success(f"Você completou {total_aluno:.1f}h ✅")
    else:
        restante = 60 - total_aluno
        st.sidebar.warning(f"Você tem {total_aluno:.1f}h\nFaltam {restante:.1f}h")
        

# Criar tabela se necessário
criar_tabela()

# ABAS
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Registro",
    "📊 Relatório",
    "📤 Exportação Total de Horas",
    "📒 Planilha Geral",
    "❓ Ajuda"
])


# -----------------------------
# 📋 REGISTRO DE PARTICIPAÇÃO
# -----------------------------
# Dentro da aba "📋 Registro"
# Dentro da aba "📋 Registro"
# Dentro da aba "📋 Registro"
with tab1:
    if "mostrar_co" not in st.session_state:
        st.session_state["mostrar_co"] = False

    editando = "editando_id" in st.session_state

    with st.form("registro_form"):
        # Dados do registro atual (edição ou novo)
        if editando:
            conn = sqlite3.connect("database.db")
            row = conn.execute("SELECT * FROM participacoes WHERE id = ?", (st.session_state["editando_id"],)).fetchone()
            conn.close()

            if row:
                data = st.date_input("Data da atividade", datetime.strptime(row[2], "%Y-%m-%d"))
                hora_inicio = st.time_input("Hora inicial", datetime.strptime(row[3], "%H:%M:%S").time())
                hora_fim = st.time_input("Hora final", datetime.strptime(row[4], "%H:%M:%S").time())
                tipo = st.selectbox("Tipo de atividade", ["Mediação", "Co-mediação", "Observação"], index=["Mediação", "Co-mediação", "Observação"].index(row[5]))

                observadores_lista = row[6].split(", ") if row[6] else []
                outro_comediador = row[7] or ""
                aluno_alvo = row[1]
            else:
                st.error("Erro ao carregar registro para edição.")
                del st.session_state["editando_id"]
                st.rerun()
        else:
            data = st.date_input("Data da atividade")
            # hora_inicio = st.time_input("Hora inicial", time(9, 0))
            # hora_fim = st.time_input("Hora final", time(13, 0))
            hora_inicio = st.time_input("Hora inicial", value=time(9, 0), step=timedelta(minutes=5))
            hora_fim = st.time_input("Hora final", value=time(13, 0), step=timedelta(minutes=5))

            tipo = st.selectbox("Tipo de atividade", ["Mediação", "Co-mediação", "Observação"])
            observadores_lista = []
            outro_comediador = ""
            aluno_alvo = usuario

        if tipo_usuario == "admin":
            aluno_alvo = st.selectbox("Aluno referente ao registro", ALUNOS, index=ALUNOS.index(aluno_alvo) if editando else 0)

        col1, col2, col3 = st.columns([1, 1, 5])
        with col1:
            if st.form_submit_button("➕"):
                st.session_state["mostrar_co"] = True
        with col2:
            if st.form_submit_button("➖"):
                st.session_state["mostrar_co"] = False
        with col3:
            st.markdown("ℹ️ Clique em '➕' para adicionar um co-mediador **apenas se a atividade for Co-mediação**.")

        if st.session_state["mostrar_co"]:
            outro_comediador = st.selectbox("Outro co-mediador", [a for a in ALUNOS if a != aluno_alvo])

        if tipo in ["Mediação", "Co-mediação"]:
            observadores_lista = st.multiselect("Quem observou essa atividade?", [a for a in ALUNOS if a != aluno_alvo], default=observadores_lista)

        enviado = st.form_submit_button("Salvar participação")

    if enviado:
        duracao = calcular_duracao(hora_inicio, hora_fim)

        if duracao <= 0:
            st.error("⚠️ Hora final deve ser maior que a hora inicial.")
        else:
            conn = sqlite3.connect("database.db")

            if editando:
                conn.execute("""
                    UPDATE participacoes
                    SET aluno = ?, data = ?, hora_inicio = ?, hora_fim = ?, tipo_atividade = ?, observadores = ?, co_mediador = ?, duracao_horas = ?
                    WHERE id = ?
                """, (
                    aluno_alvo, str(data), str(hora_inicio), str(hora_fim), tipo,
                    ", ".join(observadores_lista), outro_comediador, duracao,
                    st.session_state["editando_id"]
                ))
                st.success("✅ Registro atualizado com sucesso!")
                del st.session_state["editando_id"]
            else:
                inserir_participacao(
                    aluno_alvo, data, hora_inicio, hora_fim,
                    tipo, ", ".join(observadores_lista), outro_comediador, duracao
                )
                st.success(f"✅ Participação registrada com sucesso! ({duracao} horas)")

            conn.commit()
            conn.close()
            st.session_state["mostrar_co"] = False
            st.rerun()

    # -----------------------------
    # 🧾 Listagem de registros
    # -----------------------------
    st.markdown("---")
    st.subheader("🧾 Registros")

    conn = sqlite3.connect("database.db")
    if tipo_usuario == "admin":
        df_meus = pd.read_sql_query("SELECT * FROM participacoes", conn)
    else:
        df_meus = pd.read_sql_query("SELECT * FROM participacoes WHERE aluno = ?", conn, params=(usuario,))
    conn.close()

    if df_meus.empty:
        st.info("Nenhum registro encontrado.")
    else:
        df_meus["data"] = pd.to_datetime(df_meus["data"]).dt.strftime("%d/%m/%Y")

        for i, row in df_meus.iterrows():
            with st.expander(f"{row['aluno']} - {row['data']} - {row['tipo_atividade']} ({row['duracao_horas']}h)"):
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button(f"📝 Editar #{row['id']}", key=f"editar_{row['id']}"):
                        st.session_state["editando_id"] = row["id"]
                        st.rerun()
                with col2:
                    if st.button(f"❌ Excluir #{row['id']}", key=f"excluir_{row['id']}"):
                        conn = sqlite3.connect("database.db")
                        conn.execute("DELETE FROM participacoes WHERE id = ?", (row["id"],))
                        conn.commit()
                        conn.close()
                        st.success("Registro excluído com sucesso.")
                        st.rerun()


        # if enviado:
        #     duracao = calcular_duracao(hora_inicio, hora_fim)

        #     if duracao <= 0:
        #         st.error("⚠️ Hora final deve ser maior que a hora inicial.")
        #     else:
        #         inserir_participacao(
        #             usuario, data, hora_inicio, hora_fim,
        #             tipo, observadores, outro_comediador, duracao
        #         )
        #         st.success(f"✅ Participação registrada com sucesso! ({duracao} horas)")
        #         st.session_state["mostrar_co"] = False


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
    st.subheader("🎯 Acompanhamento por aluno vs Meta Geral (60h acumuladas)")

    # Total geral por aluno (somando todas as atividades)
    total_por_aluno = df.groupby("aluno")["duracao_horas"].sum()

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(total_por_aluno.index, total_por_aluno.values)

    # Linha de meta
    ax.axhline(y=60, color='red', linestyle='--', label='Meta: 60h')

    # Adiciona rótulo acima de cada barra
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 1, f"{height:.1f}", ha='center')

    ax.set_ylabel("Total de Horas")
    ax.set_xlabel("Aluno")
    ax.set_title("Horas acumuladas (total geral)")
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

    # if df.empty:
    #     st.info("Este aluno ainda não possui registros.")
    #     st.stop()
    
    
    if df.empty:
        st.info("Este aluno ainda não possui registros.")
    else:
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
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"download_individual_{aluno_export}"  # chave única
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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_geral"
        )


# -----------------------------
# ❓ AJUDA
# -----------------------------
with tab5:
    st.subheader("🆘 Guia de Uso")

    st.markdown("""
    ### 📋 Aba "Registro"
    - Preencha os dados da atividade.
    - Se for **Co-mediação**, clique em ➕ para adicionar o co-mediador.
    - Se outros alunos participaram como observadores, selecione-os.
    - Clique em "Salvar participação".
    - Você verá seus registros abaixo, com opções de editar ou excluir.

    ### 📊 Aba "Relatório"
    - Veja os registros (apenas os seus, se for aluno).
    - Use os filtros para visualizar por aluno ou tipo de atividade.
    - Gráficos mostram o progresso das horas por tipo.

    ### 📤 Aba "Exportação Total de Horas"
    - Gere uma planilha individual formatada com as horas de um aluno.
    - Segue o modelo oficial.

    ### 📒 Aba "Planilha Geral"
    - Gera uma planilha com todos os alunos.
    - Cada aluno tem uma aba com suas horas e totais.

    ### ❓ Aba "Ajuda"
    - Você está aqui! Use este espaço como referência rápida.

    ### 🔐 Login
    - Alunos só acessam e gerenciam seus registros.
    - Administradores visualizam todos e podem editar qualquer um.
    """)




   



