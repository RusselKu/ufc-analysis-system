import requests
import json
import time  # Para hacer pausas
from bs4 import BeautifulSoup

def obtener_todos_los_slugs():
    """
    Función 1: Scrapea la página de rankings para obtener
    una lista única de todos los slugs de peleadores.
    """
    URL = 'https://us.ufcespanol.com/rankings'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"Buscando la lista de peleadores en: {URL}...")
    
    try:
        pagina = requests.get(URL, headers=headers)
        pagina.raise_for_status()
        soup = BeautifulSoup(pagina.content, 'html.parser')
        
        # Usamos un SET para guardar los slugs.
        # Un 'set' automáticamente evita duplicados.
        slugs_unicos = set()
        
        # Usamos la clase que encontramos en la Versión 2
        peleadores_tags = soup.find_all('td', class_='views-field-title')
        
        for tag in peleadores_tags:
            enlace = tag.find('a')
            if enlace and enlace.has_attr('href'):
                href = enlace['href'] # ej. "/athlete/ilia-topuria"
                # Dividimos el texto por '/' y tomamos el último trozo
                slug = href.split('/')[-1]
                if slug: # Asegurarnos de que no esté vacío
                    slugs_unicos.add(slug)
        
        print(f"Se encontraron {len(slugs_unicos)} peleadores únicos.")
        # Convertimos el set a una lista para poder iterarla
        return list(slugs_unicos)

    except requests.exceptions.RequestException as e:
        print(f"Error fatal al obtener la lista de slugs: {e}")
        return [] # Devolvemos una lista vacía si falla


def scrapear_perfil_ufc(slug_del_peleador):
    """
    Función 2: Scrapea el perfil de un solo peleador.
    (Versión 9, con una corrección de tipeo).
    """
    URL = f'https://us.ufcespanol.com/athlete/{slug_del_peleador}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Este print nos sirve para ver el progreso
    print(f"--- Obteniendo datos de: {slug_del_peleador} ---")
    
    try:
        pagina = requests.get(URL, headers=headers)
        # Algunos perfiles pueden estar "ocultos" o rotos (error 404)
        if pagina.status_code != 200:
            print(f"ADVERTENCIA: No se pudo encontrar el perfil de {slug_del_peleador} (Error {pagina.status_code}). Saltando...")
            return None

        soup = BeautifulSoup(pagina.content, 'html.parser')
        datos_peleador = {}

        # Añadimos el slug a los datos, ¡es un buen identificador!
        datos_peleador['slug'] = slug_del_peleador

        nombre_tag = soup.find('h1', class_='hero-profile__name')
        datos_peleador['nombre'] = nombre_tag.get_text(strip=True) if nombre_tag else 'No encontrado'
        
        apodo_tag = soup.find('p', class_='hero-profile__nickname')
        datos_peleador['apodo'] = apodo_tag.get_text(strip=True) if apodo_tag else 'No encontrado'
        
        record_tag = soup.find('p', class_='hero-profile__division-body')
        if record_tag:
            record_texto_crudo = record_tag.get_text(strip=True)
            datos_peleador['record_raw'] = record_texto_crudo.split(' ')[0]
        else:
            datos_peleador['record_raw'] = 'No encontrado'
        
        stats_list = soup.find_all('div', class_='stats-records__stat')
        
        for stat in stats_list:
            titulo_tag = stat.find('div', class_='stats-records__stat-title')
            # --- ¡ERROR DE TIPEO CORREGIDO AQUÍ! ---
            # Antes decía 'classS_', ahora dice 'class_'
            valor_tag = stat.find('div', class_='stats-records__stat-value') 
            
            if titulo_tag and valor_tag:
                titulo = titulo_tag.get_text(strip=True)
                valor = valor_tag.get_text(strip=True)
                datos_peleador[titulo] = valor

        # ¡Ya no imprimimos el JSON aquí!
        # Solo devolvemos el diccionario
        return datos_peleador

    except Exception as e:
        print(f"Ocurrió un error inesperado al scrapear {slug_del_peleador}: {e}")
        return None

# --- BLOQUE PRINCIPAL (EL ORQUESTADOR) ---
if __name__ == "__main__":
    
    # PASO 1: Obtener la lista de tareas
    print("=== INICIANDO SCRIPT MAESTRO DE SCRAPING UFC ===")
    lista_de_slugs = obtener_todos_los_slugs()
    
    if not lista_de_slugs:
        print("No se pudieron obtener los slugs. Terminando script.")
    else:
        # PASO 2: Procesar la lista de tareas
        
        # --- ¡ERROR DE SINTAXIS CORREGIDO AQUÍ! ---
        # Esta línea ahora tiene la comilla de cierre "
        print(f"\n=== COMENZANDO SCRAPING DE {len(lista_de_slugs)} PERFILES ===")
        print("Esto puede tardar varios minutos...")
        
        todos_los_datos_finales = []
        
        for slug in lista_de_slugs:
            datos = scrapear_perfil_ufc(slug)
            
            if datos: # Si la función no devolvió None
                todos_los_datos_finales.append(datos)
            
            # --- ¡LA PARTE MÁS IMPORTANTE! ---
            # Esperar 1 segundo para ser amables con el servidor.
            time.sleep(1) 

        # PASO 3: Guardar todo en un archivo
        print(f"\n=== SCRAPING COMPLETADO ===")
        print(f"Se obtuvieron datos de {len(todos_los_datos_finales)} peleadores.")
        
        nombre_archivo = 'todos_los_peleadores.json'
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            # Usamos json.dump para escribir la lista completa en el archivo
            json.dump(todos_los_datos_finales, f, indent=2, ensure_ascii=False)
            
        print(f"¡Éxito! Todos los datos han sido guardados en el archivo: {nombre_archivo}")