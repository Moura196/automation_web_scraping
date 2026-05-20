# Projeto: Busca de Produtos (Scrapy + Playwright + Pandas)

Este repositório contém um protótipo de aplicação para pesquisar produtos (ex.: Amazon), extrair informações e gerar um relatório em Excel. A aplicação combina:

- Scrapy (spiders e pipelines)
- scrapy-playwright (navegação com Playwright para páginas dinâmicas)
- web-poet / page objects para extração estruturada
- Pandas para consolidação e exportação a Excel
- Streamlit para uma interface local simples (upload → execução → download)

Este README descreve como configurar, rodar e usar a aplicação localmente.

## Estrutura relevante

- `motor_busca.py` — protótipo Playwright (mantenha como referência/back-up). Não é necessário para o fluxo Scrapy.
- `app.py` — interface Streamlit (upload do Excel/CSV → executa buscas → permite download do `.xlsx`).
- `valores_produtos/` — Scrapy project (spiders, pages, pipelines, fixtures).
	- `valores_produtos/valores_produtos/spiders/amazon_spider.py` — spider principal que usa `meta:{"playwright": True}`
	- `valores_produtos/valores_produtos/pages/amazon_com_br_page.py` — page object para extração
	- `valores_produtos/valores_produtos/pipelines.py` — `PandasExportPipeline` que produz CSVs
	- `valores_produtos/runner.py` — orquestrador que executa o spider para cada termo e consolida resultados em `.xlsx`
- `requirements.txt` — dependências do projeto

## Requisitos

- Python 3.10+ (venv recomendado)
- Windows / macOS / Linux (instruções abaixo usam Windows PowerShell e caminhos relativos ao repositório)

## Instalação (local, em uma máquina do cliente)

1. Clone o repositório.
2. Crie e ative um ambiente virtual (recomendado):

```powershell
python -m venv .venv
& .venv\Scripts\Activate.ps1
```

3. Instale dependências:

```powershell
pip install -r requirements.txt
```

4. Instale os navegadores do Playwright (necessário apenas uma vez):

```powershell
python -m playwright install
```

Observação: `playwright install` baixa os binários do Chromium/Firefox/WebKit. Sem isso, as requests com `meta={"playwright": True}` falharão.

## Uso — protótipo Streamlit (recomendado)

1. Ative o `.venv` (se não estiver ativo):

```powershell
& .venv\Scripts\Activate.ps1
```

2. Rode a interface Streamlit:

```powershell
streamlit run app.py
```

3. Na interface web que abrirá (normalmente http://localhost:8501):
- Faça upload do seu arquivo `.xlsx` ou `.csv` contendo a lista de produtos.
- Selecione a coluna que contém o termo de busca (ex.: `produto`, `query`).
- Opcional: limite o número de linhas para teste.
- Clique `Executar busca`.

4. Após o processamento, será oferecido um botão para baixar o arquivo `.xlsx` consolidado.

Comportamento do runner:
- Para cada termo do arquivo enviado o runner invoca `scrapy crawl amazon_search -a query="<termo>"` dentro do projeto `valores_produtos/`.
- O `PandasExportPipeline` grava um CSV por execução em `valores_produtos/output/` chamado `amazon_search_products.csv`.
- O `runner.py` renomeia cada CSV por query e ao final gera um `.xlsx` com uma planilha por produto e uma planilha `combined`.

<!-- ## Executar o spider manualmente

Se preferir executar o spider sem usar o Streamlit:

```powershell
& .venv\Scripts\Activate.ps1
cd valores_produtos
& ..\.venv\Scripts\python.exe -m scrapy crawl amazon_search -a query="cadeira"
```

Os resultados serão salvos em `valores_produtos/output/amazon_search_products.csv` pelo pipeline. -->

## Saída esperada

- A pasta `valores_produtos/output/` conterá os CSVs gerados por cada execução e o `.xlsx` consolidado criado pelo `runner`.
- O `.xlsx` tem uma aba por termo de busca (nome truncado/sanitizado) e uma aba `combined` com todos os resultados.

## Boas práticas e limitações

- Amazon e outros marketplaces aplicam mecanismos anti-scraping. Para reduzir bloqueios:
	- Use execução serial (o runner já roda uma query por vez).
	- Adicione delays e retries (podemos melhorar o runner para isso).
	- Se precisar de escala, considere proxies rotativos (serviços pagos).
- Playwright requer `python -m playwright install` para funcionar.
- A extração depende de seletores CSS; alterações na página alvo podem quebrar o parser.

## O que já está implementado

- Interface Streamlit (`app.py`) para upload e execução local.
- Runner (`valores_produtos/runner.py`) que chama o spider por query e consolida resultados em um `.xlsx` com abas por produto.
- Spider `amazon_search` integrado com `scrapy-playwright` e `web-poet` page object (`AmazonComBrPage`).

## Próximos passos recomendados

- Implementar retries e políticas de backoff no `runner` e no `PandasExportPipeline` (já iniciei logging básico).
- Validar e tornar `preco` numérico no `Produto` e padronizar formatos antes da exportação.
- Empacotar app com PyInstaller se o cliente não desejar usar terminal/venv.
- Escrever uma seção de troubleshooting e um guia de empacotamento (posso gerar se desejar).

## Contato / Suporte

Se desejar, eu posso:
- Gerar o guia de empacotamento com `PyInstaller`.
- Adicionar retries/backoff e proxies no runner.
- Melhorar a validação e os testes das page objects (usar fixtures existentes).

---
Arquivo de referência: `motor_busca.py` (prototipo Playwright). Não exclua — contém utilitários úteis para migrar seletores e lógica de interação.
