import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

# Caché en memoria de URLs de imágenes obtenidas
_CACHE_IMAGENES = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
}

def es_link_supermercado_oficial(url):
    """Verifica si la URL es una imagen promocional válida de producto"""
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    # Descartar iconos, logos y favicons
    if any(skip in url_lower for skip in ['duckduckgo.com', 'favicon', 'logo', 'icon', 'avatar']):
        return False
    return True

def limpiar_nombre_para_busqueda(nombre):
    if not nombre:
        return ""
    nombre_clean = re.sub(r'[\(\)\[\]\{\}\*\_\,]+', ' ', nombre)
    return ' '.join(nombre_clean.split())

def obtener_imagen_stock_producto(codigo_barras, nombre_producto=""):
    """
    Busca la foto promocional oficial del producto directamente en Google Images / DuckDuckGo Images
    usando el nombre exacto del producto.
    """
    codigo_completo = str(codigo_barras).strip()
    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)

    if codigo_completo in _CACHE_IMAGENES and _CACHE_IMAGENES[codigo_completo]:
        return _CACHE_IMAGENES[codigo_completo]

    if not nombre_query:
        nombre_query = codigo_completo

    busquedas = [
        f"{nombre_query}",
        f"{nombre_query} {codigo_completo}"
    ]

    for query in busquedas:
        try:
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = requests.get(url_search, headers=HEADERS, timeout=4.0)
            if resp.status_code == 200:
                matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|png|webp|jpeg))', resp.text, re.IGNORECASE)
                for m_url in matches:
                    if es_link_supermercado_oficial(m_url):
                        print(f"📷 [GOOGLE PROMO MATCH] {m_url}")
                        _CACHE_IMAGENES[codigo_completo] = m_url
                        return m_url
        except Exception as e:
            print(f"Error Google Promo Search: {e}")

    _CACHE_IMAGENES[codigo_completo] = None
    return None
