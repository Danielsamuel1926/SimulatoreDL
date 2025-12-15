import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from fpdf import FPDF
import base64
import numpy as np 

# ==============================
# FUNZIONE DI GENERAZIONE PDF
# ==============================

class PDF(FPDF):
    """Classe personalizzata per intestazione e piè di pagina del Report"""
    def header(self):
        self.set_fill_color(37, 48, 115) # Colore blu scuro
        self.rect(0, 0, 210, 20, 'F')
        self.set_text_color(255, 255, 255) # Testo bianco
        self.set_font('Arial', 'B', 16)
        
        # Titolo Centrato
        self.cell(0, 10, 'Estratto Simulazione Daniele Lettera', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Daniele Lettera Consulenza', 0, 1, 'C')
        self.set_text_color(0, 0, 0) # Reimposta il colore del testo a nero
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100, 100, 100) # Testo grigio
        self.cell(0, 10, f'Pagina {self.page_no()}/{{nb}} - Simulazione Indicativa', 0, 0, 'C')

def genera_pdf_simulazione(cliente, periodo_str, tipo_energia, offerta, df_risultati, totale_finale, fatt_attuale, diff):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font('Arial', '', 12)

    # 1. Dati Principali
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f'Dati del Cliente e Offerta', 0, 1, 'L', fill=True)
    pdf.ln(2)

    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f'Cliente: {cliente}', 0, 1)
    pdf.cell(0, 7, f'Tipo Fornitura: {tipo_energia}', 0, 1)
    pdf.cell(0, 7, f'Offerta Simulazione: {offerta}', 0, 1)
    pdf.cell(0, 7, f'Periodo Analizzato: {periodo_str}', 0, 1)
    pdf.ln(8)

    # 2. Tabella dei Risultati (Scontrino)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(190, 190, 190)
    pdf.cell(0, 10, 'Dettaglio Costi (Scontrino dell\'Energia)', 0, 1, 'L', fill=True)
    pdf.ln(2)
    
    # Intestazioni Tabella
    col_widths = [80, 50, 40]
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_widths[0], 7, 'Descrizione', 1, 0, 'C')
    pdf.cell(col_widths[1], 7, 'Costo Unitario (Eur)', 1, 0, 'C')
    pdf.cell(col_widths[2], 7, 'Importo (Eur)', 1, 1, 'C')

    # Righe Dati
    pdf.set_font('Arial', '', 9)
    for index, row in df_risultati.iterrows():
        descrizione_pulita = str(row['Descrizione']).replace('€', 'Eur')
        costo_unitario_pulito = str(row['Costo Unitario (€)']).replace('€', 'Eur')
        importo_pulito = str(row['Importo (€)']).replace('€', 'Eur')
        
        pdf.cell(col_widths[0], 6, descrizione_pulita, 1, 0, 'L')
        pdf.cell(col_widths[1], 6, costo_unitario_pulito, 1, 0, 'R')
        pdf.cell(col_widths[2], 6, importo_pulito, 1, 1, 'R')
    pdf.ln(5)

    # 3. Totale e Risparmio
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(102, 179, 255) 
    pdf.cell(130, 10, 'TOTALE STIMATO SIMULAZIONE:', 1, 0, 'L', fill=True)
    pdf.cell(30, 10, f'{totale_finale:.2f} Eur', 1, 1, 'R', fill=True)
    pdf.ln(5)

    if fatt_attuale > 0:
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 7, f'Importo Fattura Attuale per Confronto: {fatt_attuale:.2f} Eur', 0, 1)
        pdf.set_font('Arial', 'B', 14)
        if diff > 0:
            pdf.set_fill_color(144, 238, 144) 
            risp_text = f'RISPARMIO STIMATO: {diff:.2f} Eur'
        elif diff < 0:
            pdf.set_fill_color(255, 160, 122) 
            risp_text = f'AUMENTO STIMATO: {-diff:.2f} Eur'
        else:
            pdf.set_fill_color(255, 255, 180) 
            risp_text = 'NESSUN CAMBIAMENTO SIGNIFICATIVO'
        
        pdf.cell(0, 10, risp_text, 1, 1, 'C', fill=True)

    try:
        pdf_bytes = pdf.output(dest='S').encode('iso-8859-1', 'ignore')
    except Exception:
        pdf_string = pdf.output(dest='S').decode('iso-8859-1', 'ignore')
        pdf_string_safe = pdf_string.replace('€', ' Eur').replace('\u20ac', ' Eur')
        pdf_bytes = pdf_string_safe.encode('iso-8859-1', 'ignore')

    return pdf_bytes

# ==============================
# STILE GENERALE
# ==============================
st.set_page_config(layout="wide") 
st.markdown("""
<style>
body { background-color: #E7F5FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.header-container {
    background: linear-gradient(90deg, #171d42, #253073);
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    height: 40px;
}
.box-offerta-custom {
    background: linear-gradient(90deg, #186020, #968a11);
    color:white;
    padding:15px;
    border-radius:12px;
    margin-bottom:15px;
}
.box-download-custom a {
    background: linear-gradient(90deg, #186020 0%, #38a169 100%);
    color: white !important;
    padding: 10px 20px; 
    text-align: center; 
    text-decoration: none; 
    display: block; 
    border-radius: 8px; 
    font-weight: bold; 
    width:100%; 
    box-sizing:border-box;
    margin-top: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown("""
<div class="header-container">
    <span style="font-size:30px; font-weight:bold; color:#fff; display:block;">Simulatore Luce & Gas 💡🔥</span>
    <span style="font-size:18px; font-weight:bold; color:#fff; display:block;">Daniele Lettera Consulenza</span>
</div>
""", unsafe_allow_html=True)

tipo = option_menu(
    menu_title=None,
    options=["Luce", "Gas"],
    icons=["bolt", "fire"],
    default_index=0,
    orientation="horizontal",
    key="menu_tipo_energia",
    styles={
        "container": {"background-color": "#c4c4c4", "padding": "0!important"},
        "nav-link": {"font-size": "18px", "color": "#005f91", "padding": "10px 18px"},
        "nav-link-selected": {"background-color": "#0A4CA3", "color": "white"},
    }
)

# ==============================
# COSTANTI E DATI
# ==============================
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90
ASOS = 0.03
SPESA_RETE_VAR_LUCE_UNITARIO = 0.0445

ACCISA_LUCE_TIPI = {
    "Domestico Residente (Accisa differenziata)": {"aliquota": 0.0227, "soglia_annua": 1800, "descrizione": "Oltre 1800 kWh/anno, aliquota 0.0227 €/kWh."},
    "Domestico Non Residente (Accisa piena)": {"aliquota": 0.0227, "soglia_annua": 0, "descrizione": "Aliquota piena su tutto il consumo."},
    "Uso Diverso/Azienda (Bassa Tensione)": {"aliquota": 0.0125, "soglia_annua": 0, "descrizione": "Aliquota 0.0125 €/kWh. IVA 22% obbligatoria."},
    "Esenzione Totale": {"aliquota": 0.0, "soglia_annua": 999999, "descrizione": "Esenzione totale."}
}

PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178, 0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]
OFFERTE_LUCE = {"Fast":(0.010,120.0),"F&F":(0.008,102.0),"Sind":(0.005,84.0),"Smart":(0.010,150.0)}
PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,120.0),"F&F":(0.08,102.0),"Sind":(0.05,84.0),"Smart":(0.10,150.0)}

QUOTA_CONSUMO_GAS = 0.025
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50
MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO","LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

# ==============================
# SESSION STATE
# ==============================
for key in ["cliente","kwh","kwh_annui","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale", "tipo_accisa_luce", "tipo_cliente"]:
    if key not in st.session_state:
        st.session_state[key] = "Residenziale" if key == "tipo_cliente" else ("Domestico Residente (Accisa differenziata)" if key == "tipo_accisa_luce" else 0.0)
        if key == "cliente": st.session_state[key] = ""
        if key == "kw": st.session_state[key] = 3.0

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### 📝 Dati del Cliente:")
col_main1, col_main2 = st.columns(2)
with col_main1:
    tipo_cliente = st.selectbox("Tipologia Cliente", ["Residenziale", "Business"], key='input_tipo_cliente')
with col_main2:
    cliente = st.text_input("Nome Cliente", st.session_state.cliente).upper()

col_periodo, col_mese1, col_mese2 = st.columns(3)
with col_periodo: periodo = st.selectbox("Periodo di Fatturazione", ["Mensile","Bimestrale"])
with col_mese1: mese1 = st.selectbox("Mese 1", MESI)
with col_mese2: mese2 = st.selectbox("Mese 2", MESI) if periodo == "Bimestrale" else None

st.markdown("---")
if tipo == "Luce":
    c1, c2, c3 = st.columns(3)
    with c1: kwh = st.number_input("kWh Periodo", value=250.0)
    with c2: kwh_annui = st.number_input("kWh Annui", value=2500.0)
    with c3: kw = st.selectbox("Potenza kW", [1.5, 3.0, 4.5, 6.0, 10.0], index=1)
    
    tipo_accisa_luce = st.selectbox("Tipologia Accisa", list(ACCISA_LUCE_TIPI.keys()))
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)", value=0.0)
else:
    c1, c2 = st.columns(2)
    with c1: smc = st.number_input("SMC Periodo", value=100.0)
    with c2: smc_annuo = st.number_input("SMC Annui", value=1000.0)
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()))
    canone_tv = 0.0

st.markdown("### ➕ Voci Aggiuntive:")
ca1, ca2, ca3, ca4 = st.columns(4)
with ca1: bonus = st.number_input("Bonus (€)", value=0.0)
with ca2: ricalcoli = st.number_input("Ricalcoli (€)", value=0.0)
with ca3: altre = st.number_input("Altre (€)", value=0.0)
with ca4: fatt_attuale = st.number_input("Fattura Confronto (€)", value=0.0)

# ==============================
# CALCOLO
# ==============================
if st.button("▶️ Calcola"):
    try:
        mesi_idx = [MESI.index(mese1) + 1]
        periodo_str = mese1
        if periodo=="Bimestrale" and mese2:
            mesi_idx.append(MESI.index(mese2) + 1)
            periodo_str = f"{mese1}-{mese2}"
        
        num_mesi = len(mesi_idx)
        p_medio = sum([PUN[m] if tipo=="Luce" else PSV[m] for m in mesi_idx])/num_mesi
        righe = []

        if tipo == "Luce":
            spr, comm = OFFERTE_LUCE[offerta]
            p_unit = p_medio + spr + DISPACCIAMENTO + ASOS
            materia = kwh * p_unit
            comm_periodo = (comm/12) * num_mesi
            rete = kwh * SPESA_RETE_VAR_LUCE_UNITARIO
            pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            
            # ACCISA
            cfg = ACCISA_LUCE_TIPI[tipo_accisa_luce]
            accisa = kwh * (cfg["aliquota"] * (max(0, kwh_annui - cfg["soglia_annua"])/kwh_annui)) if kwh_annui>0 else 0
            
            # IVA
            iva_rate = 0.22 if (tipo_cliente == "Business" or tipo_accisa_luce == "Uso Diverso/Azienda (Bassa Tensione)") else 0.10
            iva = (materia + comm_periodo + rete + pot + oneri + accisa) * iva_rate
            
            righe = [
                {"Descrizione": "Spesa Materia", "Costo Unitario (€)": f"{p_unit:.4f}", "Importo (€)": f"{materia:.2f} €"},
                {"Descrizione": "Commercializzazione", "Costo Unitario (€)": f"{comm:.2f}/anno", "Importo (€)": f"{comm_periodo:.2f} €"},
                {"Descrizione": "Oneri e Rete", "Costo Unitario (€)": "Vario", "Importo (€)": f"{rete+pot+oneri:.2f} €"},
                {"Descrizione": f"Accise + IVA ({iva_rate*100:.0f}%)", "Costo Unitario (€)": "N/A", "Importo (€)": f"{accisa+iva:.2f} €"}
            ]
            totale = materia + comm_periodo + rete + pot + oneri + accisa + iva + canone_tv + ricalcoli + altre - bonus

        else: # GAS
            spr, comm = OFFERTE_GAS[offerta]
            p_unit = p_medio + spr + QUOTA_CONSUMO_GAS
            materia = smc * p_unit
            comm_periodo = (comm/12) * num_mesi
            rete = (QUOTA_VAR_DIST_GAS * smc) + QUOTA_DIST_GAS
            oneri = (ONERI_SISTEMA_GAS * num_mesi) + (0.19 * smc)
            
            # ACCISA GAS
            if smc_annuo <= 120: a_u = 0.044
            elif smc_annuo <= 480: a_u = 0.175
            else: a_u = 0.170
            accisa = smc * a_u
            
            # IVA GAS
            iva_rate = 0.22 if (tipo_cliente == "Business" or smc_annuo > 480) else 0.10
            iva = (materia + comm_periodo + rete + oneri + accisa) * iva_rate
            
            righe = [
                {"Descrizione": "Spesa Materia Gas", "Costo Unitario (€)": f"{p_unit:.4f}", "Importo (€)": f"{materia:.2f} €"},
                {"Descrizione": "Commercializzazione", "Costo Unitario (€)": f"{comm:.2f}/anno", "Importo (€)": f"{comm_periodo:.2f} €"},
                {"Descrizione": "Rete e Oneri", "Costo Unitario (€)": "Vario", "Importo (€)": f"{rete+oneri:.2f} €"},
                {"Descrizione": f"Accise + IVA ({iva_rate*100:.0f}%)", "Costo Unitario (€)": "N/A", "Importo (€)": f"{accisa+iva:.2f} €"}
            ]
            totale = materia + comm_periodo + rete + oneri + accisa + iva + ricalcoli + altre - bonus

        st.dataframe(pd.DataFrame(righe), use_container_width=True)
        st.success(f"### Totale: {totale:.2f} €")
        
        if fatt_attuale > 0:
            diff = fatt_attuale - totale
            st.info(f"Risparmio rispetto attuale: {diff:.2f} €")

        # PDF
        pdf_out = genera_pdf_simulazione(cliente, periodo_str, tipo, offerta, pd.DataFrame(righe), totale, fatt_attuale, fatt_attuale-totale)
        b64 = base64.b64encode(pdf_out).decode('latin-1')
        st.markdown(f'<div class="box-download-custom"><a href="data:application/pdf;base64,{b64}" download="Report.pdf">⬇️ SCARICA PDF</a></div>', unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Errore: {e}")
