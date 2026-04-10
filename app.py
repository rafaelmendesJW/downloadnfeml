import re
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

import requests
import streamlit as st


BASE_URL = "https://www.mercadolivre.com.br/emissor/relatorios/api/document"
REQUEST_TIMEOUT_SECONDS = 30


def build_url(invoice_number: str) -> str:
    return f"{BASE_URL}/{invoice_number}/xml"


def normalize_invoice_number(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def validate_xml(content: bytes, content_type: str) -> Optional[str]:
    if not content.strip():
        return "A API retornou conteudo vazio."

    if "text/html" in (content_type or "").lower():
        return "A resposta veio como HTML em vez de XML."

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return f"O arquivo retornado nao e um XML valido: {exc}"

    root_tag = root.tag.lower()
    if root_tag == "html" or root_tag.endswith("html"):
        return "A resposta recebida e HTML, nao XML."

    return None


def build_response_diagnostics(response: requests.Response) -> str:
    redirects = []
    for item in response.history:
        location = item.headers.get("Location", "sem Location")
        redirects.append(f"{item.status_code}->{location}")

    redirect_info = " | ".join(redirects) if redirects else "sem redirecionamento"
    location_header = response.headers.get("Location", "nao informado")
    content_type = response.headers.get("Content-Type", "nao informado")

    return (
        f"status_final={response.status_code}; "
        f"url_final={response.url}; "
        f"content_type={content_type}; "
        f"location_header={location_header}; "
        f"redirects={redirect_info}"
    )


def fetch_xml(invoice_number: str) -> Tuple[Optional[bytes], Optional[str]]:
    url = build_url(invoice_number)
    headers = {
        "Accept": "application/xml, text/xml, */*",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.mercadolivre.com.br/",
    }

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException as exc:
        return None, f"Erro de conexao ao consultar a API: {exc}"

    if response.status_code != 200:
        diagnostics = build_response_diagnostics(response)
        return (
            None,
            f"Nao foi possivel baixar a nota. URL original: {url}. Diagnostico: {diagnostics}",
        )

    xml_error = validate_xml(
        content=response.content,
        content_type=response.headers.get("Content-Type", ""),
    )
    if xml_error:
        preview = response.text[:300].replace("\n", " ").strip()
        diagnostics = build_response_diagnostics(response)
        return None, f"{xml_error} Diagnostico: {diagnostics}. Trecho inicial: {preview}"

    return response.content, None


st.set_page_config(page_title="Download XML NFe", layout="centered")
st.title("Download XML de Nota Fiscal")
st.write("Informe o numero da nota para baixar o XML.")

invoice_input = st.text_input("Numero da nota", placeholder="Ex.: 5845581252")

if st.button("Baixar XML", type="primary"):
    invoice_number = normalize_invoice_number(invoice_input)
    if not invoice_number:
        st.error("Informe um numero de nota valido (somente digitos).")
        st.stop()

    with st.spinner("Consultando API..."):
        xml_content, error = fetch_xml(invoice_number)

    if error:
        st.error(error)
    else:
        st.success("XML obtido com sucesso.")
        st.download_button(
            label="Download do XML",
            data=xml_content,
            file_name=f"nfe_{invoice_number}.xml",
            mime="application/xml",
            type="primary",
        )
