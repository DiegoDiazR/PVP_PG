import dash
from dash import html, dcc, dash_table
import pandas as pd
import numpy as np 
import re
from dash.dependencies import Input, Output, State

# ----------------- Definición de Tipos y Efectividades (Simulación de Datos) -----------------

POKEMON_TYPES = [
    "Normal", "Fuego", "Agua", "Planta", "Eléctrico", "Hielo", "Lucha", "Veneno", 
    "Tierra", "Volador", "Psíquico", "Bicho", "Roca", "Fantasma", "Dragón", 
    "Acero", "Hada", "Siniestro"
]

# Definición de Colores para cada tipo (Para el nuevo estilo visual)
TYPE_COLORS = {
    "Normal": "#A8A77A", "Fuego": "#EE8130", "Agua": "#6390F0", "Planta": "#7AC74C",
    "Eléctrico": "#F7D02C", "Hielo": "#96D9D6", "Lucha": "#C22E28", "Veneno": "#A33EA1",
    "Tierra": "#E2BF65", "Volador": "#A98FF3", "Psíquico": "#F95587", "Bicho": "#A6B91A",
    "Roca": "#B6A136", "Fantasma": "#735797", "Dragón": "#6F35FC", "Acero": "#B7B7CE",
    "Hada": "#D685AD", "Siniestro": "#705746"
}

# Matriz de Efectividad (Defensa: Columna | Ataque: Fila)
# Valores: 0.5 (Resistencia), 2.0 (Debilidad), 0.0 (Inmunidad), 1.0 (Neutral)
# La tabla es leída como: [Tipo Defensivo] x [Tipo Atacante]
TYPE_MATRIX_DATA = {
    "Normal":   {"Lucha": 2.0, "Fantasma": 0.0},
    "Fuego":    {"Agua": 2.0, "Tierra": 2.0, "Roca": 2.0, "Bicho": 0.5, "Acero": 0.5, "Hada": 0.5, "Hielo": 0.5, "Planta": 0.5, "Fuego": 0.5},
    "Agua":     {"Eléctrico": 2.0, "Planta": 2.0, "Acero": 0.5, "Fuego": 0.5, "Hielo": 0.5, "Agua": 0.5},
    "Planta":   {"Fuego": 2.0, "Hielo": 2.0, "Volador": 2.0, "Bicho": 2.0, "Veneno": 2.0, "Tierra": 0.5, "Agua": 0.5, "Eléctrico": 0.5, "Planta": 0.5},
    "Eléctrico": {"Tierra": 2.0, "Volador": 0.5, "Acero": 0.5, "Eléctrico": 0.5},
    "Hielo":    {"Fuego": 2.0, "Lucha": 2.0, "Roca": 2.0, "Acero": 2.0, "Hielo": 0.5},
    "Lucha":    {"Volador": 2.0, "Psíquico": 2.0, "Hada": 2.0, "Roca": 0.5, "Bicho": 0.5, "Siniestro": 0.5},
    "Veneno":   {"Tierra": 2.0, "Psíquico": 2.0, "Lucha": 0.5, "Veneno": 0.5, "Bicho": 0.5, "Planta": 0.5, "Hada": 0.5},
    "Tierra":   {"Agua": 2.0, "Planta": 2.0, "Hielo": 2.0, "Eléctrico": 0.0, "Veneno": 0.5, "Roca": 0.5},
    "Volador":  {"Eléctrico": 2.0, "Hielo": 2.0, "Roca": 2.0, "Tierra": 0.0, "Lucha": 0.5, "Bicho": 0.5, "Planta": 0.5},
    "Psíquico": {"Bicho": 2.0, "Fantasma": 2.0, "Siniestro": 2.0, "Lucha": 0.5, "Psíquico": 0.5},
    "Bicho":    {"Fuego": 2.0, "Volador": 2.0, "Roca": 2.0, "Tierra": 0.5, "Lucha": 0.5, "Planta": 0.5},
    "Roca":     {"Agua": 2.0, "Planta": 2.0, "Lucha": 2.0, "Tierra": 2.0, "Acero": 2.0, "Normal": 0.5, "Fuego": 0.5, "Volador": 0.5, "Veneno": 0.5},
    "Fantasma": {"Fantasma": 2.0, "Siniestro": 2.0, "Lucha": 0.0, "Normal": 0.0, "Veneno": 0.5, "Bicho": 0.5},
    "Dragón":   {"Hielo": 2.0, "Dragón": 2.0, "Hada": 2.0, "Fuego": 0.5, "Agua": 0.5, "Eléctrico": 0.5, "Planta": 0.5},
    "Acero":    {"Fuego": 2.0, "Lucha": 2.0, "Tierra": 2.0, "Veneno": 0.0, "Normal": 0.5, "Volador": 0.5, "Roca": 0.5, "Bicho": 0.5, "Acero": 0.5, "Planta": 0.5, "Psíquico": 0.5, "Hielo": 0.5, "Dragón": 0.5, "Hada": 0.5},
    "Hada":     {"Veneno": 2.0, "Acero": 2.0, "Fuego": 2.0, "Lucha": 0.5, "Bicho": 0.5, "Siniestro": 0.5, "Dragón": 0.0},
    "Siniestro":{"Lucha": 2.0, "Bicho": 2.0, "Hada": 2.0, "Psíquico": 0.0, "Fantasma": 0.5, "Siniestro": 0.5}
}

# Crear DataFrame de Efectividad de Tipos para visualización (se mantiene para la tabla de Dash)
df_types = pd.DataFrame(index=POKEMON_TYPES, columns=POKEMON_TYPES)
for defense_type, weaknesses in TYPE_MATRIX_DATA.items():
    for attack_type in POKEMON_TYPES:
        value = weaknesses.get(attack_type, 1.0)
        df_types.loc[defense_type, attack_type] = value

# Convertir la tabla para Dash (Index a columna 'Defensa')
df_types_dash = df_types.reset_index().rename(columns={'index': 'Defensa'})

# ----------------- Funciones de Ayuda para Componentes Visuales -----------------

def create_type_icon(type_name):
    """Crea un círculo de color SVG/HTML para representar el tipo."""
    color = TYPE_COLORS.get(type_name, "#708090")
    return html.Div(
        type_name,
        style={
            "backgroundColor": color,
            "color": "white",
            "borderRadius": "9999px",
            "padding": "4px 8px",
            "margin": "2px",
            "display": "inline-block",
            "fontSize": "12px",
            "fontWeight": "bold",
            "boxShadow": "1px 1px 3px rgba(0,0,0,0.3)"
        }
    )

def render_type_list(types_dict):
    """Convierte un diccionario de tipos (con multiplicadores) en una lista visual de iconos."""
    if not types_dict:
        return html.P("Ninguno", style={"color": "#7f8c8d", "padding": "5px"})
    
    type_elements = []
    
    # Ordenar por multiplicador (más fuerte a más débil)
    sorted_types = sorted(types_dict.items(), key=lambda item: float(item[1].replace('x', '')), reverse=True)

    for type_name, multiplier in sorted_types:
        icon = create_type_icon(type_name)
        # Añadir un span con el multiplicador si es un valor diferente a 1.0
        if float(multiplier.replace('x', '')) != 1.0:
             display_value = html.Span(multiplier, style={"fontSize": "0.8em", "fontWeight": "normal", "marginLeft": "5px"})
        else:
             display_value = None
             
        type_elements.append(
            html.Div(
                [icon, display_value],
                style={"display": "flex", "alignItems": "center", "marginBottom": "5px"}
            )
        )
        
    return html.Div(type_elements, style={"display": "flex", "flexWrap": "wrap", "gap": "5px"})


# ----------------- Funciones de Cálculo de Efectividad -----------------

def calculate_effectiveness(type1, type2=None):
    """Calcula las debilidades, resistencias e inmunidades para un tipo o doble tipo."""
    effectiveness = {t: 1.0 for t in POKEMON_TYPES}
    
    types_to_check = [type1]
    if type2 and type2 != "Ninguno" and type2 != type1:
        types_to_check.append(type2)
        
    for type_def in types_to_check:
        if type_def in TYPE_MATRIX_DATA:
            for attack_type, multiplier in TYPE_MATRIX_DATA[type_def].items():
                effectiveness[attack_type] *= multiplier

    debilidades = {t: f"x{v:.2f}" for t, v in effectiveness.items() if v >= 2.0}
    resistencias = {t: f"x{v:.2f}" for t, v in effectiveness.items() if v < 1.0 and v > 0.0}
    inmunidades = {t: "x0.00" for t, v in effectiveness.items() if v == 0.0}

    return debilidades, resistencias, inmunidades

# ----------------- Cargar CSV y Preprocesamiento (Código anterior...) -----------------
csv_file = "gohub_moves_with_type_full.csv"
try:
    df = pd.read_csv(csv_file, encoding="utf-8-sig") 
    print(f"✅ Datos cargados desde {csv_file}")
except FileNotFoundError:
    df = pd.DataFrame()
    print(f"❌ No se encontró {csv_file}. Asegúrate de haber ejecutado el script de scraping.")

# [Mantener todas las funciones de limpieza (normalize_score, extract_probability, clean_effects_column, clean_move_name)]
# ... (Se asume que estas funciones y el preprocesamiento de 'df' existen aquí) ...

def normalize_score(series):
    series = pd.to_numeric(series, errors='coerce').fillna(0)
    if series.empty or series.max() == 0:
        return np.repeat(0.0, len(series))
    normalized = (series / series.max()) * 10
    normalized = normalized.replace(0, 0.0) 
    normalized[normalized > 0] = np.maximum(normalized[normalized > 0], 1.0) 
    return normalized.round(2)

def extract_probability(effects: str):
    if not isinstance(effects, str) or not effects: return np.nan, np.nan
    match = re.search(r'a(\d+(\.\d+)?)%', effects)
    if match:
        prob_str = match.group(1)
        try:
            prob_percent = float(prob_str)
            prob_decimal = prob_percent / 100.0
            if prob_decimal > 0:
                avg_attacks = 1.0 / prob_decimal
                return prob_percent, avg_attacks
        except ValueError:
            pass
    return np.nan, np.nan

def clean_effects_column(effects: str) -> str:
    if not isinstance(effects, str) or not effects: return ""
    tags_to_remove = ["Spam", "Bait", "Nuke", "General", "High Energy", "BoostSpecial", "DebuffSpecial"]
    for tag in tags_to_remove:
        effects = re.sub(r'\s*/?\s*' + re.escape(tag) + r'\s*/?\s*', ' / ', effects, flags=re.IGNORECASE).strip()
    effects = re.sub(r'(\s*/\s*){2,}', ' / ', effects).strip() 
    effects = effects.strip(' /') 
    if 'a' in effects and '%' in effects:
        match = re.search(r'(a\d+(\.\d+)% chance[to:]?.*)', effects, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return effects

def clean_move_name(name: str):
    if not isinstance(name, str): return name, ""
    original_name = name
    base_name = original_name
    effects = ""
    if " / " in name:
        parts = name.split(" / ", 1)
        base_name = parts[0].strip()
        effects = parts[1].strip()
        name = base_name 
    effect_start_markers = ["a100.0%", "a50.0%", "a33.3%", "a20.0%", "a10.0%", "Self-Debuff", "BoostSpecial", "DebuffSpecial"]
    for marker in effect_start_markers:
        if marker in name:
            base_parts = name.split(marker)
            base_name = base_parts[0].strip()
            effects_part = f"{marker}{base_parts[1].strip()}" if len(base_parts) > 1 else ""
            clean_base_name_pattern = re.escape(base_name.split('has')[0].split('BoostSpecial')[0].split('DebuffSpecial')[0].split('General')[0].strip())
            effects_part = re.sub(r'\s*' + clean_base_name_pattern + r'\s*', '', effects_part, flags=re.IGNORECASE).strip()
            effects = effects_part + (f" / {effects}" if effects else "")
            base_name = re.sub(r'(Spam|Bait|Nuke|General|High Energy)$', '', base_name).strip()
            return base_name.strip(), effects.strip()
    if "Nuke" in name:
        base_name = name.replace("Nuke", "")
        effects = "Nuke" + (f" / {effects}" if effects else "")
    elif "General" in name:
        base_name = name.replace("General", "")
        effects = "General" + (f" / {effects}" if effects else "")
    elif "High Energy" in name:
        base_name = name.replace("General", "")
        effects = "High Energy" + (f" / {effects}" if effects else "")
    elif "Spam" in name:
        base_name = name.replace("Spam", "")
        effects = "Spam" + (f" / {effects}" if effects else "")
    elif "Bait" in name:
        base_name = name.replace("Bait", "")
        effects = "Bait" + (f" / {effects}" if effects else "")
    return base_name.strip(), effects.strip()

# ----------------- Pre-procesamiento y Creación de Scores -----------------
if not df.empty:
    
    # 0. LIMPIEZA DE COLUMNA NAME Y EXTRACCIÓN DE EFECTOS
    if "Name" in df.columns:
        parsed_names = df["Name"].apply(lambda x: clean_move_name(x))
        
        df["Efectos"] = [item[1] for item in parsed_names]
        df["Nombre Limpio"] = [item[0] for item in parsed_names]
        
        df = df.drop(columns=["Name"], errors='ignore')
        df = df.rename(columns={"Nombre Limpio": "Name"})
    
    
    # 0.5. CREACIÓN DE COLUMNAS DE PROBABILIDAD Y AVG. ACTIVACIÓN
    if "Efectos" in df.columns:
        prob_data = df["Efectos"].apply(extract_probability)
        
        df["Prob. %"] = [item[0] for item in prob_data]
        df["Avg. Activ."] = [item[1] for item in prob_data]
        
        df["Prob. %"] = df["Prob. %"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "")
        df["Avg. Activ."] = df["Avg. Activ."].round(1).apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")
        
        # 0.6. LIMPIEZA ADICIONAL DE LA COLUMNA EFECTOS
        df["Efectos"] = df["Efectos"].apply(clean_effects_column)
        df["Efectos"] = df["Efectos"].replace('', np.nan) 
    
    
    # 1. Conversión de columnas clave a numérico
    numeric_cols = ["DPT", "EPT", "PWR", "ENG", "CD"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('-', '0.0', regex=False)
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # 2. Crear columna DPT/EPT (Eficiencia de Daño/Turno)
    if "DPT" in df.columns and "EPT" in df.columns:
        df["DPT/EPT"] = df.apply(lambda row: row["DPT"]/row["EPT"] if row["EPT"] != 0 else 0, axis=1).round(1)

    # 3. Crear columna PWR/ENG (Daño por Energía) - CLAVE para Cargados
    if "PWR" in df.columns and "ENG" in df.columns:
        df["PWR/ENG"] = df.apply(lambda row: row["PWR"]/row["ENG"] if row["ENG"] != 0 else 0, axis=1).round(2)


    # ----------------- Creación de Scores (1 a 10) -----------------
    df["Score General"] = 0.0
    
    df_fast = df[df["Categoría"] == "Fast Moves"].copy()
    if not df_fast.empty:
        df_fast["Base_Score_Rápido"] = df_fast["DPT/EPT"] * 1.5 + df_fast["EPT"] 
        df.loc[df["Categoría"] == "Fast Moves", "Score General"] = normalize_score(df_fast["Base_Score_Rápido"]).round(1)
    
    
    df_charged = df[df["Categoría"] == "Charged Moves"].copy()
    if not df_charged.empty:
        df_charged["Base_Score_Cargado"] = df_charged["PWR/ENG"] * 2 + (df_charged["PWR"] / 10)
        df.loc[df["Categoría"] == "Charged Moves", "Score General"] = normalize_score(df_charged["Base_Score_Cargado"]).round(1)
    
    df["Score General"] = df["Score General"].fillna(0.0)
    df = df.drop(columns=["PWR/ENG"], errors='ignore') 
    
    cols_to_round = ["DPT", "EPT", "PWR", "ENG", "CD", "DPT/EPT"]
    for col in cols_to_round:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.1f}" if x != 0 and pd.notna(x) else ("0.0" if x == 0 else ""))


    # ----------------- REORDENAMIENTO FINAL DE COLUMNAS -----------------
    if not df.empty:
        
        desired_initial_cols = ["Name", "Efectos", "Prob. %", "Avg. Activ.", "DPT/EPT", "Score General", "Estadisticas", "Tipo", "Categoría", "DPT", "EPT", "PWR", "ENG", "CD"]
        
        current_cols = df.columns.tolist()
        remaining_cols = [col for col in current_cols if col not in desired_initial_cols]
        
        final_cols = [col for col in desired_initial_cols if col in current_cols]
        
        for col in remaining_cols:
             if col not in final_cols:
                 final_cols.append(col)
                 
        df = df[final_cols]
    
# ----------------- Inicializar app -----------------
app = dash.Dash(__name__)
server = app.server
app.title = "Movimientos Pokémon PvP"


# ----------------- Estilos Condicionales (Coloreado de Tabla de Movimientos) -----------------
NUMERIC_COLS_FOR_COLOR = ["Score General"]

style_data_conditional = [
    {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
]

for col_id in NUMERIC_COLS_FOR_COLOR:
    style_data_conditional.append({
        'if': {'column_id': col_id, 'filter_query': '{' + col_id + '} >= 7.0'},
        'backgroundColor': '#4CAF50', 
        'color': 'white',
        'fontWeight': 'bold'
    })
    style_data_conditional.append({
        'if': {'column_id': col_id, 'filter_query': '{' + col_id + '} >= 3.0 && {' + col_id + '} < 7.0'},
        'backgroundColor': '#FFC107', 
        'color': 'black'
    })
    style_data_conditional.append({
        'if': {'column_id': col_id, 'filter_query': '{' + col_id + '} > 0.0 && {' + col_id + '} < 3.0'},
        'backgroundColor': '#F8D7DA', 
        'color': '#721C24'
    })
    style_data_conditional.append({
        'if': {'column_id': col_id, 'filter_query': '{' + col_id + '} = 0.0'},
        'backgroundColor': '#ECECEC', 
        'color': '#808080'
    })

# ----------------- Componente Modal de Filtros (Existente) -----------------
filter_modal = html.Div(
    id="filter-modal",
    children=[
        html.Div(id="modal-background-filter", style={
            "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
            "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"
        }),
        html.Div(id="modal-content-filter", style={
            "position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)",
            "backgroundColor": "white", "padding": "25px", "borderRadius": "10px",
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "90%", "maxWidth": "600px",
            "zIndex": 1000, "display": "none"
        }, children=[
            html.H3("Ajustar Filtros de Movimientos", style={"marginBottom": "20px", "textAlign": "center"}),
            html.Div([
                html.Label("Filtrar por Categoría:", style={"fontWeight": "bold", "marginTop": "10px"}),
                dcc.Dropdown(
                    id="category-filter",
                    options=[{"label": c, "value": c} for c in df["Categoría"].unique()] if not df.empty else [],
                    multi=True, placeholder="Selecciona categoría...", value=None, style={"backgroundColor": "#f9f9f9"}
                )
            ], style={"marginBottom": "20px"}),
            html.Div([
                html.Label("Filtrar por Tipo:", style={"fontWeight": "bold"}),
                dcc.Dropdown(
                    id="type-filter",
                    options=[{"label": t, "value": t} for t in df["Tipo"].unique()] if not df.empty else [],
                    multi=True, placeholder="Selecciona tipo...", value=None, style={"backgroundColor": "#f9f9f9"}
                )
            ], style={"marginBottom": "20px"}), 
            html.Div([
                html.Label("Buscar Ataque por Nombre:", style={"fontWeight": "bold"}),
                dcc.Input(
                    id="name-search-filter", type="text", placeholder="Escribe el nombre del ataque",
                    style={"width": "100%", "padding": "10px", "borderRadius": "5px", "border": "1px solid #ccc"}
                )
            ], style={"marginBottom": "30px"}),
            html.Button("Cerrar", id="close-modal-button-filter", n_clicks=0,
                style={"backgroundColor": "#2ecc71", "color": "white", "border": "none", "padding": "10px 20px",
                    "borderRadius": "5px", "cursor": "pointer", "float": "right"}
            )
        ])
    ]
)


# ----------------- Componente Modal de Análisis de Pokémon (Doble Tipo) -----------------
pokemon_analysis_modal = html.Div(
    id="pokemon-analysis-modal",
    children=[
        html.Div(id="modal-background-analysis", style={
            "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
            "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"
        }),
        html.Div(id="modal-content-analysis", style={
            "position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)",
            "backgroundColor": "white", "padding": "25px", "borderRadius": "10px",
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "90%", "maxWidth": "700px",
            "zIndex": 1000, "display": "none"
        }, children=[
            html.H3("Análisis de Debilidades por Tipo", style={"marginBottom": "20px", "textAlign": "center"}),
            html.Div(style={"display": "flex", "gap": "20px", "marginBottom": "30px"}, children=[
                html.Div(style={"flex": 1}, children=[
                    html.Label("Tipo Primario:", style={"fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="type-primary-selector",
                        options=[{"label": t, "value": t} for t in POKEMON_TYPES],
                        placeholder="Selecciona Tipo 1...",
                        value="Normal"
                    )
                ]),
                html.Div(style={"flex": 1}, children=[
                    html.Label("Tipo Secundario (Opcional):", style={"fontWeight": "bold"}),
                    dcc.Dropdown(
                        id="type-secondary-selector",
                        options=[{"label": "Ninguno", "value": "Ninguno"}] + [{"label": t, "value": t} for t in POKEMON_TYPES],
                        placeholder="Selecciona Tipo 2...",
                        value="Ninguno"
                    )
                ]),
            ]),
            
            html.Div(id="analysis-output", children=[
                html.H4("Resultado del Análisis:", style={"borderBottom": "2px solid #eee", "paddingBottom": "10px"}),
                html.P("Selecciona al menos un tipo para ver las debilidades.", style={"color": "#7f8c8d"})
            ]),

            html.Button("Cerrar", id="close-modal-button-analysis", n_clicks=0,
                style={"backgroundColor": "#2ecc71", "color": "white", "border": "none", "padding": "10px 20px",
                    "borderRadius": "5px", "cursor": "pointer", "float": "right", "marginTop": "20px"}
            )
        ])
    ]
)

# ----------------- LÓGICA DE LA TABLA DE EFECTIVIDAD VISUAL (ACTUALIZADA) -----------------

# Estilo para las cabeceras de tipo (Defensa)
type_header_style = {
    'textAlign': 'center', 
    'fontWeight': 'bold', 
    'color': 'white', 
    'padding': '10px 5px',
    'borderRight': '1px solid #708090',
    'minWidth': '100px',
    'flexGrow': 1
}

# Generar filas de la tabla de tipos
def generate_type_chart_rows():
    rows = []
    
    # 1. Encabezado (Tipos de Ataque)
    header_cells = [
        html.Div("Defensa", style={**type_header_style, 'backgroundColor': '#2c3e50', 'borderRight': 'none', 'flexGrow': 0, 'minWidth': '120px'})
    ]
    for type_name in POKEMON_TYPES:
        header_cells.append(
            html.Div(
                create_type_icon(type_name),
                style={**type_header_style, 'backgroundColor': '#2c3e50', 'padding': '5px'}
            )
        )
    rows.append(html.Div(header_cells, className="type-chart-row", style={'display': 'flex', 'borderBottom': '3px solid #708090', 'backgroundColor': '#2c3e50'}))

    # 2. Filas de Datos (Tipos de Defensa)
    for defense_type in POKEMON_TYPES:
        row_cells = []
        
        # Celda de Tipo Defensivo (Primera columna, con fondo de color)
        defense_cell = html.Div(
            create_type_icon(defense_type),
            style={
                'minWidth': '120px', 
                'flexGrow': 0,
                'backgroundColor': TYPE_COLORS.get(defense_type), 
                'display': 'flex',
                'alignItems': 'center',
                'justifyContent': 'center',
                'borderRight': '3px solid #2c3e50',
                'padding': '5px'
            }
        )
        row_cells.append(defense_cell)
        
        # Celdas de Efectividad
        for attack_type in POKEMON_TYPES:
            # Obtener el multiplicador (1.0 por defecto)
            multiplier = TYPE_MATRIX_DATA.get(defense_type, {}).get(attack_type, 1.0)
            
            # Definir estilo y contenido basado en el multiplicador
            style = {'flexGrow': 1, 'textAlign': 'center', 'padding': '5px 0', 'minWidth': '50px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
            
            content = None # Por defecto no hay contenido (neutral 1.0)
            
            if multiplier >= 2.0:
                # Debilidad (x2, x4, etc.): Mostrar el tipo atacante
                # El fondo de la celda es ROJO
                style['backgroundColor'] = '#E74C3C' 
                content = create_type_icon(attack_type) 
            elif multiplier < 1.0 and multiplier > 0.0:
                # Resistencia (x0.5, x0.25): Mostrar el tipo atacante
                # El fondo de la celda es VERDE
                style['backgroundColor'] = '#2ECC71' 
                content = create_type_icon(attack_type) 
            elif multiplier == 0.0:
                # Inmunidad (x0): Mostrar el tipo atacante
                # El fondo de la celda es AZUL OSCURO
                style['backgroundColor'] = '#34495E' 
                content = create_type_icon(attack_type) 

            # Si el contenido es nulo (neutral), solo se aplica un color de fondo neutro
            if content is None:
                 style['backgroundColor'] = '#ECF0F1' # Gris muy claro
                 content = html.Span("1", style={'color': '#7f8c8d', 'fontWeight': 'bold'}) # Opcional: mostrar un "1" pequeño

            row_cells.append(html.Div(content, style=style))

        rows.append(html.Div(row_cells, className="type-chart-row", style={'display': 'flex', 'borderBottom': '1px solid #eee'}))

    return rows


# ----------------- Componente Modal de Tabla de Efectividad Global (ACTUALIZADO) -----------------
type_chart_modal = html.Div(
    id="type-chart-modal",
    children=[
        html.Div(id="modal-background-chart", style={
            "position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0,
            "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"
        }),
        html.Div(id="modal-content-chart", style={
            "position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)",
            "backgroundColor": "white", "padding": "25px", "borderRadius": "10px",
            "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "95%", "maxWidth": "1200px",
            "zIndex": 1000, "display": "none"
        }, children=[
            html.H3("Tabla de Efectividad de Tipos (Visual)", style={"marginBottom": "10px", "textAlign": "center", "color": "#2c3e50"}),
            html.P([
                "La fila es el ", html.Strong("Tipo Defensivo (recibe)."), " El tipo dentro de las celdas es el ", html.Strong("Tipo Atacante (golpea).")
            ], style={"textAlign": "center", "color": "#7f8c8d", "marginBottom": "10px"}),
            html.Div([
                html.Span("Fondo Rojo: Debilidad (x2/x4)", style={"color": "#E74C3C", "marginRight": "15px", "fontWeight": "bold"}),
                html.Span("Fondo Verde: Resistencia (x1/2/x1/4)", style={"color": "#2ECC71", "marginRight": "15px", "fontWeight": "bold"}),
                html.Span("Fondo Azul Oscuro: Inmunidad (x0)", style={"color": "#34495E", "marginRight": "15px", "fontWeight": "bold"}),
                html.Span("Fondo Gris Claro: Neutral (x1)", style={"color": "#7f8c8d", "fontWeight": "bold"}),
            ], style={"textAlign": "center", "marginBottom": "20px", "fontSize": "12px"}),
            
            # Contenedor para la tabla generada dinámicamente
            html.Div(
                generate_type_chart_rows(),
                id="type-effectiveness-visual-chart",
                style={"overflowX": "auto", "overflowY": "hidden", "border": "2px solid #2c3e50", "borderRadius": "8px"}
            ),
            
            html.Button("Cerrar", id="close-modal-button-chart", n_clicks=0,
                style={"backgroundColor": "#2ecc71", "color": "white", "border": "none", "padding": "10px 20px",
                    "borderRadius": "5px", "cursor": "pointer", "float": "right", "marginTop": "20px"}
            )
        ])
    ]
)


# ----------------- Layout Principal -----------------
app.layout = html.Div([
    
    html.H1("Movimientos Pokémon PvP", style={"textAlign": "center", "marginBottom": "20px", "color": "#2c3e50"}),

    # Almacenamiento invisible para controlar el estado del modal de Filtros
    dcc.Store(id='modal-state-filter', data={'is_open': False, 'category': None, 'type': None, 'search': None}),
    # Almacenamiento invisible para controlar el estado del modal de Tipos
    dcc.Store(id='modal-state-chart', data={'is_open': False}),
    # Almacenamiento invisible para controlar el estado del modal de Análisis
    dcc.Store(id='modal-state-analysis', data={'is_open': False}),


    # Botones para los Modales
    html.Div([
        html.Button(
            "Aplicar Filtros", 
            id="open-modal-button-filter", n_clicks=0,
            style={"backgroundColor": "#3498db", "marginRight": "10px"}
        ),
        html.Button(
            "Tabla Global de Tipos (Visual)", 
            id="open-modal-button-chart", n_clicks=0,
            style={"backgroundColor": "#8e44ad", "marginRight": "10px"}
        ),
        html.Button(
            "Análisis de Debilidades", 
            id="open-modal-button-analysis", n_clicks=0,
            style={"backgroundColor": "#e67e22"}
        ),
    ], style={
        "textAlign": "center", 
        "marginBottom": "20px",
        "display": "flex",
        "justifyContent": "center"
    }),
    
    # Estilos comunes para los botones
    html.Br(),
    html.P("Click en la tabla para ordenar o usar los filtros en el modal.", style={"textAlign": "center", "color": "#7f8c8d"}),
    html.Br(),
    
    html.Div(id='active-filters-summary', style={'textAlign': 'center', 'marginBottom': '15px', 'color': '#7f8c8d'}),


    # Tabla de Datos
    dash_table.DataTable(
        id="moves-table",
        columns=[{"name": i, "id": i} for i in df.columns] if not df.empty else [],
        data=df.to_dict("records") if not df.empty else [],
        filter_action="native",
        sort_action="native",
        page_size=20,
        style_table={"overflowX": "auto", "border": "1px solid #ddd", "borderRadius": "8px"},
        style_cell={"textAlign": "left", "padding": "12px", "fontFamily": "sans-serif"},
        style_header={
            "backgroundColor": "#3498db", 
            "color": "white",
            "fontWeight": "bold",
            "borderBottom": "2px solid #2980b9"
        },
        style_data_conditional=style_data_conditional
    ),
    
    # Modales
    filter_modal,
    type_chart_modal,
    pokemon_analysis_modal
])


# ----------------- CALLBACKS GENERALES PARA CONTROL DE MODALES -----------------

# Callback para Modal de Filtros (EXISTENTE)
@app.callback(
    [
        Output("modal-background-filter", "style"),
        Output("modal-content-filter", "style"),
        Output("modal-state-filter", "data"),
        Output("category-filter", "value"),
        Output("type-filter", "value"),
        Output("name-search-filter", "value"),
    ],
    [
        Input("open-modal-button-filter", "n_clicks"),
        Input("close-modal-button-filter", "n_clicks"),
    ],
    [
        State("modal-state-filter", "data"),
        State("category-filter", "value"),
        State("type-filter", "value"),
        State("name-search-filter", "value"),
    ],
)
def toggle_modal_filter(open_n, close_n, current_state, cat_val, type_val, search_val):
    ctx = dash.callback_context
    default_bg_style = {"position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0, "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"}
    default_content_style = {"position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)", "backgroundColor": "white", "padding": "25px", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "90%", "maxWidth": "600px", "zIndex": 1000, "display": "none"}
    
    if not ctx.triggered:
        return (default_bg_style, default_content_style, current_state, current_state['category'], current_state['type'], current_state['search'])
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "open-modal-button-filter" and open_n > 0:
        open_bg_style = default_bg_style.copy()
        open_bg_style["display"] = "block"
        open_content_style = default_content_style.copy()
        open_content_style["display"] = "block"
        return (open_bg_style, open_content_style, current_state, current_state['category'], current_state['type'], current_state['search'])
    
    elif button_id == "close-modal-button-filter" and close_n > 0:
        new_state = {'is_open': False, 'category': cat_val, 'type': type_val, 'search': search_val}
        return (default_bg_style, default_content_style, new_state, cat_val, type_val, search_val)
        
    return (default_bg_style, default_content_style, current_state, current_state['category'], current_state['type'], current_state['search'])

# Callback para Modal de Tabla de Efectividad Global
@app.callback(
    [
        Output("modal-background-chart", "style"),
        Output("modal-content-chart", "style"),
        Output("modal-state-chart", "data"),
    ],
    [
        Input("open-modal-button-chart", "n_clicks"),
        Input("close-modal-button-chart", "n_clicks"),
    ],
    [State("modal-state-chart", "data")],
)
def toggle_modal_chart(open_n, close_n, current_state):
    ctx = dash.callback_context
    default_bg_style = {"position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0, "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"}
    default_content_style = {"position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)", "backgroundColor": "white", "padding": "25px", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "95%", "maxWidth": "1200px", "zIndex": 1000, "display": "none"}
    
    if not ctx.triggered:
        return (default_bg_style, default_content_style, current_state)
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "open-modal-button-chart" and open_n > 0:
        open_bg_style = default_bg_style.copy()
        open_bg_style["display"] = "block"
        open_content_style = default_content_style.copy()
        open_content_style["display"] = "block"
        new_state = {'is_open': True}
        return (open_bg_style, open_content_style, new_state)
    
    elif button_id == "close-modal-button-chart" and close_n > 0:
        new_state = {'is_open': False}
        return (default_bg_style, default_content_style, new_state)
        
    return (default_bg_style, default_content_style, current_state)


# Callback para Modal de Análisis de Debilidades
@app.callback(
    [
        Output("modal-background-analysis", "style"),
        Output("modal-content-analysis", "style"),
        Output("modal-state-analysis", "data"),
    ],
    [
        Input("open-modal-button-analysis", "n_clicks"),
        Input("close-modal-button-analysis", "n_clicks"),
    ],
    [State("modal-state-analysis", "data")],
)
def toggle_modal_analysis(open_n, close_n, current_state):
    ctx = dash.callback_context
    default_bg_style = {"position": "fixed", "top": 0, "left": 0, "right": 0, "bottom": 0, "backgroundColor": "rgba(0, 0, 0, 0.5)", "zIndex": 999, "display": "none"}
    default_content_style = {"position": "fixed", "top": "50%", "left": "50%", "transform": "translate(-50%, -50%)", "backgroundColor": "white", "padding": "25px", "borderRadius": "10px", "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.2)", "width": "90%", "maxWidth": "700px", "zIndex": 1000, "display": "none"}
    
    if not ctx.triggered:
        return (default_bg_style, default_content_style, current_state)
    
    button_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if button_id == "open-modal-button-analysis" and open_n > 0:
        open_bg_style = default_bg_style.copy()
        open_bg_style["display"] = "block"
        open_content_style = default_content_style.copy()
        open_content_style["display"] = "block"
        new_state = {'is_open': True}
        return (open_bg_style, open_content_style, new_state)
    
    elif button_id == "close-modal-button-analysis" and close_n > 0:
        new_state = {'is_open': False}
        return (default_bg_style, default_content_style, new_state)
        
    return (default_bg_style, default_content_style, current_state)


# ----------------- CALLBACK ESPECÍFICO DE ANÁLISIS DE TIPOS -----------------
@app.callback(
    Output("analysis-output", "children"),
    [
        Input("type-primary-selector", "value"),
        Input("type-secondary-selector", "value"),
    ]
)
def update_analysis_output(type1, type2):
    if not type1 or type1 == "Ninguno":
        return html.P("Selecciona al menos un tipo primario.", style={"color": "#7f8c8d"})

    debilidades, resistencias, inmunidades = calculate_effectiveness(type1, type2)

    return html.Div([
        html.H4(f"Análisis para el Tipo {type1}{f'/{type2}' if type2 and type2 != 'Ninguno' else ''}:", style={"marginBottom": "15px"}),

        html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))", "gap": "20px"}, children=[
            # Debilidades
            html.Div(style={"border": "2px solid #e74c3c", "padding": "15px", "borderRadius": "8px", "backgroundColor": "#fdeded"}, children=[
                html.H5("❌ Debilidades", style={"color": "#e74c3c", "marginBottom": "10px"}),
                render_type_list(debilidades)
            ]),
            
            # Resistencias
            html.Div(style={"border": "2px solid #2ecc71", "padding": "15px", "borderRadius": "8px", "backgroundColor": "#e8f8f5"}, children=[
                html.H5("✅ Resistencias", style={"color": "#2ecc71", "marginBottom": "10px"}),
                render_type_list(resistencias)
            ]),
            
            # Inmunidades
            html.Div(style={"border": "2px solid #34495e", "padding": "15px", "borderRadius": "8px", "backgroundColor": "#eaeded"}, children=[
                html.H5("🚫 Inmunidades (x0.00)", style={"color": "#34495e", "marginBottom": "10px"}),
                render_type_list(inmunidades)
            ]),
        ])
    ])


# ----------------- CALLBACK para filtrar tabla (AHORA USA Dcc.Store de Filtros) -----------------
@app.callback(
    [
        Output("moves-table", "data"),
        Output("active-filters-summary", "children"),
    ],
    [
        Input("modal-state-filter", "data"),
    ],
)
def update_table(modal_data):
    if df.empty:
        return [], "No se encontraron datos para filtrar."
    
    selected_categories = modal_data['category']
    selected_types = modal_data['type']
    search_term = modal_data['search']
    
    filtered = df.copy()
    summary_parts = []
    
    # 1. Filtrar por Categoría
    if selected_categories and selected_categories != []:
        filtered = filtered[filtered["Categoría"].isin(selected_categories)]
        summary_parts.append(f"Categoría: {', '.join(selected_categories)}")
        
    # 2. Filtrar por Tipo
    if selected_types and selected_types != []:
        filtered = filtered[filtered["Tipo"].isin(selected_types)]
        summary_parts.append(f"Tipo: {', '.join(selected_types)}")

    # 3. Filtrar por Nombre (Texto Libre)
    if search_term:
        try:
            filtered = filtered[
                filtered["Name"].astype(str).str.contains(search_term, case=False, na=False, regex=True)
            ]
            summary_parts.append(f"Búsqueda: '{search_term}'")
        except re.error:
            filtered = filtered[
                filtered["Name"].astype(str).str.contains(search_term, case=False, na=False)
            ]
            summary_parts.append(f"Búsqueda: '{search_term}' (simple)")

    if summary_parts:
        summary_message = "Filtros Activos: " + " | ".join(summary_parts)
    else:
        summary_message = "No hay filtros activos. Mostrando todos los movimientos."

    return filtered.to_dict("records"), summary_message

# ----------------- Ejecutar app -----------------
if __name__ == "__main__":
    app.run(debug=True)
