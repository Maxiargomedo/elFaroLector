import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

# Dominios CDN oficiales de retail / supermercados en Chile (Imágenes de estudio con fondo blanco)
EXACT_RETAIL_CDN_PATTERNS = [
    'jumbocl.vtexassets.com',
    'jumbo.vtexassets.com',
    'i5.walmartimages.cl',
    'walmartimages.cl',
    'walmartimages.com',
    'vtexassets.com',
    'images.lider.cl',
    'cornershopapp.com',
    'unimarc.vtexassets.com',
    'santaisabel.vtexassets.com',
    'tottus.vtexassets.com'
]

def es_link_supermercado_oficial(url):
    """
    Verifica de forma estricta si la imagen proviene de un CDN de estudio de retail
    (Jumbo, Lider, Walmart, Cornershop, Unimarc).
    """
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in EXACT_RETAIL_CDN_PATTERNS)


def limpiar_nombre_para_busqueda(nombre):
    """Limpia el nombre del producto quitando caracteres extraños para búsquedas de e-commerce"""
    if not nombre:
        return ""
    # Quitar marcas de agua, paréntesis y mantener palabras clave
    nombre_clean = re.sub(r'[\(\)\[\]\{\}\*\_]+', ' ', nombre)
    return ' '.join(nombre_clean.split()[:5])


def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    """
    Busca únicamente imágenes oficiales de estudio (fondo blanco limpio)
    utilizando búsqueda por EAN y por nombre en Jumbo (VTEX) y Lider (Walmart).
    """
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()
    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # --- 1. JUMBO VTEX API (Por Código EAN) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_jumbo = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?fq=alternateIds_EAN:{cod}"
                resp = requests.get(url_jumbo, headers=headers, timeout=3.0)
                if resp.status_code == 200:
                    items = resp.json()
                    if items and isinstance(items, list) and len(items) > 0:
                        for item in items:
                            if 'items' in item and len(item['items']) > 0:
                                images = item['items'][0].get('images', [])
                                for img_obj in images:
                                    img_url = img_obj.get('imageUrl')
                                    if es_link_supermercado_oficial(img_url):
                                        print(f"🎯 [JUMBO EAN MATCH] {img_url}")
                                        _CACHE_IMAGENES[codigo_completo] = img_url
                                        return img_url
            except Exception as e:
                print(f"Error Jumbo EAN API: {e}")

    # --- 2. LIDER WALMART API (Por Código EAN) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_lider = f"https://www.lider.cl/bff/products/search?query={cod}"
                resp = requests.get(url_lider, headers=headers, timeout=3.0)
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get('products', []) or data.get('items', [])
                    if products:
                        for prod in products:
                            img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                            if es_link_supermercado_oficial(img_url):
                                print(f"🎯 [LIDER EAN MATCH] {img_url}")
                                _CACHE_IMAGENES[codigo_completo] = img_url
                                return img_url
            except Exception as e:
                print(f"Error Lider EAN API: {e}")

    # --- 3. JUMBO VTEX API (Por Nombre de Producto) ---
    if nombre_query:
        try:
            url_jumbo_ft = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?ft={urllib.parse.quote(nombre_query)}"
            resp = requests.get(url_jumbo_ft, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                items = resp.json()
                if items and isinstance(items, list) and len(items) > 0:
                    for item in items:
                        if 'items' in item and len(item['items']) > 0:
                            images = item['items'][0].get('images', [])
                            for img_obj in images:
                                img_url = img_obj.get('imageUrl')
                                if es_link_supermercado_oficial(img_url):
                                    print(f"🎯 [JUMBO TEXT MATCH] {img_url}")
                                    _CACHE_IMAGENES[codigo_completo] = img_url
                                    return img_url
        except Exception as e:
            print(f"Error Jumbo Text API: {e}")

    # --- 4. LIDER WALMART API (Por Nombre de Producto) ---
    if nombre_query:
        try:
            url_lider_ft = f"https://www.lider.cl/bff/products/search?query={urllib.parse.quote(nombre_query)}"
            resp = requests.get(url_lider_ft, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get('products', []) or data.get('items', [])
                if products:
                    for prod in products:
                        img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                        if es_link_supermercado_oficial(img_url):
                            print(f"🎯 [LIDER TEXT MATCH] {img_url}")
                            _CACHE_IMAGENES[codigo_completo] = img_url
                            return img_url
        except Exception as e:
            print(f"Error Lider Text API: {e}")

    # --- 5. BÚSQUEDA DUCKDUCKGO / GOOGLE IMAGES (Búsqueda estricta de links jumbocl.vtexassets.com o i5.walmartimages.cl) ---
    if nombre_query:
        try:
            b_query = f"{nombre_query} {codigo_completo} jumbocl.vtexassets.com OR i5.walmartimages.cl"
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(b_query)}"
            resp = requests.get(url_search, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for a in soup.find_all('a'):
                    href = a.get('href') or ''
                    if 'uddg=' in href:
                        href = urllib.parse.unquote(href.split('uddg=')[-1].split('&')[0])
                    if es_link_supermercado_oficial(href):
                        print(f"🎯 [WEB SEARCH CDN MATCH] {href}")
                        _CACHE_IMAGENES[codigo_completo] = href
                        return href

                for img in soup.find_all('img'):
                    src = img.get('src') or ''
                    if src.startswith('//'):
                        src = 'https:' + src
                    if es_link_supermercado_oficial(src):
                        print(f"🎯 [WEB SEARCH IMG MATCH] {src}")
                        _CACHE_IMAGENES[codigo_completo] = src
                        return src
        except Exception as e:
            print(f"Error DuckDuckGo CDN Search: {e}")

    return None
