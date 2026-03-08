import os
import json
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.exceptions import OutputParserException

# 1. Traer nuestros esquemas estrictos de Pydantic
from agents.schemas.profiling_schema import CompetencyProfile

# Cargar las variables de entorno de la raíz (el .env que metiste en el gitignore)
load_dotenv()

# Rutas estáticas para leer la Taxonomía oficial y nuestro Prompt de RRHH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAXONOMY_PATH = os.path.join(BASE_DIR, "agents", "data", "competencies.json")
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "profiling_prompt.txt")

def _load_taxonomy_str() -> str:
    """Lee el diccionario oficial de 25 competencias para dárselo a leer al LLM."""
    try:
        with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error al leer la taxonomía: {e}")
        return "{}"

def _load_system_prompt() -> str:
    """Lee las instrucciones estrictas del archivo de texto."""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error al leer el prompt: {e}")
        return "You are a helpful assistant."

def generate_cognitive_profile(user_answers_json: str, original_user_id: str) -> dict:
    """
    Función Principal del Agente 1 (Profiling).
    Convierte el ruido del formulario web en un JSON perfecto usando Inteligencia Artificial.
    """
    
    # 2. Configurar el "Cerebro" 
    # Usamos LLaMA 3 8B en Groq para inferencia ultrarrápida. 
    # GUARDARRAÍL 1: Temperatura 0.1 para que no invente historias ni se ponga creativo.
    llm = ChatGroq(
        model="llama3-8b-8192",
        temperature=0.1,
        max_retries=2 # Si falla por red, Groq lo intenta solo 2 veces más
    )
    
    # 3. Forzar el Output a la estructura de Pydantic
    # GUARDARRAÍL 2: Langchain inyectará aquí detrás las reglas exactas de nuestro schema.
    structured_llm = llm.with_structured_output(CompetencyProfile)
    
    # 4. Construir la Plantilla del Diálogo
    system_instructions = _load_system_prompt()
    taxonomy_data = _load_taxonomy_str()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instructions),
        ("system", f"OFFICIAL COMPETENCY TAXONOMY JSON:\n{taxonomy_data}"),
        ("human", "Analiza este formulario de usuario y devuélveme mi perfil JSON.\nUser_Id={user_id}\nRaw_Answers:\n{raw_answers}")
    ])
    
    # 5. Unir la tubería (Prompt -> IA con Pydantic)
    profiling_chain = prompt | structured_llm
    
    print(f"🕵️ Iniciando Análisis Cognitivo para el usuario: {original_user_id}...")
    
    # 6. Lanzar la Inferencia e invocar al LLM
    try:
        # Aquí es donde ocurre la magia (y donde gastamos tokens de la API)
        response_model = profiling_chain.invoke({
            "user_id": original_user_id,
            "raw_answers": user_answers_json
        })
        
        # Como usamos un modelo Pydantic, la IA ya nos devuelve un Objeto Python nativo
        # Para dárselo a tu compañero del Backend de vuelta, lo volvemos un diccionario Python (JSON format)
        return response_model.model_dump()
        
    except OutputParserException as e:
        # GUARDARRAÍL 3: Si el LLM se ha vuelto loco y no ha devuelto un JSON válido.
        print(f"❌ Error FATAL del Agente: El LLM desobedeció y no devolvió un JSON matemático.\n{e}")
        return {"error": "El Agente de Perfilado no pudo estructurar los datos del usuario."}
    except Exception as e:
        # GUARDARRAÍL 4: Si se cae nuestra API Key de Groq o no hay Internet.
        print(f"❌ Error de Sistema del Agente API Groq: {e}")
        return {"error": "Servicio de análisis cognitivo caído en este momento."}

# ==========================================
# Zona de Pruebas Rápidas al ejecutar el archivo directamente
# ==========================================
if __name__ == "__main__":
    
    # Un JSON de prueba artificial como si el frontend (Rol 3) se lo hubiera enviado a la API (Rol 1)
    mock_frontend_answers = json.dumps({
        "q1_role": "Soy programadora frontend hace un par de años.",
        "q2_skills": "Sé maquetar muy bien, pero he empezado a tocar bases de datos este año y solo sé que es un SELECT básico en SQL. De python no tengo ni idea.",
        "q3_goal": "Mi objetivo es convertirme en Data Engineer el año que viene."
    }, ensure_ascii=False)
    
    test_user = "usr_999_test"
    
    print("\n--- INVOCANDO AL AGENTE 1 ---\n")
    final_output = generate_cognitive_profile(user_answers_json=mock_frontend_answers, original_user_id=test_user)
    
    print("\n✅ OUTPUT FINAL VALIDADO DEL AGENTE 1:")
    print(json.dumps(final_output, indent=2, ensure_ascii=False))
