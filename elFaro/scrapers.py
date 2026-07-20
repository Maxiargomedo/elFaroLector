import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

# Lista de dominios CDN oficiales de retail / supermercados (fotos de estudio con fondo blanco)
RETAIL_CDN_DOMAINS = [
    'vtexassets.com',
    'jumbo.cl',
    'lider.cl',
    'cornershopapp.com',
    'unimarc.cl',
    'tottus.cl',
    'walmartimages.com',
    'santaisabel.cl',
    'falabella.com',
    'ripley.cl'
]

def es_imagen_retail_oficial(url):
    """Verifica si una URL proviene de un servidor oficial de retail de estudio"""
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    return any(domain in url_lower for domain in RETAIL_CDN_DOMAINS)


def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    """
    Busca únicamente la imagen oficial de estudio (sobre fondo blanco / aislada) 
    de supermercados e e-commerce de Chile (Jumbo, Lider, Cornershop, Unimarc, etc.)
    """
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()

    # Verificar caché en memoria
    if codigo_completo in _CACHE_IMAGENES and _CACHE_IMAGENES[codigo_completo]:
        return _CACHE_IMAGENES[codigo_completo]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    # --- PRIORITY 1: API Directa de Jumbo.cl (Fotos de estudio VTEX 100% aisladas) ---
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
                            if images and len(images) > 0:
                                img_url = images[0].get('imageUrl')
                                if img_url and es_imagen_retail_oficial(img_url):
                                    print(f"🛍️ [RETAIL STOCK] Imagen studio Jumbo obtenida: {img_url}")
                                    _CACHE_IMAGENES[codigo_completo] = img_url
                                    return img_url
            except Exception as e:
                print(f"Error Jumbo API: {e}")

    # --- PRIORITY 2: API de Búsqueda por EAN en Lider.cl (Walmart Chile) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 7:
            try:
                url_lider = f"https://www.lider.cl/bff/products/search?query={cod}"
                resp = requests.get(url_lider, headers=headers, timeout=3.5)
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get('products', []) or data.get('items', [])
                    if products:
                        prod = products[0]
                        img_url = prod.get('image') or prod.get('imageUrl') or prod.get('thumbnail')
                        if img_url and es_imagen_retail_oficial(img_url):
                            print(f"🛍️ [RETAIL STOCK] Imagen studio Lider obtenida: {img_url}")
                            _CACHE_IMAGENES[codigo_completo] = img_url
                            return img_url
            except Exception as e:
                print(f"Error Lider API: {e}")

    # --- PRIORITY 3: Búsqueda Web filtrada EXCLUSIVAMENTE por CDNs de Supermercados ---
    query_terms = []
    if nombre_producto:
        query_terms.append(f"{nombre_producto}")
    query_terms.append(f"{codigo_completo}")

    for q_text in query_terms:
        try:
            query = f"{q_text} site:jumbo.cl OR site:lider.cl OR site:cornershopapp.com OR site:unimarc.cl"
            url_ddg = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = requests.get(url_ddg, headers=headers, timeout=3.5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or ''
                    if src.startswith('//'):
                        src = 'https:' + src
                    if es_imagen_retail_oficial(src):
                        print(f"🛍️ [RETAIL STOCK] Imagen studio filtrada web: {src}")
                        _CACHE_IMAGENES[codigo_completo] = src
                        return src
        except Exception as e:
            print(f"Error Retail Web Search: {e}")

    # --- PRIORITY 4: Open Food Facts (Filtro secundario si viene de servidor de imágenes de producto) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 8:
            try:
                url_off = f"https://world.openfoodfacts.org/api/v2/product/{cod}.json"
                resp = requests.get(url_off, headers=headers, timeout=2.5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 1 and 'product' in data:
                        prod = data['product']
                        img_url = (prod.get('image_front_url') or 
                                   prod.get('image_url'))
                        if img_url and 'openfoodfacts' in img_url:
                            print(f"🛍️ [RETAIL STOCK] Imagen OpenFoodFacts: {img_url}")
                            _CACHE_IMAGENES[codigo_completo] = img_url
                            return img_url
            except Exception as e:
                print(f"Error OpenFoodFacts: {e}")

    _CACHE_IMAGENES[codigo_completo] = None
    return None
