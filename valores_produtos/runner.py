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

    temp_csvs = []
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
                temp_csvs.append(dest)
            except Exception as e:
                logging.exception("Falha ao mover CSV de saída")
        else:
            logging.info("Nenhum CSV gerado para esta query (provavelmente bloqueado ou nenhum resultado)")

        # pequeno delay para reduzir pressão
        time.sleep(1.0)

    if len(temp_csvs) == 0:
        raise RuntimeError("Nenhum resultado foi gerado para as queries fornecidas")

    # consolidar CSVs
    dfs = []
    for p in temp_csvs:
        try:
            dfs.append(pd.read_csv(p))
        except Exception:
            logging.exception(f"Falha ao ler {p}")

    combined = pd.concat(dfs, ignore_index=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_xlsx = os.path.join(output_dir, f"results_{timestamp}.xlsx")
    combined.to_excel(out_xlsx, index=False)
    logging.info(f"Resultados consolidados em: {out_xlsx}")
    return out_xlsx
