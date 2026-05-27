import os
import tempfile
import streamlit as st
import pandas as pd

from valores_produtos import runner

# Used to set the configuration of the Streamlit page. In this case, sets the title of the web page
st.set_page_config(page_title="Busca de Produtos", layout="wide")
st.title("Busca de Produtos — Upload Excel → Busca → Download")

# Create a file uploader widget using Streamlit. The `st.file_uploader` function allow the user to upload a file with 
# the specified file types (in this case,".xlsx").
uploaded = st.file_uploader("Envie um arquivo .xlsx com a lista de produtos e suas características", type=["xlsx"])
if not uploaded:
    st.info("Faça upload de um arquivo para começar.")
    st.stop()

# Handling the uploaded file in the Streamlit app. Here's a breakdown of what each line is doing:
# Extracting the file extension from the name of the uploaded file.
suffix = os.path.splitext(uploaded.name)[1]
# Creating a temporary file using the `tempfile` module in Python. Here's a breakdown of what it's doing:
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
# Writing the contents of the uploaded file into the temporary file. Necessary to save the uploaded file data into a 
# temporary file so that it can be processed further, using pandas for analysis or any other operations required in the 
# Streamlit application.
tmp.write(uploaded.getvalue())
# Flush the temporary file to ensure buffered data is written to disk.
# This should be called after tmp.write().
tmp.flush()
# Assigning the file path of the temporary file created to the variable `tmp_path`. 
# Ensures that the file path of the temporary file is stored in the `tmp_path` variable for further 
# processing, such as reading its contents using pandas for analysis or any other operations required in the 
# Streamlit application.
tmp_path = tmp.name

# This block of code is responsible for reading the uploaded file based on its extension. Here's a
# breakdown of what it does:
try:
    df = pd.read_excel(tmp_path)
except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

# Displaying a message indicating that the file has been loaded successfully, along with the detected columns in the 
# uploaded Excel file. It shows the user the columns present in the DataFrame `df` by listing them.
st.write("Arquivo carregado — colunas detectadas:", list(df.columns))

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
