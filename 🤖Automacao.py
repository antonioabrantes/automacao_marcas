# https://share.streamlit.io/
# https://faleconosco.streamlit.app/
# https://github.com/antonioabrantes/automacao_marcas

import streamlit as st
import PyPDF2
import re, os, io
from langchain_groq import ChatGroq
from dotenv import load_dotenv

st.set_page_config(page_title="Resumo de Petição do INPI", layout="wide")
st.title("📄 Resumo de Petição da COREM")

load_dotenv() 
groq_api_key = os.getenv("GROQ_API_KEY")
llm = ChatGroq(model="openai/gpt-oss-20b",temperature=0.2, max_tokens=1024)

def extrair_argumentacao_siscap(texto):
    """
    Extrai apenas a parte argumentativa típica de recursos do INPI
    """
    texto = texto.replace("\n", " ")

    padrao_inicio = re.compile(
        r"(Recurso contra o indeferimento|DOS ARGUMENTOS)",
        re.IGNORECASE
    )

    padrao_fim = re.compile(
        r"(CONSIDERAÇÕES FINAIS|CONCLUSÃO)",
        re.IGNORECASE
    )

    inicio = padrao_inicio.search(texto)
    fim = padrao_fim.search(texto)

    if inicio:
        start_idx = inicio.start()
        end_idx = fim.start() if fim else len(texto)
        return texto[start_idx:end_idx].strip()
    else:
        return "⚠️ Não foi possível identificar automaticamente a seção de argumentação."

def extrair_argumentacao_ipas(texto: str) -> str:
    """
    Extrai apenas a argumentação do requerente em petições do INPI,
    removendo dados pessoais e partes administrativas iniciais.
    """

    if not texto or not texto.strip():
        return ""

    # Normaliza espaços
    texto = re.sub(r'\n{2,}', '\n\n', texto)

    # Padrões que indicam início da argumentação
    padrao_inicio = re.compile(
        r"(ILMO\s+SENHOR\s+PRESIDENTE\s+DO\s+INPI|"
        r"DOS\s+FATOS|"
        r"DO\s+DIREITO|"
        r"DAS\s+RAZÕES)",
        re.IGNORECASE
    )

    match = padrao_inicio.search(texto)

    if match:
        texto_filtrado = texto[match.start():]
        return texto_filtrado.strip()

    # Se nenhum marcador for encontrado, retorna texto inteiro (fallback)
    return texto.strip()

def ler_pdf_pypdf2(pdf_bytes):
    """
    Lê PDF textual usando PyPDF2 e retorna o texto completo
    """
    leitor = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    texto = ""

    for i, pagina in enumerate(leitor.pages):
        texto_pagina = pagina.extract_text()
        if texto_pagina:
            texto += f"\n\n--- Página {i+1} ---\n{texto_pagina}"

    return texto
    


uploaded_file = st.file_uploader("Faça upload do PDF da petição", type=["pdf"])

if uploaded_file:
    st.info("🔍 Processando OCR do PDF, aguarde...")

    pdf_bytes = uploaded_file.read()
    
    #texto_ocr = ocr_pdf(pdf_bytes)
    #argumentacao = extrair_argumentacao_siscap(texto_ocr)

    texto_pdf = ler_pdf_pypdf2(pdf_bytes)
    argumentacao = extrair_argumentacao_ipas(texto_pdf)
    st.write("Tamanho original do arquivo:", len(argumentacao))
    MAX_CHARS = 24000
    #argumentacao = argumentacao[:MAX_CHARS]

    st.subheader("🧠 Argumentação do Requerente (extraída automaticamente)")
    st.text_area(
        label="Conteúdo filtrado",
        value=argumentacao,
        height=500
    )

    with st.expander("📜 Ver texto completo do OCR"):
        st.text_area(
            label="Texto integral",
            value=texto_pdf,
            height=400
        )
        
    question = f"Resuma a argumentação do recurso: {argumentacao}"
    messages=[{"role":"user", "content":question}]
    response = llm.invoke(messages)
    st.subheader("🧠 Resumo da petição")
    st.write(response.content)