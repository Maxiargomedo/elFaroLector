import os
import csv
import re
import time
import requests
import urllib.parse

# --- CONFIGURACIÓN ---
CSV_FILENAME = 'Lista_de_Precios_Base.csv'
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'imagenes_productos')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-CL,es;q=0.9,en-US;q=0.8,en;q=0.7'
}

def limpiar_nombre_para_busqueda(nombre):
    """Limpia el nombre del producto quitando caracteres extraños"""
    if not nombre:
        return ""
    nombre_clean = re.sub(r'[\(\)\[\]\{\}\*\_\,]+', ' ', nombre)
    return ' '.join(nombre_clean.split())

def buscar_imagen_google(nombre_producto, codigo_barras):
    """
    Busca la foto promocional/catálogo oficial del producto directamente en Google Images / DuckDuckGo Images
    usando el nombre exacto del producto.
    """
    nombre_query = limpiar_nombre_para_busqueda(nombre_producto)
    if not nombre_query:
        return None, None

    # Probar primero con el nombre exacto del producto (como en Google Images)
    busquedas = [
        f"{nombre_query}",
        f"{nombre_query} {codigo_barras}"
    ]

    for query in busquedas:
        try:
            url_search = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            resp = requests.get(url_search, headers=HEADERS, timeout=4.5)
            if resp.status_code == 200:
                # Extraer URLs de imágenes JPG/PNG/WEBP directamente de los resultados de búsqueda
                matches = re.findall(r'(https?://[^\s"\'<>]+\.(?:jpg|png|webp|jpeg))', resp.text, re.IGNORECASE)
                for m_url in matches:
                    m_lower = m_url.lower()
                    # Ignorar favicons, logos de navegadores y miniaturas de la propia página de búsqueda
                    if any(skip in m_lower for skip in ['duckduckgo.com', 'favicon', 'logo', 'icon', 'yandex', 'bing.com/th']):
                        continue
                    
                    # ¡Encontrada foto promocional de producto!
                    return m_url, 'Google/DuckDuckGo Images'
        except Exception as e:
            pass

    return None, None

def descargar_imagen(url, ruta_salida):
    """Descarga la imagen del producto y la guarda en disco"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(ruta_salida, 'wb') as f:
                f.write(r.content)
            return True
    except Exception as e:
        pass
    return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    csv_path = os.path.join(os.path.dirname(__file__), CSV_FILENAME)
    if not os.path.exists(csv_path):
        print(f"[X] No se encontro el archivo CSV en: {csv_path}")
        return

    print("==========================================================")
    print("INICIANDO DESCARGADOR DE IMAGENES PROMOCIONALES DE GOOGLE")
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

        print(f"[{idx}/{total}] Buscando foto promocional para: '{nombre}'...")
        url_img, fuente = buscar_imagen_google(nombre, cod)

        if url_img:
            if descargar_imagen(url_img, filepath):
                exitosos += 1
                print(f"   [OK] Descargada imagen de producto -> {filename}")
            else:
                fallidos += 1
                print(f"   [FAIL] No se pudo descargar la imagen")
        else:
            fallidos += 1
            print(f"   [WARN] Sin foto promocional encontrada para {nombre}")

        time.sleep(0.12)

    print("\n==========================================================")
    print("DESCARGA FINALIZADA")
    print(f"Descargadas nuevas: {exitosos}")
    print(f"Ya existian: {ya_existian}")
    print(f"Sin imagen encontrada: {fallidos}")
    print(f"Carpeta de imagenes listas: {OUTPUT_DIR}")
    print("==========================================================")

if __name__ == '__main__':
    main()
