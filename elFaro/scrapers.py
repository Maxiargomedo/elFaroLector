import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

# Servidores oficiales de retail (Máxima prioridad: Fotos de estudio aisladas sobre fondo blanco)
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

# Dominios que deben DESCARTARSE por ser fotos de usuarios / redes / fotos caseras
DOMINIOS_FOTOS_CASERAS = [
    'facebook.com', 'instagram.com', 'pinterest.com', 'mercadolibre', 'yapochile',
    'yapo.cl', 'blogspot.com', 'wordpress.com', 'twitter.com', 'tiktok.com',
    'reddit.com', 'flickr.com', 'ebay.com', 'wallapop.com'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
}

def es_link_supermercado_oficial(url):
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in EXACT_RETAIL_CDN_PATTERNS)

def es_foto_casera_o_red_social(url):
    if not url or not isinstance(url, str):
        return True
    url_lower = url.lower()
    return any(domain in url_lower for domain in DOMINIOS_FOTOS_CASERAS)

def limpiar_nombre_para_busqueda(nombre):
    if not nombre:
        return ""
    nombre_clean = re.sub(r'[\(\)\[\]\{\}\*\_]+', ' ', nombre)
    palabras = nombre_clean.split()
    return ' '.join(palabras[:5])

def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()
    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)

    if codigo_completo in _CACHE_IMAGENES and _CACHE_IMAGENES[codigo_completo]:
        return _CACHE_IMAGENES[codigo_completo]

    # 1. Jumbo VTEX API por EAN
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_jumbo = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?fq=alternateIds_EAN:{cod}"
                resp = requests.get(url_jumbo, headers=HEADERS, timeout=3.5)
                if resp.status_code == 200:
                    items = resp.json()
                    if items and isinstance(items, list) and len(items) > 0:
                        for item in items:
                            if 'items' in item and len(item['items']) > 0:
                                images = item['items'][0].get('images', [])
                                for img_obj in images:
                                    img_url = img_obj.get('imageUrl')
                                    if es_link_supermercado_oficial(img_url):
                                        _CACHE_IMAGENES[codigo_completo] = img_url
                                        return img_url
            except Exception:
                pass

    # 2. Lider Walmart API por EAN
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_lider = f"https://www.lider.cl/bff/products/search?query={cod}"
                resp = requests.get(url_lider, headers=HEADERS, timeout=3.5)
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get('products', []) or data.get('items', [])
                    if products:
                        for prod in products:
                            img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                            if es_link_supermercado_oficial(img_url):
                                _CACHE_IMAGENES[codigo_completo] = img_url
                                return img_url
            except Exception:
                pass

    # 3. Jumbo VTEX API por Nombre
    if nombre_query:
        try:
            url_jumbo_ft = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?ft={urllib.parse.quote(nombre_query)}"
            resp = requests.get(url_jumbo_ft, headers=HEADERS, timeout=3.5)
            if resp.status_code == 200:
                items = resp.json()
                if items and isinstance(items, list) and len(items) > 0:
                    for item in items:
                        if 'items' in item and len(item['items']) > 0:
                            images = item['items'][0].get('images', [])
                            for img_obj in images:
                                img_url = img_obj.get('imageUrl')
                                if es_link_supermercado_oficial(img_url):
                                    _CACHE_IMAGENES[codigo_completo] = img_url
                                    return img_url
        except Exception:
            pass

    # 4. Lider Walmart API por Nombre
    if nombre_query:
        try:
            url_lider_ft = f"https://www.lider.cl/bff/products/search?query={urllib.parse.quote(nombre_query)}"
            resp = requests.get(url_lider_ft, headers=HEADERS, timeout=3.5)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get('products', []) or data.get('items', [])
                if products:
                    for prod in products:
                        img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                        if es_link_supermercado_oficial(img_url):
                            _CACHE_IMAGENES[codigo_completo] = img_url
                            return img_url
        except Exception:
            pass

    # 5. BÚSQUEDA DE RESPALDO EN GOOGLE / WEB (Fondo blanco de producto, filtrando fotos caseras)
    if nombre_query:
        try:
            b_query = f"{nombre_query} {codigo_completo} producto supermercado fondo blanco"
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(b_query)}"
            resp = requests.get(url_search, headers=HEADERS, timeout=4.0)
            if resp.status_code == 200:
                matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|png|webp|jpeg))', resp.text, re.IGNORECASE)
                for m_url in matches:
                    if es_link_supermercado_oficial(m_url):
                        _CACHE_IMAGENES[codigo_completo] = m_url
                        return m_url

                for m_url in matches:
                    if not es_foto_casera_o_red_social(m_url) and not 'duckduckgo' in m_url.lower():
                        _CACHE_IMAGENES[codigo_completo] = m_url
                        return m_url
        except Exception:
            pass

    _CACHE_IMAGENES[codigo_completo] = None
    return None
