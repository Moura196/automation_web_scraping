import os
import tempfile
import streamlit as st
import pandas as pd

from valores_produtos import runner

st.set_page_config(page_title="Busca de Produtos", layout="wide")
st.title("Busca de Produtos — Upload Excel → Busca → Download")

uploaded = st.file_uploader("Envie um arquivo .xlsx ou .csv com a lista de produtos", type=["xlsx", "csv"])
if not uploaded:
    st.info("Faça upload de um arquivo para começar.")
    st.stop()

suffix = os.path.splitext(uploaded.name)[1]
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
tmp.write(uploaded.getvalue())
tmp.flush()
tmp_path = tmp.name

try:
    if suffix.lower() == ".csv":
        df = pd.read_csv(tmp_path)
    else:
        df = pd.read_excel(tmp_path)
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

st.write("Arquivo carregado — colunas detectadas:", list(df.columns))
query_col = st.selectbox("Selecione a coluna que contém o termo de busca", options=list(df.columns))

max_rows = st.number_input("Limitar número de linhas (0 = todas)", min_value=0, value=0, step=1)

if st.button("Executar busca"):
    rows = df if max_rows == 0 else df.head(int(max_rows))
    with st.spinner("Executando buscas — isto pode demorar dependendo do número de consultas..."):
        try:
            out_path = runner.process_file(tmp_path, query_col, rows=rows)
        except Exception as e:
            st.error(f"Falha na execução: {e}")
            st.stop()

    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            data = f.read()
        st.success("Busca concluída")
        st.download_button("Baixar resultados (.xlsx)", data, file_name=os.path.basename(out_path))
    else:
        st.error("Nenhum resultado gerado.")
