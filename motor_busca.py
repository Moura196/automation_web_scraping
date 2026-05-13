""" - Sempre que um novo import incluido rodar: python -m pip install <nome do pacote>
    - Verificar a lista de dependências instaladas: pip list"""
from math import e

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import requests
from bs4 import BeautifulSoup

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
        print(context) """
        print(page)
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

def lendo_conteudo_site():
    response = requests.get(URL_GOOGLE_SHOPPING)
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
    print(html[:800])

def main():
    p, browser, context, page = iniciar_navegador(headless=True)
    try:
        URL_GOOGLE_SHOPPING = "https://www.google.com/shopping?hl=pt-BR&gl=br"
        abrir_pagina(page, URL_GOOGLE_SHOPPING)
        
        if pagina_bloqueada(page):
            page.screenshot(path="bloqueio_google_shopping.png", full_page=True)
            print("Página com possível bloqueio detectada.")
            print("Screenshot salvo: bloqueio_google_shopping.png")
        
    except PlaywrightTimeoutError:
        print("Tempo de carregamento excedido para a página.")
        
    finally:
        context.close()
        browser.close()
        p.stop()

if __name__ == "__main__":
    main()
    # lendo_conteudo_site() ---