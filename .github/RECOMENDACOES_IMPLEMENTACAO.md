# 📋 RECOMENDAÇÕES DE IMPLEMENTAÇÃO - Web Scraping Project

**Data**: 28 de Maio de 2026  
**Status**: Pronto para Implementação Fase 1

---

## 🎯 Resumo Executivo

Baseado na análise completa do projeto, segue as recomendações para avançar com a SPEC.

---

## 1️⃣ O QUE É "VARIAÇÕES" DE MAPEAMENTO?

### Definição
**Variações** são diferentes estruturas que usuários podem trazer em suas planilhas, mesmo tendo o mesmo conteúdo.

### Exemplos Práticos

```
VARIAÇÃO 1 (Padrão esperado):
| Produto  | Descrição 1 | Descrição 2 |
| Luva     | correr      | 20mm        |

VARIAÇÃO 2 (Colunas renomeadas):
| Item     | Caracter_1  | Caracter_2  |
| Luva     | correr      | 20mm        |

VARIAÇÃO 3 (Ordem diferente):
| Descrição 1 | Descrição 2 | Produto |
| correr      | 20mm        | Luva    |

VARIAÇÃO 4 (Menos dados):
| Produto | Especificação |
| Luva    | correr 20mm   |

VARIAÇÃO 5 (Mais colunas):
| Produto | Desc1 | Desc2 | Marca | Fornecedor |
| Luva    | correr| 20mm  | XYZ   | Empresa    |
```

### Como a App Lida
1. **Detecção automática**: Lê primeira linha e detecta padrão
2. **Dropdowns de confirmação**: Usuário valida mapeamento (ex: "Esta coluna é o Produto? SIM/NÃO")
3. **Flexibilidade**: App acessa dados pela coluna lógica, não pela posição
4. **Colunas extras**: Simplesmente ignoradas se não forem mapeadas

---

## 2️⃣ MAPEAMENTO COM CÉLULAS VAZIAS (SUA MODIFICAÇÃO)

### Antes (Sem Inteligência)
```
INPUT:
| Produto | Desc1   | Desc2  | Desc3 | Desc4 |
| Luva    | correr  | 20mm   |       |       |

Query gerada: "Luva correr 20mm  " ← espaços extras, feo
```

### Depois (Com Inteligência - SUA SUGESTÃO ✅)
```
INPUT:
| Produto | Desc1   | Desc2  | Desc3 | Desc4 |
| Luva    | correr  | 20mm   |       |       |

PROCESSAMENTO INTELIGENTE:
1. Itera: Produto → "Luva" ✓
2. Itera: Desc1 → "correr" ✓ (não vazio)
3. Itera: Desc2 → "20mm" ✓ (não vazio)
4. Itera: Desc3 → "" ✗ PULA (vazio)
5. Itera: Desc4 → "" ✗ PULA (vazio)

Query gerada: "Luva correr 20mm" ← limpo, sem espaços extras ✓
```

### Implementação
No módulo `src/product_query_builder.py`:
```python
def build_queries(df_padronizado):
    queries = []
    for idx, row in df_padronizado.iterrows():
        # Coleta apenas valores não-vazios
        parts = [str(val).strip() for val in row if pd.notna(val) and str(val).strip()]
        query = " ".join(parts)
        queries.append(query)
    return queries

# Exemplo:
# Input: ["Luva", "correr", "20mm", NaN, NaN]
# Output: "Luva correr 20mm"
```

---

## 3️⃣ ANÁLISE DE ARQUIVOS - RECOMENDAÇÕES IMEDIATAS

### ✅ **MANTER** (9 arquivos em produção)
```
app.py                          → Interface Streamlit (necessário)
motor_busca.py                  → Backup/referência (conforme README)
runner.py                       → Orquestrador Scrapy (ativo)
amazon_spider.py                → Spider Amazon (ativo)
amazon_com_br_page.py           → Page Object Amazon (ativo)
items.py                        → Dataclass de produtos (ativo)
pipelines.py                    → Export Excel (ativo)
settings.py                     → Config Scrapy (ativo)
page_object_config.json         → Config referência (ativo)
```

### 🗑️ **REMOVER IMEDIATAMENTE** (2 arquivos inutilizados)
```
valores_produtos/pages/google_com_page.py
  └─ Motivo: Page Object para Google sem nenhum spider que o use
  
valores_produtos/tools/create_page_object_cli.py
  └─ Motivo: Ferramenta de desenvolvimento, não automática
```

### 🗑️ **REMOVER** (Estrutura abandonada)
```
config.py (vazio, nunca importado)
src/logger.py (vazio)
src/input_handler.py (vazio)
src/output_handler.py (vazio)
src/scraper.py (vazio)
src/google_shopping_scraper.py (vazio)
src/mercado_livre_scraper.py (vazio)
src/product_query_builder.py (vazio)

┳ Esses serão RECRIADOS na nova implementação com código real ✓
```

### 🧹 **LIMPAR** (Dead code)
```
motor_busca.py
├─ Remover imports não usados:
│  ├─ from math import e
│  ├─ import requests
│  ├─ from bs4 import BeautifulSoup
│  ├─ import zipfile
│  └─ from xml.sax.saxutils import escape
│
└─ Remover funções não usadas:
   ├─ buscar_produto()
   ├─ texto_primeiro()
   ├─ href_primeiro()
   ├─ imagem_primeira()
   ├─ extrair_produtos()
   └─ imprimir_conteudo_site()
```

### 📋 **Recomendação Final**
**Antes de iniciar Fase 1**, limpe o projeto:
```bash
# Passos
1. Remover: google_com_page.py e create_page_object_cli.py
2. Remover: todos os arquivos src/ vazios + config.py vazio
3. Limpar: motor_busca.py (remover imports/funções não usadas)
4. Estrutura final limpa pronta para nova implementação
```

---

## 4️⃣ PLANO DE IMPLEMENTAÇÃO - PRIORIDADES GRATUITAS

### Resumo das Alterações Feitas no SPEC

| Seção | Alteração | Benefício |
|-------|-----------|-----------|
| **1.1** | Detalhado Google Shopping (scraping leve GRATUITO) + alternativas pagas documentadas | Clareza: tenta grátis 1º, pago se necessário |
| **1.2** | Adicionado "APENAS células NÃO VAZIAS" na concatenação | Queries mais limpas, sem espaços extras |
| **1.3** | Expandido "Mapeamento Flexível" com 5 variações de exemplo | Usuário entende que app funciona com estruturas diferentes |
| **2** | Reorganizado: Caminho A (GRATUITO) vs Caminho B (PAGO) | Prioridade clara: livre antes de pago |
| **3** | Adicionado ações de limpeza imediata no projeto | Projeto fica pronto antes de nova implementação |
| **Fase 3** | Reorganizado em 3 opções: A (recomendado GRATUITO), B (pago), C (legacy) | Estratégia clara com fallbacks |
| **5.3** | Detalhado como `product_query_builder` remove células vazias | Implementador sabe exatamente o que fazer |
| **5.4, 5.5, 5.6** | Adicionado detalhes de retry, backoff, tratamento de bloqueios | Robusto contra falhas de rede |
| **5.5** | Google Shopping: scraping leve + investigação pré-implementação | Testa grátis 1º, documentado para pago |
| **5.6** | Mercado Livre: CONFIRMADO GRATUITO, API pública | Sem surpresas, funciona 100% free |
| **7** | Reorganizado como "Investigações Necessárias" + alternativas | Tudo documentado para decisões futuras |

---

## 5️⃣ ESTRATÉGIA GRATUITO vs PAGO

### Google Shopping (Desafio)
```
┌─────────────────────────────────────────────────┐
│ PRIORIDADE 1: Scraping Leve (GRATUITO) ✓       │
├─────────────────────────────────────────────────┤
│ Usar: Playwright + headers realistas            │
│ Teste: Quantas req/min antes de 429?            │
│ Risk: Alto (provavelmente será bloqueado)       │
│ Implementação: src/google_shopping_scraper.py   │
└─────────────────────────────────────────────────┘
         ↓ (Se falhar)
┌─────────────────────────────────────────────────┐
│ PRIORIDADE 2: SerpAPI (PAGO) ⚠️                │
├─────────────────────────────────────────────────┤
│ Usar: SerpAPI Google Search (~$0.001/req)       │
│ Free Tier: 100 requisições/mês (teste)          │
│ Chave: .env + settings                          │
│ Implementação: Ativa se Prioridade 1 falhar     │
└─────────────────────────────────────────────────┘
```

### Mercado Livre (Fácil)
```
┌─────────────────────────────────────────────────┐
│ CONFIRMADO: API Pública (GRATUITO) ✅           │
├─────────────────────────────────────────────────┤
│ URL: https://api.mercadolibre.com/sites/MLB/... │
│ Auth: Nenhuma necessária (sem API key)          │
│ Rate Limit: ~60 req/min (INVESTIGAR)            │
│ Implementação: src/mercado_livre_scraper.py     │
│ Status: Fallback padrão (sempre funciona)       │
└─────────────────────────────────────────────────┘
```

### Proxy (Se Necessário)
```
┌─────────────────────────────────────────────────┐
│ PRIORIDADE 1: Bright Data Freemium (GRATUITO)  │
├─────────────────────────────────────────────────┤
│ Limite: 100GB/mês gratuito                       │
│ Uso: Rotate User-Agent + delay                  │
└─────────────────────────────────────────────────┘
         ↓ (Se necessário mais)
┌─────────────────────────────────────────────────┐
│ PRIORIDADE 2: Pago ($$$$)                       │
├─────────────────────────────────────────────────┤
│ Bright Data: ~$100/mês                          │
│ ScrapingBee: ~$29/mês                           │
│ Alternativas premium                             │
└─────────────────────────────────────────────────┘
```

---

## 6️⃣ ROADMAP RECOMENDADO

### 🔴 ANTES DE FASE 1
```
[ ] Limpar projeto (remover arquivos inutilizados)
[ ] Conferir com você: principais dúvidas resolvidas?
[ ] Aprovar estratégia gratuito/pago
```

### 🟡 FASE 1 (2-3 horas)
```
[✓] requirements.txt limpo
[✓] src/logger.py com logging estruturado
[✓] config.py com constantes (delays, timeouts, etc)
[✓] app.py refatorado (sem limites manuais)
```

### 🟠 FASE 2 (2-3 horas)
```
[✓] src/input_handler.py (validação + detecção de colunas)
[✓] src/product_query_builder.py (INTELIGENTE com células vazias)
[✓] src/output_handler.py (consolidação de resultados)
[✓] templates/template_entrada.xlsx (exemplo download)
```

### 🟡 FASE 3 (4-6 horas) ← **CRÍTICA**
```
[✓] src/google_shopping_scraper.py (scraping leve GRATUITO)
    └─ INVESTIGAÇÃO: Rate limits reais?
    └─ ALTERNATIVA: SerpAPI se grátis não funcionar
    
[✓] src/mercado_livre_scraper.py (API pública GRATUITO ✅)
    └─ INVESTIGAÇÃO: Confirmar rate limits
    
[✓] src/scraper.py (orquestrador com fallback)
    └─ Lógica: Google → bloqueado? → Mercado Livre
```

### 🟢 FASE 4-6 (6-8 horas)
```
[✓] Tratamento de bloqueios (retry, backoff)
[✓] Testes E2E
[✓] Deploy
```

---

## 7️⃣ PRÓXIMAS AÇÕES

1. **Confirme com você**:
   - [ ] Entendeu "variações" de mapeamento?
   - [ ] Concorda com limpeza de arquivos?
   - [ ] Aprova estratégia gratuito (Google scraping) → pago (SerpAPI)?

2. **Vou preparar**:
   - Limpeza do projeto (remover arquivos desnecessários)
   - Script de investigação para testar Google Shopping scraping
   - Fase 1 pronta para começar

3. **Você avisa quando**:
   - Tiver testado scraping de Google Shopping
   - Quiser começar Fase 1
   - Tiver dúvidas sobre qualquer módulo

---

## 📞 Dúvidas Frequentes

**P: Por que priorizar gratuito se não funcionar?**  
R: Economiza cliente. Se gratuito falhar, temos SerpAPI documentado e pronto para implementação rápida.

**P: E se Google Shopping bloquedar muito rápido?**  
R: Mercado Livre funciona como fallback automático. Cliente sempre tem resultados.

**P: Quanto vai custar SerpAPI se precisar usar?**  
R: ~$0.001/req (1 real por 1000). Teste com 100/mês free tier 1º.

**P: As células vazias podem quebrar algo?**  
R: Não! A inteligência remove vazios antes de buscar. Queries sempre limpas.

---

**Documento SPEC atualizado com sucesso! 🎉**  
Pronto para começar quando quiser.
