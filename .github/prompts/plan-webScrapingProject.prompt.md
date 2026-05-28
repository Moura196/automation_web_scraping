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
  - **INVESTIGAÇÃO NECESSÁRIA**: Confirmar viabilidade de API pública gratuita (Google Shopping API requer chave, pode ter custos)
  - **Opção gratuita recomendada**: Implementar scraping leve com Playwright + headers realistas (PRIMEIRA PRIORIDADE)
  - **Alternativa paga** (se scraping simples for bloqueado): SerpAPI, Bright Data, ou Google Custom Search API (manter documentado)
  
- **Fallback**: Mercado Livre (se Google Shopping bloqueado) ✅ **GRATUITO**
  - **Confirmado**: Mercado Livre possui API pública oficial com documentação
  - Rate limit: ~60 requisições/min (INVESTIGAR limites reais antes de implementar)
  
- **Método**: APIs públicas + scraping leve com rate limiting (PRIORIDADE: gratuito → pago)
  - Primária: Scraping com Playwright + headers realistas, delays 0.5-2s
  - Fallback: Mercado Livre API pública (CONFIRMADO GRATUITO)
  - Alternativa paga: SerpAPI, Bright Data, Google APIs pagas (manter como plano B)
  
- **Evitar bloqueios**: Usar headers realistas (User-Agent rotativo), delays entre requisições, proxy gratuito se necessário (Bright Data freemium ou Free Proxy List). **Priorizar estratégias gratuitas antes de considerar soluções pagas.**

### 1.2 Fluxo de Processamento
```
Upload .xlsx
    ↓
Mapeamento de colunas (UI flexível com detecção automática)
    ↓
Leitura: Produto + Descrições 1-5 + outras colunas
    ↓
Para cada linha:
  - Concatenar: "Produto + Descrição1 + Descrição2 + ... (APENAS células NÃO VAZIAS)"
    * Exemplo: Se Desc3 e Desc4 estão vazios → pula e vai para próxima
    * Resultado: "Luva correr 20mm" (sem espaços extras)
  - Realizar busca na plataforma primária
  - Se bloqueado → tentar fallback
  - Registrar em log detalhado
    ↓
Consolidar resultados em .xlsx único com uma aba para cada produto 
```

### 1.3 Formato de Planilha (Entrada) e Mapeamento Flexível
**Obrigatório**:
- `Produto` (coluna essencial) — Nome do produto
- `Descrição 1` a `Descrição 5` ou mais (colunas características opcionais, podem estar parcialmente vazias)

**Mapeamento Flexível**:
A app detecta automaticamente quais colunas contêm características. O usuário confirma via UI dropdowns caso queira alterar (ex: se as colunas tiverem nomes diferentes como "Item", "Especificação", "Características", etc).

**Processamento Inteligente de Células Vazias**:
- Células vazias são **AUTOMATICAMENTE IGNORADAS** na concatenação
- A app constrói a query com apenas os campos preenchidos
- Espaços extras são removidos

**Exemplo esperado** (usuário recebe template):
| Produto | Descrição 1 | Descrição 2 | Descrição 3 | Descrição 4 | Descrição 5 |
|---------|-------------|-------------|-------------|-------------|-------------|  
| Luva | correr | 20mm | pvc | | |
| Açúcar | cristal | branco | 1kg | | |
| Barhante | 85% | algodão | 4/6 | fios | 600g |

**Processamento Real**:
- Luva: "Luva correr 20mm pvc" (Desc4 e Desc5 vazios → ignorados)
- Açúcar: "Açúcar cristal branco 1kg" (Desc4 e Desc5 vazios → ignorados)  
- Barhante: "Barhante 85% algodão 4/6 fios 600g" (nenhum vazio → todos inclusos)

**Variações Aceitas** (usuario pode ter estrutura diferente):
- Colunas renomeadas: "Item" em vez de "Produto", "Característica" em vez de "Descrição 1"
- Ordem diferente: Descrições podem estar antes do Produto
- Menos colunas: App aceita se tiver apenas Produto + 1 descrição
- Mais colunas: Colunas extras são ignoradas

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

**Para Web Scraping** (PRIORIDADE: Gratuito primeiro):

**Caminho A (RECOMENDADO - Scraping Leve + API Gratuita)**:
- `playwright` ou `selenium` — Browser automation (gratuito)
- `beautifulsoup4` — Parse HTML (gratuito)
- `requests` — HTTP básico (já listado acima)
- Mercado Livre SDK (se existe e gratuita) OU requests para chamar API pública

**Caminho B (ALTERNATIVA - Se scraping simples for bloqueado)**:
- `serpapi` — Google Search API (⚠️ PAGO, ~$0.001/requisição, mas tem free tier 100/mês)
- `google-api-client` — Google Custom Search (⚠️ PAGO, ~$5/1000 requisições)
- Bright Data proxy (⚠️ PAGO, mas tem free tier 100GB/mês)

**Auxiliares**:
- `logging` (built-in) — Logs estruturados
- `python-dotenv` — Variáveis de ambiente (API keys)

**A REMOVER**:
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
│   ├── product_query_builder.py    # Concatena "Produto + Descrições" (inteligente com células vazias)
│   ├── scraper.py                  # Orquestra diferentes plataformas (com fallback)
│   ├── google_shopping_scraper.py  # Módulo Google Shopping (scraping leve OU API paga)
│   ├── mercado_livre_scraper.py    # Módulo Mercado Livre (API pública GRATUITA)
│   ├── output_handler.py           # Gera .xlsx de saída
│   ├── logger.py                   # Logging centralizado
│   └── utils.py                    # Funções auxiliares (retry, delays, proxy rotation, etc)
│
├── logs/
│   └── app.log                     # Arquivo de log persistente
│
├── templates/
│   └── template_entrada.xlsx       # Arquivo exemplo para download
│
└── valores_produtos/               # [REMOVER DEPOIS] Código antigo Scrapy (manter apenas runner.py se necessário)
    ├── runner.py                   # Pode ser refatorado para usar novos módulos src/
    ├── scrapy.cfg
    └── ... (remover spiders, pages, settings se migrado para src/)
```

**AÇÕES DE LIMPEZA IMEDIATA**:
- ❌ Remover: `google_com_page.py` (não tem spider)
- ❌ Remover: `create_page_object_cli.py` (ferramenta dev)
- ❌ Remover: Estrutura `src/` VAZIA anterior (será recriada nesta refatoração)
- ❌ Remover: `config.py` VAZIO (será recriado com valores)
- 🧹 Limpar: `motor_busca.py` (5 imports não usados + 6 funções não usadas)

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
**Prioridade: GRATUITO PRIMEIRO → Pago conforme necessidade**

**Opção A (RECOMENDADA 1ª LINHA - Scraping Leve + API Gratuita)** ✅ **PRIORITÁRIO**:
1. ✅ **Google Shopping**: Implementar scraping leve com Playwright + headers realistas
   - Rate limiting: 0.5-2s entre requisições
   - Headers com User-Agent rotativo
   - Retry logic com backoff exponencial (máx 3 tentativas)
   - **Investigação**: Testar rate limits reais; se bloqueado persistentemente → fallback
2. ✅ **Mercado Livre**: Usar API pública oficial (CONFIRMADO GRATUITO)
   - Documentação: https://developers.mercadolibre.com.br/pt_br/api-docs-pt-br
   - **Investigação**: Confirmar rate limits reais (~60 req/min?)
   - Sem necessidade de API key
3. Criar `src/google_shopping_scraper.py` (scraping leve)
4. Criar `src/mercado_livre_scraper.py` (API pública)
5. Criar `src/scraper.py` (orquestrador com fallback Google → Mercado Livre)

**Opção B (ALTERNATIVA - Se scraping simples for bloqueado)** ⚠️ **PAGO**:
- Use SerpAPI (Google Search): ~$0.001/req, free tier 100/mês
- Use Bright Data proxy: PAGO mas freemium 100GB/mês
- Use Google Custom Search API: ~$5/1000 reqs (CARO)
- **AÇÃO**: Documentar essas alternativas e deixar implementação pronta mas desativada

**Opção C (Legacy - Manter Scrapy se necessário)**:
1. Refatorar `valores_produtos/settings.py` (remover Zyte)
2. Atualizar `amazon_spider.py` para Playwright + rate limiting
3. Wrapper em `src/scraper.py` que chama spiders via subprocess
4. **RECOMENDAÇÃO**: Priorizar Opção A; usar Opção C apenas se Opção A não funcionar

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
  # Exemplo saída: ["Luva correr 20mm pvc", "Açúcar cristal branco 1kg", ...]

# INTELIGÊNCIA DE CÉLULAS VAZIAS:
# INPUT df:
#   Produto      | Desc1   | Desc2  | Desc3 | Desc4
#   Luva         | correr  | 20mm   | pvc   | 
#   Açúcar       | cristal | branco | 1kg   | 

# Função remove automaticamente células vazias:
- concat_with_empty_check(row) -> str
  * Itera Produto + Descrições
  * Inclui apenas células não vazias
  * Remove espaços extras
  * Retorna query limpa

# OUTPUT esperado:
# ["Luva correr 20mm pvc", "Açúcar cristal branco 1kg"]
```

### 5.4 `src/scraper.py` (Orquestrador Principal com Fallback)
```python
# Funções principais:

- search_product(query: str, platform: str = "google_shopping") -> {
    "titulo": str,
    "preco": float,
    "link": str,
    "plataforma": str,
    "encontrado": bool,
    "timestamp": str
  }
  
- search_with_fallback(query: str) -> same_dict
  # PRIORIDADE 1: Tenta Google Shopping (scraping leve GRATUITO)
  #   └─ Se sucesso → retorna resultado
  #   └─ Se erro 429/403 ou timeout → Log warning + próxima tentativa
  # 
  # PRIORIDADE 2: Se Google Shopping falha 3x → Tenta Mercado Livre (API GRATUITA)
  #   └─ Se sucesso → retorna resultado com plataforma="Mercado Livre"
  #   └─ Se erro → Log error + retorna {encontrado: false}
  #
  # TRATAMENTO DE BLOQUEIOS:
  # - 429/403 (bloqueado) → aguarda 5s, retry até 3x
  # - Timeout → aguarda 3s, retry até 2x
  # - Erro persistente → Log error + vai para próximo produto

# RETRY LOGIC:
- retry_with_backoff(func, max_attempts=3, initial_delay=1s) -> result
  * Backoff exponencial: 1s, 2s, 4s, 8s...
  * Captura exceções e tenta novamente
```

### 5.5 `src/google_shopping_scraper.py`
```python
# PRIORIDADE GRATUITA: Scraping leve com Playwright

- search_google_shopping(query: str, max_results: int = 5) -> List[produto]
  * Implementar com Playwright (headless browser)
  * Headers com User-Agent realista
  * Rate limit: delay 1-2s entre requisições
  * Retry logic: max 3 tentativas com backoff exponencial
  
# TRATAMENTO DE ERROS:
- Capturar 429 (Too Many Requests) → Log warning + throw BlockedException
- Capturar 403 (Forbidden) → Log warning + throw BlockedException
- Capturar timeout → Log warning + retry com delay maior
- Capturar CloudFlare 403 → Log warning + throw BlockedException

# INVESTIGAÇÃO PRÉ-IMPLEMENTAÇÃO:
- [ ] Testar quantas requisições/min são permitidas de um IP
- [ ] Testar se headers simples são suficientes ou se precisa de proxy
- [ ] Testar se Playwright consegue burlar proteções ou se será bloqueado rapidamente

# SE SCRAPING SIMPLES NÃO FUNCIONAR:
- Implementar Opção B (SerpAPI): google_shopping_scraper_serpapi.py
- Usar SerpAPI com API key (PAGO: ~$0.001/req, free tier 100/mês)
```

### 5.6 `src/mercado_livre_scraper.py`
```python
# ✅ CONFIRMADO GRATUITO: API Pública Mercado Livre

- search_mercado_livre(query: str, max_results: int = 5) -> List[produto]
  * Usar API oficial: https://api.mercadolibre.com/sites/MLB/search?q=QUERY
  * Sem necessidade de API key
  * Returns: JSON com produtos encontrados
  * Parse: titulo, preco, link da API response

# RATE LIMITING:
- Implementar delay 0.5-1s entre requisições
- Monitorar headers de resposta para rate limit

# TRATAMENTO DE ERROS:
- Capturar 429/503 (bloqueio temporário) → retry com backoff
- Capturar 404 (produto não encontrado) → retornar lista vazia
- Capturar timeout → retry

# INVESTIGAÇÃO PRÉ-IMPLEMENTAÇÃO:
- [ ] Confirmar rate limits reais (API docs indicam ~60 req/min?)
- [ ] Testar campos retornados pela API
- [ ] Testar parsing de preço (formato BRL, casas decimais)
- [ ] Testar parsing de link
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

**Antes de implementação** (INVESTIGAÇÃO NECESSÁRIA):
- [ ] **Google Shopping**: Testar se scraping leve com Playwright funciona sem bloqueios rápidos
  - Quantas requisições/min antes de 429?
  - Headers simples são suficientes ou precisa proxy?
  - Implementar Opção B (SerpAPI) se scraping falhar
- [ ] **Mercado Livre**: CONFIRMADO API Pública Gratuita
  - Confirmar rate limits reais (documentação diz ~60 req/min?)
  - Testar campos retornados e parsing
- [ ] **Proxy Gratuito**: Se necessário, testar alternativas gratuitas
  - Bright Data freemium (100GB/mês)
  - Free Proxy List (confiabilidade baixa)
  - Decidir se será necessário antes de Implementação

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

### ⚠️ **Pendente de Investigação** (Integrado nos módulos acima)

**Antes de Fase 3 iniciar:**

1. **Google Shopping** (Fase 3, Opção A)
   - Testar scraping leve: Playwright consegue burlar proteções?
   - Rate limits reais: quantas req/min antes de 429?
   - Alternativa paga: Se não funcionar → implementar SerpAPI (~$0.001/req)

2. **Mercado Livre** (Fase 3, Opção A - CONFIRMADO GRATUITO)
   - Confirmar rate limits reais da API (docs indicam ~60 req/min)
   - Testar parsing de campos: preço formato, link format, etc
   - Confirmar que não precisa de API key

3. **Proxy** (Fase 4, se necessário)
   - Se Google Shopping bloqueado rapidamente → avaliar proxy
   - Prioridade gratuita: Bright Data freemium, Free Proxy List
   - Alternativa paga: Bright Data full ($$$), ScrapingBee, etc

4. **Performance** (Fase 5)
   - Com rate limits: ~10-50 produtos/min é realista?
   - Testar com 50, 100, 500 linhas para medir tempo

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
