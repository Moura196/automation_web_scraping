# SPEC: Aplicação de Web Scraping com Streamlit

**Versão**: 1.0  
**Data**: 2026-05-26  
**Status**: Planejamento - Pronto para Implementação

---

## TL;DR

Refatorar e melhorar a aplicação Streamlit atual para:
1. **Buscar produtos com características** (não apenas nome) combinando coluna "Produto" + "Descrição 1-5"
2. **Processar todas as linhas automaticamente** (remover seleção manual de limite)
3. **Implementar fallback de plataformas**: Google Shopping → Mercado Livre (se bloqueado)
4. **Adicionar logging estruturado** para monitoramento em tempo real
5. **Padronizar entrada com mapeamento flexível**: usuário mapeia colunas via UI, mas app processa automaticamente
6. **Usar bibliotecas leves** com foco em APIs oficiais para evitar bloqueios

---

## 1. Decisões de Arquitetura

### 1.1 Estratégia de Web Scraping
- **Primária**: Google Shopping (maior cobertura, melhor UX)
- **Fallback**: Mercado Livre (se Google Shopping bloqueado)
- **Método**: APIs oficiais com rate limiting (prioridade sobre scrapy direto - Priorizar estratégias gratúitas antes de considerar soluções pagas.)
  - Google Shopping API (se disponível) ou Custom Search API
  - Mercado Livre tem API pública com documentação
- **Evitar bloqueios**: Usar headers realistas, delays entre requisições, múltiplos IPs se necessário (proxy gratuito). Priorizar estratégias gratúitas antes de considerar soluções pagas.

### 1.2 Fluxo de Processamento
```
Upload .xlsx
    ↓
Mapeamento de colunas (UI flexível)
    ↓
Leitura: Produto + Descrições 1-5 + outras colunas
    ↓
Para cada linha:
  - Concatenar: "Produto + Descrição1 + Descrição2 + ... (se existir)"
  - Realizar busca na plataforma primária
  - Se bloqueado → tentar fallback
  - Registrar em log detalhado
    ↓
Consolidar resultados em .xlsx único com uma aba para cada produto 
```

### 1.3 Formato de Planilha (Entrada)
**Obrigatório**:
- `Produto` (coluna A) — Nome do produto
- `Descrição 1` a `Descrição 5` ou mais (colunas B-F...) — Características opcionais

**Opcional**:
- Qualquer outra coluna será ignorada (ou mapeável)

**Exemplo esperado** (usuário recebe template):
| Produto | Descrição 1 | Descrição 2 | Descrição 3 | Descrição 4 | Descrição 5 |...
|---------|-------------|-------------|-------------|-------------|-------------|...
| Luva | correr | 20mm | pvc | | |...
| Açúcar | cristal | branco | 1kg | | |...
| Barhante | 85% | algodão | 4/6 | fios | 600g |...

### 1.4 Formato de Planilha (Saída)
**Colunas obrigatórias**:
1. `Descrição Completa` — "Luva correr 20mm pvc" (concatenação de entrada)
2. `Valor (R$)` — Numérico, tratado para float
3. `Link` — URL do produto encontrado
4. `Plataforma` — "Google Shopping" ou "Mercado Livre" (rastreabilidade)
5. `Data da Busca` — (timestamp)

**Colunas opcionais** (futuro):
- `Disponibilidade` (sim/não/verificar)

### 1.5 Logging Estruturado
**Nível**: Detalhado (cada produto, bloqueios, tentativas)  
**Formato**: JSON estruturado
**Canais**:
1. **Console** (Streamlit: `st.success()`, `st.warning()`, `st.error()`)
2. **Arquivo**: `logs/app.log` (persistente, para análise pós-execução)
3. **Estrutura mínima**:
   ```
   [TIMESTAMP] [LEVEL] [PROCESSO] Mensagem
   
   Exemplos:
   [2026-05-26 14:30:15] [INFO] [BUSCA] Produto 1/50: "Luva correr 20mm pvc"
   [2026-05-26 14:30:20] [WARNING] [GOOGLE_SHOPPING] Bloqueado (429). Tentando Mercado Livre...
   [2026-05-26 14:30:25] [SUCCESS] [MERCADO_LIVRE] Encontrado: R$ 25.90
   [2026-05-26 14:30:30] [ERROR] [MERCADO_LIVRE] Erro de conexão. Pulando este produto.
   ```

---

## 2. Bibliotecas Recomendadas (Mínimas)

**Obrigatórias**:
- `streamlit` — Frontend/UI
- `pandas` — Leitura/escrita .xlsx
- `openpyxl` — Suporte para Excel
- `requests` — HTTP requests com retry/timeout

**Para Web Scraping** (escolher 1 caminho):
- **Caminho A (Recomendado - APIs)**: `google-api-client`, `mercado-libre-sdk` (se existe)
- **Caminho B (Scraping)**: `scrapy` (manter) + `scrapy-playwright` OU `beautifulsoup4`

**Auxiliares**:
- `logging` (built-in) — Logs estruturados
- `python-dotenv` — Variáveis de ambiente (API keys)

**NÃO recomendadas** (remover):
- `scrapy_zyte_api` (custo, exposição de chave)
- `scrapy_poet` (complexidade desnecessária)

---

## 3. Estrutura de Arquivos (Nova)

```
Web Scraping Project/
├── app.py                          # Streamlit UI (refatorado)
├── config.py                       # Configurações globais
├── requirements.txt                # Dependências (limpas)
├── .env.example                    # Template para variáveis (API keys)
├── .gitignore                      # Incluir .env, logs/
│
├── src/
│   ├── __init__.py
│   ├── input_handler.py            # Leitura e validação de .xlsx entrada
│   ├── product_query_builder.py    # Concatena "Produto + Descrições"
│   ├── scraper.py                  # Orquestra diferentes plataformas
│   ├── google_shopping_scraper.py  # Módulo Google Shopping
│   ├── mercado_livre_scraper.py    # Módulo Mercado Livre (fallback)
│   ├── output_handler.py           # Gera .xlsx de saída
│   ├── logger.py                   # Logging centralizado
│   └── utils.py                    # Funções auxiliares (retry, delays, etc)
│
├── logs/
│   └── app.log                     # Arquivo de log persistente
│
├── templates/
│   └── template_entrada.xlsx       # Arquivo exemplo para download
│
└── valores_produtos/               # [Opcional] Manter para compat. Scrapy (refatorar depois)
    └── settings.py                 # Remover chave Zyte, limpar imports
```

---

## 4. Fluxo de Implementação (Fases)

### **Fase 1: Setup e Refatoração Básica** [~2-3 horas]
1. Criar `requirements.txt` limpo (remover Zyte, scrapy_poet)
2. Criar `src/logger.py` — Logging estruturado (console + arquivo)
3. Criar `config.py` com constantes (timeouts, delays, mensagens)
4. Refatorar `app.py`:
   - Remover seleção de coluna e limite de linhas
   - Remover UI de "Executar busca" simples (apenas botão final)
   - Adicionar mapeamento flexível de colunas (dropdown por coluna detectada)

### **Fase 2: Input/Output Handling** [~2-3 horas]
1. Criar `src/input_handler.py`:
   - Validar .xlsx (colunas esperadas)
   - Permitir mapeamento de colunas (se houver variações)
   - Converter para DataFrame padrão
2. Criar `src/product_query_builder.py`:
   - Concatenar Produto + Descrições (com espaços entre)
   - Retornar lista de queries
3. Criar `src/output_handler.py`:
   - Consolidar resultados de múltiplos spiders/scrapers
   - Gerar .xlsx com colunas padrão (Descrição Completa, Valor, Link, Plataforma)
4. Criar template `templates/template_entrada.xlsx`

### **Fase 3: Web Scraping** [~4-6 horas — maior esforço]
**Opção A (Recomendada - APIs)**:
1. Investigar Google Shopping API / Custom Search API (pode ser pago -> priorizar alternativas gratuitas)
2. Se não viável → usar SerpAPI ou Similar Web API (freemium)
3. Criar `src/google_shopping_scraper.py`
4. Criar `src/mercado_livre_scraper.py` (usar API pública)
5. Criar `src/scraper.py` (orquestrador com fallback)

**Opção B (Mantendo Scrapy)**:
1. Refatorar `valores_produtos/settings.py` (remover Zyte)
2. Atualizar `amazon_spider.py` para Playwright + rate limiting
3. Criar novo spider para Mercado Livre
4. Wrapper em `src/scraper.py` que chama spiders via subprocess

### **Fase 4: Tratamento de Bloqueios e Erros** [~2-3 horas]
1. Implementar retry logic com backoff exponencial
2. Implementar proxy rotation (alternativa: Bright Data freemium)
3. Adicionar delay aleatório entre requisições
4. Capturar 429 (throttled), 403 (forbidden), timeout → log + fallback

### **Fase 5: Integração e Testes** [~2 horas]
1. Integrar tudo no `app.py`
2. Testar com planilha exemplo (luva, açúcar, barhante)
3. Validar saída .xlsx
4. Testar logs (console + arquivo)
5. Tratamento de edge cases (coluna vazia, produto não encontrado, etc)

### **Fase 6: Deploy e Documentação** [~1-2 horas]
1. Criar `README.md` atualizado
2. Criar `.env.example`
3. Adicionar instruções de uso (como preencher planilha, como rodar localmente)
4. Deploy no Streamlit Cloud (configurar secrets para API keys)

---

## 5. Detalhamento Técnico por Módulo

### 5.1 `src/logger.py`
```python
# Funções principais:
- setup_logger(name, log_file, level=INFO)
- log_search_start(product_num, total, query)
- log_search_success(platform, value, link)
- log_search_blocked(platform, error_code)
- log_search_failed(product_num, reason)
```

### 5.2 `src/input_handler.py`
```python
# Funções principais:
- validate_excel(file_path) -> bool
- detect_columns(df) -> dict { 'produto': col_name, 'descricoes': [col_names] }
- map_columns_ui(df) -> dict (permite user override)
- standardize_dataframe(df, column_map) -> df_padronizado
```

### 5.3 `src/product_query_builder.py`
```python
# Funções principais:
- build_queries(df_padronizado) -> List[str]
  # Exemplo: ["Luva correr 20mm pvc", "Açúcar cristal branco 1kg", ...]
```

### 5.4 `src/scraper.py` (Orquestrador Principal)
```python
# Funções principais:
- search_product(query: str, platform: str = "google_shopping") -> {
    "titulo": str,
    "preco": float,
    "link": str,
    "plataforma": str,
    "encontrado": bool
  }
- search_with_fallback(query: str) -> same_dict
  # Tenta Google Shopping, se bloqueado tenta Mercado Livre
```

### 5.5 `src/google_shopping_scraper.py`
```python
# Usar API ou scraping leve:
- search_google_shopping(query: str, max_results: int = 5) -> List[produto]
# Tratamento de 429/403 → levanta exception customizada
```

### 5.6 `src/mercado_livre_scraper.py`
```python
# Usar API pública Mercado Livre:
- search_mercado_livre(query: str, max_results: int = 5) -> List[produto]
```

### 5.7 `src/output_handler.py`
```python
# Funções principais:
- consolidate_results(query_results: List[dict], original_df: df) -> df_consolidado
- export_to_xlsx(df, output_path: str) -> str
# Gera arquivo com colunas: Descrição Completa | Valor | Link | Plataforma
```

### 5.8 `app.py` (Streamlit Refatorado)
```
Seções:
1. Upload de arquivo
2. Detecção e mapeamento de colunas (interativo)
3. Preview dos dados
4. Botão "Executar Busca"
5. Progress bar / Status em tempo real
6. Download resultado .xlsx
7. Visualização de logs em expandable
```

---

## 6. Tratamento de Erros e Bloqueios

### 6.1 Estratégia de Retry
```
Tentativa 1: Google Shopping (sem proxy)
  ├─ Sucesso → Retornar resultado
  ├─ 429/403 → Aguardar 5s, tentar novamente (max 2x)
  ├─ Timeout → Aguardar 3s, tentar novamente
  └─ Persistente → Log warning + ir para fallback

Fallback: Mercado Livre (sempre tem API pública)
  ├─ Sucesso → Retornar resultado
  └─ Erro → Log error, marcar produto como "não encontrado"
```

### 6.2 Rate Limiting
- Delay mínimo entre requisições: 0.5-2s (configurável)
- Aumentar delay se receber 429
- Usar headers realistas (User-Agent rotativo)

---

## 7. Verificação e Testes

**Antes de implementação**:
- [ ] Confirmar se Google Shopping API é acessível/gratuita (investigação)
- [ ] Confirmar API Mercado Livre para Brasil
- [ ] Testar rates limits reais (quantas requisições/min são permitidas?)
- [ ] Definir alternativa se Google Shopping não for viável

**Durante implementação**:
- [ ] Teste unitário: `test_product_query_builder.py`
- [ ] Teste unitário: `test_input_handler.py`
- [ ] Teste E2E: Upload planilha exemplo → Download resultado
- [ ] Validação de saída: Colunas corretas, dados esperados
- [ ] Validação de logs: Arquivo criado, mensagens corretas

**Pós-implementação**:
- [ ] Teste com múltiplas linhas (10+, 50+, 100+)
- [ ] Teste de timeout (simular bloqueio, verificar fallback)
- [ ] Teste de planilha mal formatada (log claro, sem crash)

---

## 8. Decisions & Scope

### ✅ **Incluído**
- Busca com características (Produto + Descrições)
- Processamento automático de todas as linhas
- Logging detalhado estruturado
- Fallback de plataforma (Google Shopping → Mercado Livre)
- Mapeamento flexível de colunas
- Arquivo .xlsx de saída com informações requeridas
- Template de planilha de entrada

### ❌ **Explicitamente Excluído**
- Dashboard de análise histórica (fora de escopo atual)
- Autenticação/login (aplicação simples)
- Suporte a múltiplos usuários/sessões persistentes
- Cache de resultados (cada execução é nova)
- Scraping de preços históricos (apenas consulta atual)
- Integração com APIs de e-commerce paga (Zyte, etc) — usar APIs públicas

### ⚠️ **Pendente de Investigação**
- Viabilidade técnica de Google Shopping (API pública vs. scraping)
- Custos de APIs alternativas (SerpAPI, etc)
- Rate limits reais de Mercado Livre
- Estratégia de proxy se necessário

---

## 9. Próximos Passos

1. **Investigação**: Validar APIs disponíveis (Google Shopping vs. SerpAPI vs. scraping direto)
2. **Confirmação**: Aprovar decisões sobre plataformas e bibliotecas
3. **Implementação**: Começar pela Fase 1 (Setup) → iterativo até Fase 6

---

## Notas Adicionais

- **Chave Zyte exposta**: Remover imediatamente do settings.py (usar .env)
- **Compatibilidade**: Manter estrutura Scrapy se decidir usar, mas simplificar
- **Performance**: Com rates adequados, ~10-50 produtos/min é realista
- **Escalabilidade futura**: Arquitetura desacoplada permite adicionar mais plataformas
