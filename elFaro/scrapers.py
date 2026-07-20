import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

# Dominios CDN exactos de imágenes oficiales de estudio de supermercados en Chile
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
    'santaisabel.vtexassets.com'
]

def es_link_supermercado_oficial(url):
    """
    Verifica de forma estricta si el link de la imagen pertenece a los servidores 
    oficiales de Jumbo (vtexassets) o Lider/Walmart (walmartimages.cl)
    """
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    return any(pattern in url_lower for pattern in EXACT_RETAIL_CDN_PATTERNS)


def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    """
    Busca la imagen oficial del producto referenciando directamente los servidores 
    CDN oficiales de supermercados:
    - https://jumbocl.vtexassets.com
    - https://i5.walmartimages.cl
    """
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()

    if codigo_completo in _CACHE_IMAGENES and _CACHE_IMAGENES[codigo_completo]:
        return _CACHE_IMAGENES[codigo_completo]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # --- MÉTODO 1: API Directa de Jumbo (Servidores jumbocl.vtexassets.com) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_jumbo = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?fq=alternateIds_EAN:{cod}"
                resp = requests.get(url_jumbo, headers=headers, timeout=3.5)
                if resp.status_code == 200:
                    items = resp.json()
                    if items and isinstance(items, list) and len(items) > 0:
                        item = items[0]
                        if 'items' in item and len(item['items']) > 0:
                            images = item['items'][0].get('images', [])
                            for img_obj in images:
                                img_url = img_obj.get('imageUrl')
                                if es_link_supermercado_oficial(img_url):
                                    print(f"🎯 [MATCH VTEX JUMBO] {img_url}")
                                    _CACHE_IMAGENES[codigo_completo] = img_url
                                    return img_url
            except Exception as e:
                print(f"Error Jumbo VTEX API: {e}")

    # --- MÉTODO 2: API Directa de Lider / Walmart (Servidores i5.walmartimages.cl) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_lider = f"https://www.lider.cl/bff/products/search?query={cod}"
                resp = requests.get(url_lider, headers=headers, timeout=3.5)
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get('products', []) or data.get('items', [])
                    if products:
                        for prod in products:
                            img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                            if es_link_supermercado_oficial(img_url):
                                print(f"🎯 [MATCH WALMART LIDER] {img_url}")
                                _CACHE_IMAGENES[codigo_completo] = img_url
                                return img_url
            except Exception as e:
                print(f"Error Lider Walmart API: {e}")

    # --- MÉTODO 3: Búsqueda Web de Referencia con Filtro Directo de Links CDN (vtexassets / walmartimages) ---
    busquedas = [
        f"{codigo_completo} vtexassets OR walmartimages",
        f"{nombre_producto} {codigo_completo} vtexassets OR walmartimages",
        f"{nombre_producto} site:jumbo.cl OR site:lider.cl"
    ]

    for b in busquedas:
        if not b.strip():
            continue
        try:
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(b)}"
            resp = requests.get(url_search, headers=headers, timeout=3.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Analizar todos los enlaces de imágenes de la página de resultados
                for a in soup.find_all('a'):
                    href = a.get('href') or ''
                    if 'uddg=' in href:
                        href = urllib.parse.unquote(href.split('uddg=')[-1].split('&')[0])
                    if es_link_supermercado_oficial(href):
                        print(f"🎯 [MATCH REFERENCIA WEB CDN] {href}")
                        _CACHE_IMAGENES[codigo_completo] = href
                        return href

                for img in soup.find_all('img'):
                    src = img.get('src') or ''
                    if src.startswith('//'):
                        src = 'https:' + src
                    if es_link_supermercado_oficial(src):
                        print(f"🎯 [MATCH REFERENCIA WEB IMG] {src}")
                        _CACHE_IMAGENES[codigo_completo] = src
                        return src
        except Exception as e:
            print(f"Error búsqueda de referencia CDN: {e}")

    _CACHE_IMAGENES[codigo_completo] = None
    return None
