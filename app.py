"""
Web Scraping Project - Streamlit Application
Main UI for product scraping and price search
"""

import os
import tempfile
import streamlit as st
import pandas as pd
from pathlib import Path

# Import our modules
from src.input_handler import load_products_dataframe, is_template_available, get_template_path
from src.product_query_builder import build_queries_from_dataframe, validate_queries
from src.output_handler import get_default_output_path, export_results_to_excel, ScrapingResult
from src.logger import setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='logs/app.log')

# Page configuration
st.set_page_config(
    page_title="Busca de Produtos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🔍 Busca de Produtos — Upload Excel → Busca → Download")
st.markdown("""
Carregue uma planilha com produtos e características para buscar preços em plataformas de e-commerce.
""")

# Sidebar - Help and template
with st.sidebar:
    st.header("📋 Instruções")
    
    st.markdown("""
    ### Formato esperado:
    - **Coluna A**: Produto (obrigatório)
    - **Colunas B-K**: Descrição 1 até Descrição 10 (opcionais)
    
    ### Exemplo:
    | Produto | Descrição 1 | Descrição 2 |
    |---------|-------------|------------|
    | Luva    | correr      | 20mm       |
    | Meia    | algodão     |            |
    
    ✅ Suporta 1 a 10 descrições  
    ⚠️ Avisos em caso de inconsistências  
    ✅ Processa mesmo com avisos
    """)
    
    st.divider()
    
    # Template download
    if is_template_available():
        st.subheader("📥 Template")
        with open(get_template_path(), 'rb') as f:
            st.download_button(
                label="Baixar template",
                data=f.read(),
                file_name="template_entrada.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    st.divider()
    
    st.subheader("⚙️ Configurações")
    max_rows = st.number_input(
        "Limitar a quantas linhas?",
        min_value=0,
        value=0,
        help="0 = sem limite"
    )

# Main content
st.header("1️⃣ Carregue seu arquivo")

# File uploader
uploaded_file = st.file_uploader(
    "Envie um arquivo .xlsx",
    type=["xlsx"],
    help="Arquivo com produtos e características"
)

if not uploaded_file:
    st.info("👈 Use o template para criar sua planilha. Em seguida, faça upload aqui.")
    st.stop()

# Save uploaded file temporarily
suffix = os.path.splitext(uploaded_file.name)[1]
tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
tmp_file.write(uploaded_file.getvalue())
tmp_file.flush()
tmp_path = tmp_file.name

logger.info(f"Arquivo carregado: {uploaded_file.name}")

# Process and validate file
st.header("2️⃣ Validação")

st.info("Validando arquivo...")

df_standardized, warnings_list = load_products_dataframe(tmp_path)

# Show validation results
if df_standardized is None:
    st.error("❌ Erro crítico ao processar arquivo")
    for warning in warnings_list:
        if warning['level'] == 'critical':
            st.error(f"**{warning['message']}**")
    st.stop()

# Display warnings and info messages
if warnings_list:
    st.warning("⚠️ Avisos durante validação:")
    for warning in warnings_list:
        if warning['level'] == 'critical':
            st.error(f"• {warning['message']}")
        elif warning['level'] == 'warning':
            st.warning(f"• {warning['message']}")
        else:  # info
            st.info(f"• {warning['message']}")
else:
    st.success("✓ Arquivo validado sem avisos")

# Show data preview
st.subheader("Dados carregados")
preview_df = df_standardized.head(10)

# Remove empty description columns for preview
non_empty_cols = ['Produto']
for col in df_standardized.columns[1:]:
    if df_standardized[col].notna().any():
        non_empty_cols.append(col)

preview_df = preview_df[non_empty_cols]

st.dataframe(preview_df, use_container_width=True)

st.write(f"✓ {len(df_standardized)} linhas carregadas")

# Apply row limit if specified
if max_rows > 0:
    df_to_process = df_standardized.head(max_rows)
    st.info(f"Limitando a {max_rows} linhas")
else:
    df_to_process = df_standardized

# Build queries
st.header("3️⃣ Construção de Queries")

st.info("Construindo queries de busca...")
df_with_queries = build_queries_from_dataframe(df_to_process)

# Validate queries
all_valid, invalid_queries = validate_queries(df_with_queries['Query'].tolist())

if not all_valid:
    st.warning(f"⚠️ {len(invalid_queries)} queries podem ter problemas de formatação")
else:
    st.success(f"✓ {len(df_with_queries)} queries construídas com sucesso")

# Show query preview
st.subheader("Preview de queries")
query_preview = df_with_queries[['Produto', 'Query']].head(10)
st.dataframe(query_preview, use_container_width=True)

# Search execution
st.header("4️⃣ Execução de Busca")

if st.button("🔍 Executar busca", use_container_width=True, type="primary"):
    
    with st.spinner("⏳ Executando buscas... isto pode demorar alguns minutos..."):
        
        st.info("Este é um protótipo. Em produção, aqui seria integrada a lógica de scraping.")
        
        # TODO: Integrate actual scraping logic here
        # For now, create dummy results for demonstration
        
        st.success("✓ Busca simulada concluída")
        
        # Create dummy results for demonstration
        results = [
            ScrapingResult(
                query=row['Query'],
                preco=29.90 + (idx * 2.5),
                link=f"https://example.com/produto/{idx}",
                plataforma="Google Shopping" if idx % 2 == 0 else "Mercado Livre",
                timestamp=None
            )
            for idx, (_, row) in enumerate(df_with_queries.iterrows())
        ]
        
        # Export results
        output_path = get_default_output_path()
        from src.output_handler import create_results_dataframe
        df_results = create_results_dataframe(results)
        
        if export_results_to_excel(df_results, str(output_path)):
            st.success("✓ Resultados exportados com sucesso")
            
            # Download button
            with open(output_path, 'rb') as f:
                st.download_button(
                    label="📥 Baixar resultados (.xlsx)",
                    data=f.read(),
                    file_name=output_path.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
            # Show results preview
            st.subheader("Preview de resultados")
            st.dataframe(df_results.head(20), use_container_width=True)
        else:
            st.error("❌ Erro ao exportar resultados")

# Footer
st.divider()
st.caption("""
💡 **Dica**: Este app suporta até 10 características por produto.  
⚠️ **Avisos não impedem o processamento** - o app sempre tenta processar sua planilha.  
🔧 **Funcionalidade**: Fase 1 - MVP com estrutura fixa.
""")
