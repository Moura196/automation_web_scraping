""" - Sempre que um novo import incluido rodar: python -m pip install <nome do pacote>
    - Verificar a lista de dependências instaladas: pip list"""
from math import e

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import requests
from bs4 import BeautifulSoup

URL_GOOGLE_SHOPPING : str = "https://www.amazon.com.br/?tag=msndesktopsta-20&hvadid=&hvpos=&hvexid={aceid}&hvnetw=o&hvrand=&hvpone=&hvptwo=&hvqmt=e&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=167258&hvtargid=kwd-71331395852319:loc-20&ref=pd_sl_4g0yu04uek_e" #"https://www.google.com/shopping?hl=pt-BR&gl=br"

def iniciar_navegador(headless=True):
        p = sync_playwright().start()
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="pt-BR",
        )
        page = context.new_page()
        """ print("Navegador iniciado com sucesso.")
        print(p)
        print(browser)
        print(context)
        print(page) """
        return p, browser, context, page
    
def abrir_pagina(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)
    
def pagina_bloqueada(page):
    titulo = page.title().strip().lower()
    sinais = [
        "Atualize o navegador",
        "Atualize o navegador para continuar",
        "update your browser",
        "unusual traffic",
        "não sou um robô",
    ]
    return any(s in titulo for s in sinais)

def buscar_produto(page, termo):
    seletores_busca = [
        "input[name='field-keywords']",
        "input[name='q']",
        "textarea[name='q']",
        "input[aria-label='Pesquisar']",
        "textarea[aria-label='Pesquisar']",
    ] # TODO: verificar se existe um seletor mais específico para o google shopping

    caixa = None
    for sel in seletores_busca:
        loc = page.locator(sel)
        print(f"======>>> Tentando localizar caixa de busca com seletor: '{sel}' - Encontrados: {loc.count()}")
        if loc.count() > 0:
            caixa = loc.first
            break

    if caixa is None:
        raise RuntimeError("Não encontrei campo de busca na página.")

    caixa.click()
    caixa.fill(termo)
    caixa.press("Enter")

    # Espera curta por resultados
    page.wait_for_timeout(2500)
    print(f"======>>> A caixa de busca '{caixa}' foi encontrada.")
    # TODO: Foi encontrada, porém o google traz um reCAPTCHA. 
    # Preciso saber o que deve ser feito para não cair neste bloqueio ou 
    # conseguir sair dele.
    
def texto_primeiro(locator, timeout_ms=500):
    try:
        if locator.count() > 0:
            return locator.first.inner_text(timeout=timeout_ms).strip()
    except Exception:
        pass
    return ""

def href_primeiro(locator):
    try:
        if locator.count() > 0:
            return locator.first.get_attribute("href") or ""
    except Exception:
        pass
    return ""
    
def extrair_produtos(page, limite=10):
    seletores_cards = [
        "div.g-inner-card",
        "div[class_='a-section a-spacing-base desktop-grid-content-view']",
        "div.sh-dgr__grid-result",
        "div.pla-unit-container",
        "div.i0X6df",
        "div[data-docid]"
    ]

    cards = None
    for sel in seletores_cards:
        loc = page.locator(sel)
        if loc.count() > 0:
            cards = loc
            break

    if cards is None:
        return []

    total = min(cards.count(), limite)
    resultados = []

    for i in range(total):
        card = cards.nth(i)
        print(f"======>>> Card: {card}")

        nome = texto_primeiro(card.locator("h3, a, h4, [role='heading'], .tAxDx, .Xjkr3b"))
        preco = texto_primeiro(card.locator(".a8Pemb, .e10twf, span:has-text('R$')"))
        loja = texto_primeiro(card.locator(".aULzUe, .IuHnof, .E5ocAb"))
        link = href_primeiro(card.locator("a"))

        if nome: #or preco or loja:
            resultados.append({
                "nome": nome,
                #"preco": preco,
                #"loja": loja,
                #"link": link,
            })

    return resultados

def imprimir_conteudo_site(resultados):
    if not resultados:
        print("Nenhum produto encontrado.")
        return
    
    print(f"Produtos encontrados: {len(resultados)}")
    for i, item in enumerate(resultados, start=1):
        print("-" * 60)
        print(f"{i}. Nome : {item['nome'] or 'N/D'}")
        print(f"   Preço: {item['preco'] or 'N/D'}")
        print(f"   Loja : {item['loja'] or 'N/D'}")
        print(f"   Link : {item['link'] or 'N/D'}")
    
    """ response = requests.get(URL_GOOGLE_SHOPPING)
    response.raise_for_status()
    html = response.text
    site = BeautifulSoup(html, "html.parser")
    # Verificando se site é um objeto BeautifulSoup
    print(type(site))
    print(site.prettify()[:1000])  # Imprime os primeiros 500 caracteres do HTML formatado
    print(site.title.string)
    
    procurar_produtos = site.find_all("span", role_="heading")
    barra_busca = site.find_all("textarea", class_="gLFyf")
    placeholder = barra_busca[0].get("placeholder") if barra_busca else "Placeholder não encontrado"

    print(f"URL acessada: {URL_GOOGLE_SHOPPING}")
    print(f"Status HTTP: {response.status_code}")
    print(f"HTML recebido: {len(html)} caracteres")
    print(f"Trecho do HTML contém o título? {'<title>' in html}")

    titulo = site.title.string.strip() if site.title and site.title.string else "Sem titulo"
    print(f"Titulo da pagina: {titulo}")

    procurar_produtos = site.find_all("span", attrs={"role": "heading"})
    print(f"Quantidade de spans com role=heading: {len(procurar_produtos)}")

    if procurar_produtos:
        for indice, produto in enumerate(procurar_produtos[:5], start=1):
            texto = produto.get_text(" ", strip=True)
            print(f"{indice}. {texto}")
    else:
        print("Nenhum span com role=heading foi encontrado no HTML retornado por requests.")

    print("\n--- Trecho inicial do HTML ---")
    print(html[:800]) """

def main():
    termo = "celular"
    p, browser, context, page = iniciar_navegador(headless=True)
    print(f'======>>> {p}')
    print(f'======>>> {browser}')
    print(f'======>>> {context}')
    response = requests.get(URL_GOOGLE_SHOPPING)
    html = response.text
    site = BeautifulSoup(html, "html.parser")
    
    try:
        abrir_pagina(page, URL_GOOGLE_SHOPPING)
        print(f'======>>> Página aberta: {page}')
        """ print(f'====== CONTENT ======')
        print(site.prettify()[:1000])  # Imprime os primeiros 1000 caracteres do conteúdo da página
        print(f'====== CONTENT ======') """
        
        if pagina_bloqueada(page):
            page.screenshot(path="bloqueio_google_shopping.png", full_page=True)
            print("Página com possível bloqueio detectada.")
            print("Screenshot salvo: bloqueio_google_shopping.png")
            return
        
        buscar_produto(page, termo)
        if buscar_produto:
            print(f"======>>> Busca por '{termo}' realizada com sucesso.")
            resultados = extrair_produtos(page, limite=10)
        
        if not resultados:
            page.screenshot(path="sem_resultados.png", full_page=True)
            print("Sem resultados. Screenshot salvo: sem_resultados.png")

        imprimir_conteudo_site(resultados)
    except PlaywrightTimeoutError:
        print("Tempo de carregamento excedido para a página.")
        
    finally:
        context.close()
        browser.close()
        p.stop()

if __name__ == "__main__":
    main()
    # lendo_conteudo_site() ---