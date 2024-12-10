import streamlit as st
import tempfile
import json
import os
from PyPDF2 import PdfReader
import time
import requests
import fitz
import io

# Función para inicializar claves en st.session_state
def initialize_votes_state(analysis_idx, paragraph_idx, voter_name):

    key_vote = f"{voter_name}_vote_{analysis_idx}_{paragraph_idx}"

    if key_vote not in st.session_state:
        st.session_state[key_vote] = None  # Ningun voto inicialmente

    return key_vote

# Transformar JSON
def transform_json(input_json):
    transformed_data = {
        "paper_title": input_json.get("paper_title", "Not available"),
        "DOI": input_json.get("DOI", "Not available"),
        "analysis": []
    }

    # Recorrer los resultados del análisis
    for result in input_json.get("result", []):
        question_category = result.get("question_category", "Unknown Category")
        selected_answer_dict = result.get("selected_answer", {})
        
        # Manejo de claves en `selected_answer` para buscar la respuesta
        selected_answer = "Not available"
        for key, value in selected_answer_dict.items():
            if question_category.replace(" ", "_").lower() in key.lower():
                selected_answer = value.strip()
                break

        evidences = result.get("evidences", [])

        # Añadir la información procesada
        transformed_data["analysis"].append({
            "question_category": question_category,
            "selected_answer": selected_answer,
            "evidences": evidences
        })

    return transformed_data

# Página JSON

def json_page():
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 13, 1])
    with col2:
        st.image("https://github.com/oeg-upm/solar-qa-ui/web/images/logo_pg.png", width=600)

    st.markdown("<h2 style='text-align: center;'>JSON INFORMATION</h2>", unsafe_allow_html=True)

    uploaded_json = st.file_uploader("Upload JSON file", type="json")

    if uploaded_json is not None:
        try:
            json_content = json.load(uploaded_json)
            transformed_json = transform_json(json_content)

            # Solicitar nombre del usuario
            st.markdown("### Please enter your name to continue:")
            voter_name = st.text_input("Enter your name:")

            if voter_name:
                st.success(f"Welcome, {voter_name}! You can now cast your votes.")

                # Información general del documento
                with st.expander("Paper Information"):
                    st.markdown(f"""
                        <h4 style='color:#333;'>TITLE:</h4>
                        <p style='font-size:16px; color:#555;'>{transformed_json['paper_title']}</p>
                        <h4 style='color:#333;'>DOI:</h4>
                        <p style='font-size:16px; color:#555;'>{transformed_json['DOI']}</p>
                        """, unsafe_allow_html=True)

                if "analysis" in transformed_json:
                    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)  
                    st.subheader("Answers found in the PDF")
                    st.write("Below are the answers our system found in the input PDF. You will see the answers divided in 5 tables: catalyst, co-catalyst, light_source, lamp, reaction_medium, reactor_type and operation_mode. Each answer has the five most relevant paragraphs the system found in the paper. Please vote for each paragraph (up or down) whether the target text has the right answer for the corresponding category.")
                    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)  

                    for analysis_idx, analysis in enumerate(transformed_json["analysis"]):
                        # Mostrar categoría y tipo directamente con formato
                        category = analysis.get('question_category', 'Unknown Category').capitalize()
                        selected_answer = analysis.get('selected_answer', 'Not available')

                        # Mostrar con formato mejorado
                        st.markdown(
                            f"<p style='font-size:14px;'><strong>{category}:</strong> <span style='font-weight:normal;'>{selected_answer}</span></p>",
                            unsafe_allow_html=True
                        )

                        # Crear expander para evidencias
                        with st.expander("View Evidence Details"):
                            for evidence_idx, evidence in enumerate(analysis.get("evidences", [])):
                                pdf_reference = evidence.get("pdf_reference", "Not available")

                                # Inicializar estado de votos
                                key_vote = f"{voter_name}_vote_{analysis_idx}_{evidence_idx}"
                                if key_vote not in st.session_state:
                                    st.session_state[key_vote] = None

                                # Mostrar evidencia
                                st.markdown(f"<p style='font-size:14px;'><strong>PDF Reference:</strong> {pdf_reference}</p>", unsafe_allow_html=True)

                                # Botones de votación
                                col1, col2 = st.columns([8, 2])
                                with col2:
                                    upvote_disabled = st.session_state[key_vote] == "Positive"
                                    downvote_disabled = st.session_state[key_vote] == "Negative"

                                    if st.button("↑", key=f"{voter_name}_button_up_{analysis_idx}_{evidence_idx}", disabled=upvote_disabled):
                                        st.session_state[key_vote] = "Positive"

                                    if st.button("↓", key=f"{voter_name}_button_down_{analysis_idx}_{evidence_idx}", disabled=downvote_disabled):
                                        st.session_state[key_vote] = "Negative"

                                # Guardar voto
                                evidence["votes"] = {
                                    "Voter": voter_name,
                                    "Vote": st.session_state[key_vote]
                                }

                    # Descargar JSON actualizado
                    st.markdown("### Download Updated JSON")
                    updated_json_data = json.dumps(transformed_json, indent=4)
                    st.download_button(
                        label="Download JSON",
                        data=updated_json_data,
                        file_name=f"{voter_name}_updated.json",
                        mime="application/json"
                    )
            else:
                st.warning("Please enter your name to enable voting.")
        except Exception as e:
            st.error(f"Error loading JSON file: {e}")


    
    # Agregar espacio antes del pie de página
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)    

    st.markdown("---")
    st.markdown("""
    <div style='text-align: center;'>
        <a href="https://github.com/oeg-upm/solar-qa" style="text-decoration: none;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg" alt="GitHub Logo" width="18" style="vertical-align: middle;"/>
        https://github.com/oeg-upm/solar-qa
        </a> | CLI Version: 1 | © 2024 SolarChem
    </div>
    """, unsafe_allow_html=True)

    # Crear una columna para centrar la imagen
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col2:
        st.image("images/logo_uni.png", width=150)

# Cargamos el JSON automaticamente
def load_json_automatically(json_path):
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            query_data = json.load(f)
        #st.write("Archivo JSON cargado automáticamente.")
        return query_data
    else:
        st.error(f"El archivo JSON no se encontró en la ruta: {json_path}")
        return None

# Pagina principal
def main_page():

    # Agregar espacio
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 13, 1])
    with col2:
        st.image("images/logo_pg.png", width=600)

    #Mostrar imagen con logo pero sin columna
    #st.image("images/logo_pg.png", width=600)

    # Agregar espacio
    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)

    # Cargar archivo JSON de configuración
    json_path = "prompts.json"  # Usa una ruta relativa
    query_data = load_json_automatically(json_path)

    # Cargar el archivo PDF
    uploaded_pdf = st.file_uploader("Sube tu archivo PDF", type="pdf")
    
    # Verificar si se ha subido un archivo y si se ha presionado el botón Submit
    if uploaded_pdf is not None and st.button("Submit"):
        with st.spinner('Analyzing your paper... Please be patient'):
            try:
                # Crear un diccionario de argumentos
                args_dict = {
                    "use_platform": "True",
                    "user_key": "",
                    "llm_id": "llama3-groq-8b-8192-tool-use-preview",
                    "hf_key": "",
                    "llm_platform": "groq",
                    "sim_model_id": "Salesforce/SFR-Embedding-Mistral",
                    "input_file_path": uploaded_pdf.name,
                    "prompt_file_pdf": json_path,
                    "context_file_path": "context_result.json"
                }
                
                # Enviar solicitud al backend
                response = requests.post("http://127.0.0.1:8000/analysis/", json=args_dict)
                
                # Verificar si la respuesta fue exitosa
                if response.status_code == 200:
                    result = response.json()["result"]
                    context = response.json()["context"]
                    
                    st.write("Respuesta completa del backend:", context)

                    # Mostrar Resultados Principales
                    if result:
                        st.subheader("Análisis - Resultados Principales")
                        st.write("Catalyst: " + str(result.get("catalyst", "No disponible")))
                        st.write("Co_catalyst: " + str(result.get("co_catalyst", "No disponible")))
                        st.write("Light_source: " + str(result.get("Light_source", "No disponible")))
                        st.write("Lamp: " + str(result.get("Lamp", "No disponible")))
                        st.write("Reaction_medium: " + str(result.get("Reaction_medium", "No disponible")))
                        st.write("Reactor_type: " + str(result.get("Reactor_type", "No disponible")))
                        st.write("Operation_mode: " + str(result.get("Operation_mode", "No disponible")))

                        # Mostrar el modelo utilizado
                        #generation_model = response.json().get("generation_model", "No disponible")
                        #st.markdown(f"**Modelo utilizado:** {generation_model}")

                    # Mostrar Evidencias Detalladas con el formato específico
                    st.subheader("Evidencias Detalladas")
                    
                    evidencias = context.get("result", [])  # Lista de evidencias
                    
                    titulos = [
                        "Catalyst: Tipo " + str(result.get("catalyst", "No disponible")) + 
                        " | Co_catalyst: Tipo " + str(result.get("co_catalyst", "No disponible")),
                        "Light_source: Tipo " + str(result.get("Light_source", "No disponible")) + 
                        " | Lamp: Tipo " + str(result.get("Lamp", "No disponible")),
                        "Reaction_medium: Tipo " + str(result.get("Reaction_medium", "No disponible")),
                        "Reactor_type: Tipo " + str(result.get("Reactor_type", "No disponible")),
                        "Operation_mode: Tipo " + str(result.get("Operation_mode", "No disponible"))
                    ]

                    for idx, evidence_entry in enumerate(evidencias):
                        if idx < len(titulos):
                            expander_title = titulos[idx]
                        else:
                            expander_title = "Evidencia {}".format(idx + 1)
                        
                        with st.expander(expander_title):
                            for e_idx, detalle in enumerate(evidence_entry.get("evidence", [])):
                                pdf_reference = detalle.get("pdf_reference", "No disponible")
                                #similarity_score = detalle.get("similarity_score", "No disponible")
                                
                                st.markdown(f"**Párrafo {e_idx + 1}**")
                                #st.markdown(f"- **Puntuación de Similitud:** `{similarity_score}`")
                                st.markdown(f"- **Referencia del PDF:** {pdf_reference}")
                                st.markdown("---")
                else:
                    st.error("Error al procesar el PDF.")
                    st.write("Respuesta del servidor:", response.text)
            except Exception as e:
                st.error(f"Error al conectar con el backend: {e}")

    # Agregar espacio antes del pie de página
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center;'>
        <a href="https://github.com/oeg-upm/solar-qa" style="text-decoration: none;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg" alt="GitHub Logo" width="18" style="vertical-align: middle;"/>
        https://github.com/oeg-upm/solar-qa
        </a> | CLI Version: 1 | © 2024 SolarChem
    </div>
    """, unsafe_allow_html=True)

    # Crear una columna para centrar la imagen
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col2:
        st.image("images/logo_uni.png", width=150)

# About page
def about_page():

    # Agregar espacio
    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 13, 1])
    with col2:
        st.image("images/logo_pg.png", width=600)
    
    #st.image("images/logo_pg.png", width=600)

    
    st.markdown("<h2 style='text-align: center;'>ABOUT</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(
        """
        <div style="max-width: 800px; margin: 0 auto; padding: 50px 20px;">
            <p style="font-size: 1.2em; text-align: justify; line-height: 1.6;">
                Solarchem is an innovative platform designed to leverage artificial intelligence for the analysis of scientific papers in chemistry. 
                Our mission is to provide researchers, students, and professionals with an efficient way to extract key insights from academic documents 
                by automating the process of answering questions and highlighting relevant information.
            </p>
            <p style="font-size: 1.2em; text-align: justify; line-height: 1.6;">
                We use two advanced AI models based on Retrieval-Augmented Generation (RAG): a generation model and a similarity model. 
                These models process scientific PDFs, answering key questions about methodologies, findings, and more. 
                Each answer is linked to the specific paragraph in the document, ensuring accuracy and transparency. 
                Additionally, we provide a highlighted version of the PDF, marking relevant sections. Users can download this annotated PDF for future reference.
            </p>
            <h2 style="text-align: center; font-size: 2em; font-family: 'Arial', sans-serif; font-weight: bold;">How It Works</h2>
            <p style="font-size: 1.2em; text-align: justify; line-height: 1.6;">
                On our website, you first upload a PDF, which is processed using AI to generate key answers. 
                You will then receive evidence for these answers, with the option to download the PDF with the relevant sections highlighted or a JSON file containing the extracted data.
            </p>
            <p style="font-size: 1em; font-weight: bold;">
                Developed by: This website was carefully crafted by Alexandra Faje.
            </p>
            <p style="font-size: 1em; font-weight: bold;">
                Powered by: The platform is hosted and maintained by Clark Wang, Erick Cedeño, Ana Iglesias and Daniel Garijo, ensuring top-tier performance, security, and reliability.
            </p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    st.markdown("---")

    st.markdown("""
    <div style='text-align: center;'>
        <a href="https://github.com/oeg-upm/solar-qa" style="text-decoration: none;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/9/91/Octicons-mark-github.svg" alt="GitHub Logo" width="18" style="vertical-align: middle;"/>
        https://github.com/oeg-upm/solar-qa
        </a> | CLI Version: 1 | © 2024 SolarChem
    </div>
    """, unsafe_allow_html=True)

    # Crear una columna para centrar la imagen
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
    with col2:
        st.image("images/logo_uni.png", width=150)


# Función principal para gestionar las páginas
def main():
    if "page" not in st.session_state:
        st.session_state.page = "Home"

    # Barra de navegación con botones en línea
    col1, col2, col3, col4 = st.columns([5, 1, 1, 1])
    with col2:
        if st.button("Home", key="home_button"):
            st.session_state.page = "Home"
    with col3:
        if st.button("JSON", key="json_button"):
            st.session_state.page = "Json"
    with col4:
        if st.button("About", key="about_button"):
            st.session_state.page = "About"

    # Cargar la página seleccionada
    if st.session_state.page == "Home":
        main_page()
    elif st.session_state.page == "About":
        about_page()
    elif st.session_state.page == "Json":
        json_page()

if __name__ == "__main__":
    main()
    
