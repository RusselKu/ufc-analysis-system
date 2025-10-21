import requests
import json
from bs4 import BeautifulSoup

URL_BASE = 'http://ufcstats.com'

# Encabezados para simular una petición de navegador y evitar bloqueos (500 Error)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ----------------------------------------------------------------------
# TESTEO DE EXTRACCIÓN 1: LISTA DE PELEADORES
# ----------------------------------------------------------------------

def test_extract_fighter_list(url_fighters):
    """Extrae nombres, clase de peso y el enlace al perfil de cada peleador."""
    print("=" * 70)
    print(f"--- 🥊 TEST 1: Extracción de Lista de Peleadores desde: {url_fighters} ---")
    print("=" * 70)
    
    try:
        # Petición con el User-Agent simulado
        response = requests.get(url_fighters, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser') 
        
        fighters_data = []
        
        # 1. Encontrar todas las filas de datos de peleadores
        rows = soup.find_all('tr', class_='b-statistics__table-row')
        
        if not rows:
            print("❌ Error: No se encontraron filas de peleadores. ¡Revisar selector CSS!")
            return []

        for row in rows:
            # Enlace al perfil individual (columna 1)
            link_tag = row.find('a', class_='b-link') 
            cells = row.find_all('td')
            
            if link_tag and 'href' in link_tag.attrs and len(cells) >= 3: 
                
                name = link_tag.text.strip()
                profile_url = link_tag['href']
                weight_class = cells[2].text.strip() # Clase de peso (índice 2)
                
                fighters_data.append({
                    'name': name,
                    'weight_class': weight_class,
                    'profile_url': profile_url
                })

        print(f"✅ Extracción de lista exitosa. Se encontraron {len(fighters_data)} registros.")
        return fighters_data

    except requests.RequestException as e:
        print(f"❌ Error en la petición: {e}")
        return []

# ----------------------------------------------------------------------
# TESTEO DE EXTRACCIÓN 2: DETALLES Y HISTORIAL DE COMBATES
# ----------------------------------------------------------------------

def test_extract_fighter_details_with_fights(profile_url):
    """Extrae métricas detalladas y el historial de combates de un peleador."""
    print("=" * 70)
    print(f"--- 📊 TEST 2: Extracción de Detalles y Historial desde: {profile_url} ---")
    print("=" * 70)
    
    try:
        response = requests.get(profile_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 1. Extracción de Métricas de Carrera (SLPM, SAPM, TD_Avg, TD_Def)
        stats_block = {}
        stats_group = soup.find('div', class_='b-list__info-box-left')
        
        if stats_group:
            stats_items = stats_group.find_all('li', class_='b-list__box-list-item')
            for item in stats_items:
                text = item.text.strip()
                if ':' in text:
                    key, value = text.split(':', 1)
                    stats_block[key.strip()] = value.strip()
        
        key_metrics = {
            'SLpM': stats_block.get('SLpM', 'N/A'),
            'SAPM': stats_block.get('SApM', 'N/A'),
            'TD_Avg': stats_block.get('TD Avg.', 'N/A'),
            'TD_Def': stats_block.get('TD Def.', 'N/A'),
            'Strikes_Acc': stats_block.get('Str. Acc.', 'N/A')
        }
        
        # 2. Extracción del Historial de Combates
        fights_history = []
        fights_table = soup.find('table', class_='b-fight-details__table')

        if fights_table:
            rows = fights_table.find_all('tr', class_='b-fight-details__table-row')
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 8:
                    result_raw = cells[0].text.strip()
                    opponent_tag = cells[1].find('a') 
                    opponent_name = opponent_tag.text.strip() if opponent_tag else 'N/A'
                    event_tag = cells[6].find('a') 
                    event_name = event_tag.text.strip() if event_tag else 'N/A'
                    
                    win_binary = 1 if result_raw == 'W' else (0 if result_raw == 'L' else -1)
                    
                    fights_history.append({
                        'result_text': result_raw,
                        'win_binary': win_binary,
                        'opponent': opponent_name,
                        'event': event_name,
                        'link_detalle_combate': event_tag['href'] if event_tag else 'N/A'
                    })

            print(f"✅ Extracción de historial exitosa. Se encontraron {len(fights_history)} combates.")
        else:
             print("❌ Error: No se encontró la tabla de historial de combates. ¡Revisar selector!")
        
        return {
            'career_metrics': key_metrics,
            'fights_history': fights_history
        }

    except requests.RequestException as e:
        print(f"❌ Error al extraer detalles: {e}. Revisa la URL o si el User-Agent está siendo bloqueado.")
        return {'career_metrics': {}, 'fights_history': []}

# ----------------------------------------------------------------------
# EJECUCIÓN DE TESTEOS Y FORMATO DE SALIDA EN LISTA
# ----------------------------------------------------------------------

# Ejecución del Test 1
fighters = test_extract_fighter_list(URL_BASE + "/statistics/fighters?page=all") 

print("\n--- 📋 Vista Previa de Lista de Peleadores (Primeros 3) ---")
if fighters:
    # Imprimimos en formato JSON indentado para legibilidad
    print(json.dumps(fighters[:3], indent=4, ensure_ascii=False))
else:
    print("No hay datos de peleadores para mostrar.")

# Ejecución del Test 2: Usar el URL del primer peleador encontrado (si la lista no está vacía)
if fighters:
    sample_url = fighters[0]['profile_url']
else:
    # URL de respaldo para pruebas manuales si la lista de peleadores falla
    # Nota: Este URL DEBE ser validado manualmente si el test anterior falla
    sample_url = 'http://ufcstats.com/fighter-details/935560b73c9f280a' 
    print("\nAVISO: Usando URL de respaldo para el Test 2.")


full_details = test_extract_fighter_details_with_fights(sample_url)

print("\n--- 📈 Métricas Clave Extraídas ---")
# Imprimimos el diccionario de métricas
print(json.dumps(full_details['career_metrics'], indent=4, ensure_ascii=False))

print("\n--- 📜 Historial de Combates (Primeros 3) ---")
# Imprimimos la lista de combates
print(json.dumps(full_details['fights_history'][:3], indent=4, ensure_ascii=False))