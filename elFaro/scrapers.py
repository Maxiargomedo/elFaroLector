import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    """
    Busca automáticamente la imagen stock de supermercado (.jpg/.png limpia)
    para un producto mediante búsqueda en Open Food Facts, Jumbo, Lider o web scraping.
    """
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()

    # Verificar si está en caché
    if codigo_completo in _CACHE_IMAGENES:
        return _CACHE_IMAGENES[codigo_completo]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
    }

    imagen_url = None

    # --- FUENTE 1: Open Food Facts API (EAN / UPC internacional y Chile) ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 8:
            try:
                url_off = f"https://world.openfoodfacts.org/api/v2/product/{cod}.json"
                resp = requests.get(url_off, headers=headers, timeout=2.5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('status') == 1 and 'product' in data:
                        prod = data['product']
                        imagen_url = (prod.get('image_front_url') or 
                                      prod.get('image_url') or 
                                      prod.get('image_front_small_url'))
                        if imagen_url:
                            print(f"📷 [SCRAPER SUCCESS] Encontrada en OpenFoodFacts: {imagen_url}")
                            _CACHE_IMAGENES[codigo_completo] = imagen_url
                            return imagen_url
            except Exception as e:
                print(f"Error OpenFoodFacts: {e}")

    # --- FUENTE 2: API de Catálogo Jumbo.cl ---
    for cod in [codigo_completo, codigo_limpio]:
        if len(cod) >= 8:
            try:
                url_jumbo = f"https://www.jumbo.cl/api/catalog_system/pub/products/search?fq=alternateIds_EAN:{cod}"
                resp = requests.get(url_jumbo, headers=headers, timeout=3.0)
                if resp.status_code == 200:
                    items = resp.json()
                    if items and isinstance(items, list) and len(items) > 0:
                        item = items[0]
                        if 'items' in item and len(item['items']) > 0:
                            images = item['items'][0].get('images', [])
                            if images and len(images) > 0:
                                imagen_url = images[0].get('imageUrl')
                                if imagen_url:
                                    print(f"📷 [SCRAPER SUCCESS] Encontrada en Jumbo API: {imagen_url}")
                                    _CACHE_IMAGENES[codigo_completo] = imagen_url
                                    return imagen_url
            except Exception as e:
                print(f"Error Jumbo API: {e}")

    # --- FUENTE 3: Búsqueda por Nombre / Código en E-commerce de Chile (Lider / Jumbo / Cornershop) ---
    if nombre_producto:
        try:
            query = f"{nombre_producto} supermercado chile"
            url_ddg = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = requests.get(url_ddg, headers=headers, timeout=3.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                for img in soup.find_all('img'):
                    src = img.get('src') or ''
                    if src.startswith('//'):
                        src = 'https:' + src
                    if 'http' in src and any(domain in src for domain in ['jumbo.cl', 'lider.cl', 'cornershop', 'unimarc.cl', 'wikimedia', 'bing']):
                        print(f"📷 [SCRAPER SUCCESS] Encontrada en Web Search: {src}")
                        _CACHE_IMAGENES[codigo_completo] = src
                        return src
        except Exception as e:
            print(f"Error DuckDuckGo Search: {e}")

    # Si no se encuentra imagen stock, retornar una imagen placeholder limpia de producto
    imagen_fallback = "https://images.unsplash.com/photo-1542838132-92c53300491e?w=500&auto=format&fit=crop&q=80"
    _CACHE_IMAGENES[codigo_completo] = None
    return None
