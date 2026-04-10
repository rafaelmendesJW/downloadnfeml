import re
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


BASE_URL = "https://www.mercadolivre.com.br/emissor/relatorios/api/document"
LOGO_CANDIDATE_PATHS = [
    Path("C:/Users/RafaelMendesCarneiro/OneDrive - MARHGUS MOTOS LTDA/Imagens/logo v 1.png"),
    Path("logo v 1.png"),
    Path("assets/logo.png"),
]


def normalize_invoice_number(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def parse_invoice_numbers(raw_value: str) -> list[str]:
    tokens = re.split(r"[\n,;]+", raw_value or "")
    normalized = [normalize_invoice_number(token) for token in tokens]
    filtered = [item for item in normalized if item]

    unique_in_order: list[str] = []
    seen = set()
    for item in filtered:
        if item not in seen:
            unique_in_order.append(item)
            seen.add(item)
    return unique_in_order


def build_download_url(invoice_number: str) -> str:
    return f"{BASE_URL}/{invoice_number}/xml"


def find_logo_path() -> Path | None:
    for candidate in LOGO_CANDIDATE_PATHS:
        if candidate.exists():
            return candidate
    return None


st.set_page_config(page_title="Download XML NFe", layout="centered")

logo_path = find_logo_path()
if logo_path is not None:
    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        st.image(str(logo_path), width=220)
    st.markdown("## Download XML de Nota Fiscal")
else:
    st.title("Download XML de Nota Fiscal")

st.write(
    "Informe um ou varios numeros de nota e abra os links de download. "
    "O XML sera autenticado pela sessao ja logada no navegador."
)

invoice_input = st.text_area(
    "Numeros das notas",
    placeholder="Ex.: 5845581252, 5741995505, 5123456789",
    help="Separe por virgula, ponto e virgula ou quebra de linha.",
)

if st.button("Gerar link de download", type="primary"):
    invoice_numbers = parse_invoice_numbers(invoice_input)
    if not invoice_numbers:
        st.error("Informe ao menos um numero de nota valido (somente digitos).")
        st.stop()

    download_urls = [build_download_url(number) for number in invoice_numbers]
    st.success(f"Foram gerados {len(download_urls)} links de download.")

    urls_json = json.dumps(download_urls)
    open_all_html = f"""
    <div>
      <button
        onclick='openAllDownloads()'
        style="
          background:#0068c9;
          color:white;
          border:none;
          border-radius:8px;
          padding:10px 16px;
          cursor:pointer;
          font-weight:600;
        "
      >
        Abrir download no Mercado Livre
      </button>
    </div>
    <script>
      const urls = {urls_json};
      function openAllDownloads() {{
        urls.forEach((url, index) => {{
          setTimeout(() => window.open(url, "_blank"), index * 250);
        }});
      }}
    </script>
    """
    components.html(open_all_html, height=70)

    st.write("Links gerados:")
    for number, url in zip(invoice_numbers, download_urls):
        st.markdown(f"- Nota `{number}`: [Abrir link]({url})")

    st.caption(
        "Se o navegador bloquear pop-ups, permita pop-ups para esta pagina e clique novamente."
    )
