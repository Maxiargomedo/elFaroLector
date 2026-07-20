import requests
import re
import urllib.parse

# Caché en memoria RAM para respuesta instantánea en escaneos repetidos
_CACHE_REALTIME_URLS = {}

# Lista de exclusión para filtrar logos, iconos o redes sociales
DOMINIOS_EXCLUIDOS = [
    'facebook.com', 'instagram.com', 'pinterest.com', 'yapochile',
    'yapo.cl', 'blogspot.com', 'wordpress.com', 'twitter.com', 'tiktok.com',
    'reddit.com', 'flickr.com', 'ebay.com', 'stock.adobe.com', 'shutterstock.com',
    'alamy.com', 'stocksy.com', 'freepik.com', 'vecteezy.com'
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
}

def es_url_valida(url):
    """Verifica que la URL pertenezca a una imagen promocional válida"""
    if not url or not isinstance(url, str):
        return False
    url_lower = url.lower()
    if any(bad in url_lower for bad in DOMINIOS_EXCLUIDOS):
        return False
    if any(skip in url_lower for skip in ['favicon', 'logo', 'icon', 'avatar', 'banner']):
        return False
    return True

def limpiar_nombre_para_busqueda(nombre):
    if not nombre:
        return ""
    nombre_clean = re.sub(r'[\(\)\[\]\{\}\*\_\,]+', ' ', nombre)
    return ' '.join(nombre_clean.split())

def obtener_imagen_promocional_realtime(nombre_producto, codigo_barras):
    """
    Busca en tiempo real la URL de la imagen promocional del producto al escanear,
    SIN descargar ni guardar ningún archivo físico en el servidor.
    """
    codigo_completo = str(codigo_barras).strip()
    
    # 1. Verificar si ya fue consultado en la memoria RAM del servidor
    if codigo_completo in _CACHE_REALTIME_URLS:
        return _CACHE_REALTIME_URLS[codigo_completo]

    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)
    if not nombre_query:
        nombre_query = codigo_completo

    queries = [
        f"{nombre_query} supermercado chile",
        f"{nombre_query}"
    ]

    for q in queries:
        try:
            url_bing = f"https://www.bing.com/images/search?q={urllib.parse.quote(q)}&cc=CL"
            resp = requests.get(url_bing, headers=HEADERS, timeout=2.5)
            if resp.status_code == 200:
                murls = re.findall(r'murl&quot;:&quot;(https?://[^&"]+)&quot;', resp.text)
                for img_url in murls:
                    if es_url_valida(img_url):
                        print(f"⚡ [REALTIME IMAGE WEB] {img_url}")
                        _CACHE_REALTIME_URLS[codigo_completo] = img_url
                        return img_url
        except Exception as e:
            print(f"Error búsqueda tiempo real: {e}")

    _CACHE_REALTIME_URLS[codigo_completo] = None
    return None
