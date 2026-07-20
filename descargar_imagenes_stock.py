import os
import csv
import re
import time
import requests
import urllib.parse

# --- CONFIGURACIÓN ---
CSV_FILENAME = 'Lista_de_Precios_Base.csv'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'imagenes_productos')

# Servidores oficiales de retail (Máxima prioridad: Fotos de estudio aisladas sobre fondo blanco)
RETAIL_CDN_DOMAINS = [
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
    return any(domain in url_lower for domain in RETAIL_CDN_DOMAINS)

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

def buscar_url_imagen_retail(codigo_barras, nombre_producto):
    codigo_limpio = str(codigo_barras).strip().lstrip('0')
    codigo_completo = str(codigo_barras).strip()
    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)

    # 1. Jumbo VTEX API por EAN (Fotos de estudio aisladas)
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
                                        return img_url, 'Jumbo VTEX (EAN)'
            except Exception:
                pass

    # 2. Lider Walmart API por EAN (Fotos de estudio aisladas)
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
                                return img_url, 'Lider Walmart (EAN)'
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
                                    return img_url, 'Jumbo VTEX (Nombre)'
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
                            return img_url, 'Lider Walmart (Nombre)'
        except Exception:
            pass

    # 5. BÚSQUEDA DE RESPALDO EN GOOGLE / WEB (Fotos de producto sobre fondo blanco, sin fotos caseras)
    if nombre_query:
        try:
            b_query = f"{nombre_query} {codigo_completo} producto supermercado fondo blanco"
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(b_query)}"
            resp = requests.get(url_search, headers=HEADERS, timeout=4.0)
            if resp.status_code == 200:
                # Extraer URLs de imágenes directa
                matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|png|webp|jpeg))', resp.text, re.IGNORECASE)
                
                # Primero probar coincidencia con servidores e-commerce
                for m_url in matches:
                    if es_link_supermercado_oficial(m_url):
                        return m_url, 'Google Web Retail CDN'

                # Segundo probar fotos web que NO sean de redes o caseras
                for m_url in matches:
                    if not es_foto_casera_o_red_social(m_url) and not 'duckduckgo' in m_url.lower():
                        return m_url, 'Google Web Studio Match'
        except Exception as e:
            pass

    return None, None

def descargar_imagen(url, ruta_salida):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(ruta_salida, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        print(f"Error descargando {url}: {e}")
    return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILENAME)
    if not os.path.exists(csv_path):
        print(f"[X] No se encontro el archivo CSV en: {csv_path}")
        return

    print("==========================================================")
    print("INICIANDO DESCARGADOR AUTOMATICO DE IMAGENES STOCK")
    print(f"Carpeta destino: {OUTPUT_DIR}")
    print("==========================================================")

    productos = []
    with open(csv_path, mode='r', encoding='utf-8-sig', errors='replace') as f:
        reader = csv.reader(f)
        encabezado_encontrado = False
        for row in reader:
            if not row or len(row) < 3:
                continue
            if 'Código Barras' in row or 'Codigo Barras' in row or 'Código' in row:
                encabezado_encontrado = True
                continue
            if encabezado_encontrado:
                cod = row[1].strip() if len(row) > 1 else ''
                nombre = row[3].strip() if len(row) > 3 else (row[2].strip() if len(row) > 2 else '')
                if cod and re.match(r'^\d+$', cod):
                    productos.append({'codigo': cod, 'nombre': nombre})

    total = len(productos)
    print(f"Total de productos cargados desde el CSV: {total}\n")

    exitosos = 0
    ya_existian = 0
    fallidos = 0

    for idx, prod in enumerate(productos, 1):
        cod = prod['codigo']
        nombre = prod['nombre']
        filename = f"{cod}.jpg"
        filepath = os.path.join(OUTPUT_DIR, filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
            ya_existian += 1
            print(f"[{idx}/{total}] SKIP {cod}.jpg ya existe.")
            continue

        print(f"[{idx}/{total}] Buscando foto de estudio para: '{nombre}' ({cod})...")
        url_img, fuente = buscar_url_imagen_retail(cod, nombre)

        if url_img:
            if descargar_imagen(url_img, filepath):
                exitosos += 1
                print(f"   [OK] Descargada ({fuente}) -> {filename}")
            else:
                fallidos += 1
                print(f"   [FAIL] Fallo la descarga de URL: {url_img}")
        else:
            fallidos += 1
            print(f"   [WARN] Sin foto de estudio para {cod}")

        time.sleep(0.15)

    print("\n==========================================================")
    print("DESCARGA FINALIZADA")
    print(f"Descargadas nuevas: {exitosos}")
    print(f"Ya existian: {ya_existian}")
    print(f"Sin imagen encontrada: {fallidos}")
    print(f"Carpeta de imagenes listas: {OUTPUT_DIR}")
    print("==========================================================")

if __name__ == '__main__':
    main()
