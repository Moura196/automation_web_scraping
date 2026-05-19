import os
import sys
import time
import shutil
import logging
from datetime import datetime
import pandas as pd
import subprocess

logging.basicConfig(level=logging.INFO)


def _read_input(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def process_file(input_path, query_column, rows=None, output_dir=None, timeout=300):
    """Processa o arquivo de entrada, executa o spider para cada termo e consolida em .xlsx

    - input_path: path para o arquivo enviado
    - query_column: nome da coluna com termos de busca
    - rows: opcional DataFrame (subconjunto) para processar
    - output_dir: onde salvar resultados (padrão valores_produtos/output)
    """
    root = os.getcwd()
    project_dir = os.path.join(root, "valores_produtos")
    if output_dir is None:
        output_dir = os.path.join(project_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    if rows is None:
        df = _read_input(input_path)
    else:
        df = rows

    if query_column not in df.columns:
        raise ValueError(f"Coluna '{query_column}' não encontrada no arquivo de entrada")

    queries = df[query_column].dropna().astype(str).tolist()
    if len(queries) == 0:
        raise ValueError("Nenhuma query encontrada na coluna selecionada")

    temp_results = []
    for idx, q in enumerate(queries):
        logging.info(f"[{idx+1}/{len(queries)}] Executando query: {q}")
        cmd = [sys.executable, "-m", "scrapy", "crawl", "amazon_search", "-a", f"query={q}"]
        try:
            subprocess.run(cmd, cwd=project_dir, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            logging.warning(f"Query timed out: {q}")

        src = os.path.join(project_dir, "output", "amazon_search_products.csv")
        if os.path.exists(src):
            dest = os.path.join(output_dir, f"result_{idx+1}.csv")
            try:
                # overwrite if exists
                if os.path.exists(dest):
                    os.remove(dest)
                shutil.move(src, dest)
                temp_results.append((dest, q))
            except Exception as e:
                logging.exception("Falha ao mover CSV de saída")
        else:
            logging.info("Nenhum CSV gerado para esta query (provavelmente bloqueado ou nenhum resultado)")

        # pequeno delay para reduzir pressão
        time.sleep(1.0)

    if len(temp_results) == 0:
        raise RuntimeError("Nenhum resultado foi gerado para as queries fornecidas")

    # Escrever workbook com uma aba por produto e uma aba combinada
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_xlsx = os.path.join(output_dir, f"results_{timestamp}.xlsx")

    def _sanitize_sheet_name(name: str, idx: int) -> str:
        # Excel sheet name limits: max 31 chars, cannot contain :\\/?*[]
        illegal = r"\\/:?*[]"
        s = str(name)
        for ch in illegal:
            s = s.replace(ch, "-")
        s = s.strip()
        if len(s) == 0:
            s = f"sheet_{idx+1}"
        if len(s) > 30:
            s = s[:30]
        # ensure uniqueness by appending index if necessary
        return f"{s}_{idx+1}" if len(s) <= 30 else f"{s[:26]}_{idx+1}"

    dfs_for_combined = []
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
        for i, (csv_path, q) in enumerate(temp_results):
            try:
                dfi = pd.read_csv(csv_path)
            except Exception:
                logging.exception(f"Falha ao ler {csv_path}")
                continue
            sheet_name = _sanitize_sheet_name(q, i)
            # Write sheet for this query
            try:
                dfi.to_excel(writer, sheet_name=sheet_name, index=False)
            except Exception:
                logging.exception(f"Falha ao escrever sheet '{sheet_name}'")
            dfs_for_combined.append(dfi)

        # combined sheet
        try:
            combined = pd.concat(dfs_for_combined, ignore_index=True)
            combined.to_excel(writer, sheet_name="combined", index=False)
        except Exception:
            logging.exception("Falha ao escrever sheet combined")

    logging.info(f"Resultados escritos em: {out_xlsx}")
    return out_xlsx
