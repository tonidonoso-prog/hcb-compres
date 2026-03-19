import streamlit as st
import io
import os
import sys

# Asegurar que pcap_processor es importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcap_processor import extract_text, analyze_pcap, create_word_report

st.set_page_config(page_title="Extractor PCAP", page_icon="📄", layout="wide")

st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { color: #004a99; }
    .stButton>button {
        background-color: #004a99; color: white; font-weight: bold;
        border: none; border-radius: 8px; height: 3em; width: 100%;
    }
    .stButton>button:hover { background-color: #003366; }
</style>
""", unsafe_allow_html=True)

st.title("📄 Extractor de Criterios PCAP")
st.write("Sube el Pliego (PDF) y se extraerán los criterios de adjudicación de forma estructurada. Soporte bilingüe: Castellano / Català.")

uploaded_file = st.file_uploader("Elige un archivo PDF", type="pdf")

if uploaded_file is not None:
    filename = uploaded_file.name
    name_only = filename.replace('.pdf', '').replace('.PDF', '')
    st.info(f"Procesando: **{filename}**")

    with st.spinner("Extrayendo texto y analizando criterios..."):
        text = extract_text(io.BytesIO(uploaded_file.read()))

        if not text:
            st.error("No se pudo extraer texto del PDF. Si es un PDF escaneado (imagen), requiere OCR.")
        else:
            analysis = analyze_pcap(text)
            subj = analysis.get('subjective')
            obj = analysis.get('objective')
            warnings = analysis.get('warnings', [])

            # --- AVISOS ---
            for w in warnings:
                st.warning(f"⚠️ {w}")

            # --- RESUMEN ---
            if subj or obj:
                st.subheader("📊 Resumen de Puntuación")
                cols = st.columns(3)
                with cols[0]:
                    pts = subj.get('max_points', '—') if subj else '—'
                    st.metric("Subjectius (Judici de Valor)", f"{pts} punts")
                with cols[1]:
                    pts = obj.get('max_points', '—') if obj else '—'
                    st.metric("Objectius (Automàtics)", f"{pts} punts")
                with cols[2]:
                    total = (subj.get('max_points', 0) or 0) + (obj.get('max_points', 0) or 0)
                    st.metric("TOTAL", f"{total} punts")

            st.divider()

            # --- SUBJECTIUS ---
            if subj and subj.get('lots'):
                st.subheader("1. Criteris Subjectius — Judici de Valor")
                for lot in subj['lots']:
                    with st.expander(f"📦 {lot['id']} ({lot['description']})", expanded=True):
                        if lot['criteria']:
                            for c in lot['criteria']:
                                pts = f"**{c['max_points']} punts**" if c['max_points'] else ""
                                st.markdown(f"**{c['letter']}) {c['name']}** — {pts}")
                                if c['ranges']:
                                    for rng in c['ranges']:
                                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• **{rng['level']}:** {rng['detail']}")
                                st.markdown("---")
                        else:
                            st.write("No s'han detectat criteris detallats.")

            # --- OBJECTIUS ---
            if obj and obj.get('criteria'):
                st.subheader("2. Criteris Objectius — Automàtics")
                for c in obj['criteria']:
                    pts = f"**{c['max_points']} punts**" if c['max_points'] else ""
                    with st.expander(f"📐 {c['letter']}) {c['name']} — {pts}", expanded=True):
                        if c.get('tiers'):
                            for tier in c['tiers']:
                                st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• {tier}")
                        else:
                            st.write(c.get('body', ''))

            st.divider()

            # --- GENERAR WORD ---
            word_buffer = create_word_report(name_only, analysis)
            st.success("Informe Word generado correctamente.")
            st.download_button(
                label="📥 Descargar Informe Word (.docx)",
                data=word_buffer,
                file_name=f"{name_only}_Criterios.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary"
            )
else:
    st.warning("⚠️ Sube un archivo PDF para comenzar.")

st.markdown("---")
st.caption("© 2026 Hospital Clínic Barcelona - Gestión de Compras Hospitalarias")
