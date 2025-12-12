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
        # Sostituisci il simbolo Euro con la stringa "Eur" nella descrizione
        descrizione_pulita = str(row['Descrizione']).replace('€', 'Eur')
        costo_unitario_pulito = str(row['Costo Unitario (€)']).replace('€', 'Eur')
        importo_pulito = str(row['Importo (€)']).replace('€', 'Eur')
        
        pdf.cell(col_widths[0], 6, descrizione_pulita, 1, 0, 'L')
        pdf.cell(col_widths[1], 6, costo_unitario_pulito, 1, 0, 'R')
        pdf.cell(col_widths[2], 6, importo_pulito, 1, 1, 'R')
    pdf.ln(5)

    # 3. Totale e Risparmio
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(102, 179, 255) # Azzurro
    pdf.cell(130, 10, 'TOTALE STIMATO SIMULAZIONE:', 1, 0, 'L', fill=True)
    pdf.cell(30, 10, f'{totale_finale:.2f} Eur', 1, 1, 'R', fill=True)
    pdf.ln(5)

    if fatt_attuale > 0:
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 7, f'Importo Fattura Attuale per Confronto: {fatt_attuale:.2f} Eur', 0, 1)
        
        pdf.set_font('Arial', 'B', 14)
        if diff > 0:
            pdf.set_fill_color(144, 238, 144) # Verde chiaro
            risp_text = f'RISPARMIO STIMATO: {diff:.2f} Eur'
        elif diff < 0:
            pdf.set_fill_color(255, 160, 122) # Salmone
            risp_text = f'AUMENTO STIMATO: {-diff:.2f} Eur'
        else:
            pdf.set_fill_color(255, 255, 180) # Giallo chiaro
            risp_text = 'NESSUN CAMBIAMENTO SIGNIFICATIVO'
        
        pdf.cell(0, 10, risp_text, 1, 1, 'C', fill=True)

    # CORREZIONE ERRORE U+00A0 e €: 
    # Usiamo 'iso-8859-1' che è simile a latin-1 ma compatibile con fpdf2 
    # e rimuoviamo eventuali simboli euro residui
    try:
        pdf_bytes = pdf.output(dest='S').encode('iso-8859-1', 'ignore')
    except UnicodeEncodeError:
        # Soluzione fallback se fallisce ancora: decodifica, pulisci e codifica
        pdf_string = pdf.output(dest='S').decode('iso-8859-1', 'ignore')
        pdf_string_safe = pdf_string.replace('€', ' Eur').replace('\u20ac', ' Eur')
        pdf_bytes = pdf_string_safe.encode('iso-8859-1', 'ignore')

    return pdf_bytes

# ==============================
# STILE GENERALE
# ==============================
st.set_page_config(layout="wide") # Imposta il layout wide per maggiore spazio
st.markdown("""
<style>
/* Caratteri e Sfondo */
body { background-color: #E7F5FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }

/* Header */
.header-container {
    background: linear-gradient(90deg, #0b0c12, #253073);
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

/* Tabella (DataFrame) */
.stDataFrame {
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

/* Pulsanti */
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    height: 40px;
}

/* Stile per il box dell'offerta */
.box-offerta-custom {
    background: linear-gradient(90deg, #186020, #968a11);
    color:white;
    padding:15px;
    border-radius:12px;
    margin-bottom:15px;
}
.box-offerta-custom h6, .box-offerta-custom p {
    margin: 3px 0; /* Riduco i margini interni */
}
.box-offerta-custom p {
    font-size: 14px;
}
.box-offerta-custom p:last-child {
    font-weight: bold;
    font-size: 15px;
    margin-top: 5px;
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

# ==============================
# MENU ORIZZONTALE
# ==============================
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
        "nav-link:hover": {"background-color": "#0077b6"},
        "nav-link-selected": {"background-color": "#00BFFF", "color": "white"},
    }
)

# ==============================
# COSTANTI E DATI
# ==============================
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90 # €/mese
ASOS = 0.03
SPESA_RETE_VAR_LUCE_UNITARIO = 0.0445

# ACCISA LUCE
ACCISA_LUCE_ALIQUOTA_DOMESTICO_RESIDENTE = 0.0227 # €/kWh
ACCISA_LUCE_SOGLIA_ANNUA_RESIDENTE = 150 * 12 # 1800 kWh/anno (150 kWh/mese)

ACCISA_LUCE_TIPI = {
    "Domestico Residente (Accisa differenziata)": {
        "aliquota": ACCISA_LUCE_ALIQUOTA_DOMESTICO_RESIDENTE,
        "soglia_annua": ACCISA_LUCE_SOGLIA_ANNUA_RESIDENTE,
        "descrizione": f"Oltre {ACCISA_LUCE_SOGLIA_ANNUA_RESIDENTE} kWh/anno (150/mese), aliquota {ACCISA_LUCE_ALIQUOTA_DOMESTICO_RESIDENTE} €/kWh."
    },
    "Domestico Non Residente (Accisa piena)": {
        "aliquota": 0.0227, 
        "soglia_annua": 0,
        "descrizione": f"Aliquota piena (0.0227 €/kWh) su tutto il consumo."
    },
    "Uso Diverso/Azienda (Bassa Tensione)": {
        "aliquota": 0.0125, 
        "soglia_annua": 0,
        "descrizione": f"Aliquota ridotta uso diverso: 0.0125 €/kWh."
    },
    "Esenzione Totale": {
        "aliquota": 0.0,
        "soglia_annua": 999999, 
        "descrizione": "Esenzione totale da Accisa."
    }
}
DEFAULT_ACCISA_LUCE_KEY = "Domestico Residente (Accisa differenziata)"

# PUN (1-indexed: 0=dummy, 1=Gennaio, ..., 12=Dicembre)
PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178, 
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

# OFFERTE_LUCE: (SPREAD, COSTO_COMM_ANNUO)
OFFERTE_LUCE = {"Fast":(0.010,120.0),"F&F":(0.008,102.0),"Sind":(0.005,84.0),"Smart":(0.010,150.0)}

# PSV (1-indexed: 0=dummy, 1=Gennaio, ..., 12=Dicembre)
PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
# OFFERTE_GAS: (SPREAD, COSTO_COMM_ANNUO)
OFFERTE_GAS = {"Fast":(0.10,120.0),"F&F":(0.08,102.0),"Sind":(0.05,84.0),"Smart":(0.10,150.0)}

QUOTA_CONSUMO_GAS = 0.025
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50 # €/mese

MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO",
        "LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

# Funzioni di calcolo per il Gas
def accisa_annua_gas(smc_annuo):
    if smc_annuo <= 120: return 0.044
    elif smc_annuo <= 480: return 0.175
    elif smc_annuo <= 1560: return 0.170
    else: return 0.186

def aliquota_iva_gas(smc_annuo):
    return 0.10 if smc_annuo <= 480 else 0.22

# ==============================
# INIZIALIZZAZIONE SESSION STATE
# ==============================
for key in ["cliente","kwh","kwh_annui","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale", "tipo_accisa_luce"]:
    if key not in st.session_state:
        if key == "kw":
            st.session_state[key] = 3.0
        elif key == "cliente":
            st.session_state[key] = ""
        elif key == "tipo_accisa_luce":
            st.session_state[key] = DEFAULT_ACCISA_LUCE_KEY
        elif key in ["kwh_annui", "smc_annuo"]:
            st.session_state[key] = 2000.0 if key == "kwh_annui" else 700.0
        else:
            st.session_state[key] = 0.0
    
    # CONTROLLO DI ROBUSTEZZA PER LA CHIAVE ACCISA
    if key == "tipo_accisa_luce" and st.session_state.tipo_accisa_luce not in ACCISA_LUCE_TIPI.keys():
        st.session_state.tipo_accisa_luce = DEFAULT_ACCISA_LUCE_KEY


# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### 📝 Dati del Cliente e Consumi:")

# === CAMPO CLIENTE IN PRIMIS ===
cliente = st.text_input("Nome Cliente", st.session_state.cliente, key='input_cliente_final').upper()
st.session_state.cliente = cliente
# ===============================

# Contenitore per i dati del periodo
col_periodo, col_mese1, col_mese2 = st.columns(3)

with col_periodo:
    periodo = st.selectbox("Periodo di Fatturazione", ["Mensile","Bimestrale"], key='input_periodo')
with col_mese1:
    mese1 = st.selectbox("Mese 1", MESI, key='input_mese1')
with col_mese2:
    if periodo == "Bimestrale":
        mese2 = st.selectbox("Mese 2", MESI, key='input_mese2')
    else:
        mese2 = None

# Input Dati Luce/Gas specifici
st.markdown("---")

col_cons_1, col_cons_2 = st.columns(2)

if tipo == "Luce":
    with col_cons_1:
        kwh = st.number_input("Consumo Luce kWh (del periodo)", value=st.session_state.kwh, min_value=0.0, key='input_kwh')
        st.session_state.kwh = kwh
    with col_cons_2:
        kwh_annui = st.number_input("Consumo annuo Luce (kWh)", value=st.session_state.kwh_annui, min_value=0.0, key='input_kwh_annui')
        st.session_state.kwh_annui = kwh_annui
    
    col_accisa_1, col_accisa_2 = st.columns(2)
    with col_accisa_1:
        kw_options = [1.0, 1.5, 2.0, 2.5, 3.0, 4.5, 5.0, 5.5, 6.0]
        default_index = kw_options.index(st.session_state.kw) if st.session_state.kw in kw_options else 4
        kw = st.selectbox("Potenza impegnata (kW)", kw_options, index=default_index, key='input_kw')
        st.session_state.kw = kw
    
    with col_accisa_2:
        tipo_accisa_luce = st.selectbox(
            "Tipologia Accisa (Luce)", 
            list(ACCISA_LUCE_TIPI.keys()),
            index=list(ACCISA_LUCE_TIPI.keys()).index(st.session_state.tipo_accisa_luce),
            key='input_tipo_accisa_luce'
        )
        st.session_state.tipo_accisa_luce = tipo_accisa_luce
    
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()), key='input_offerta_luce')
    st.info(f"**Dettaglio Accisa:** {ACCISA_LUCE_TIPI[tipo_accisa_luce]['descrizione']}")
    
    canone_tv = st.number_input("Canone TV (€)", value=0.0, min_value=0.0, key='input_canone_tv')
else:
    with col_cons_1:
        smc = st.number_input("Consumo Gas (m³)", value=st.session_state.smc, min_value=0.0, key='input_smc')
        st.session_state.smc = smc
    with col_cons_2:
        smc_annuo = st.number_input("Consumo annuo Gas (m³)", value=st.session_state.smc_annuo, min_value=0.0, key='input_smc_annuo')
        st.session_state.smc_annuo = smc_annuo
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()), key='input_offerta_gas')
    canone_tv = 0.0

# Input Dati Comuni/Aggiuntivi
st.markdown("---")
st.markdown("### ➕ Voci Aggiuntive Altri Importi:")

col_extra_1, col_extra_2 = st.columns(2)
with col_extra_1:
    bonus = st.number_input("Bonus Sociale (da sottrarre, €)", value=st.session_state.bonus, key='input_bonus')
    ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli, key='input_ricalcoli')
with col_extra_2:
    altre = st.number_input("Altre Partite (€)", value=st.session_state.altre, key='input_altre')
    fatt_attuale = st.number_input("Importo Fattura Attuale per Confronto (€)", value=st.session_state.fatt_attuale, key='input_fatt_attuale')

# Memorizzazione dello stato della sessione (assicura la persistenza dei dati)
st.session_state.bonus = bonus
st.session_state.ricalcoli = ricalcoli
st.session_state.altre = altre
st.session_state.fatt_attuale = fatt_attuale


# ==============================
# PULSANTI CALCOLA E RESET
# ==============================
st.markdown("---")
col1, col2, col3 = st.columns(3)

calcola = col1.button("▶️ Calcola Simulazione")
reset = col2.button("🗑️ Reset Dati")


if reset:
    # Resetta tutti i valori e ricarica l'app
    for key in ["cliente","kwh","kwh_annui","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
        if key == "cliente":
            st.session_state[key] = ""
        elif key in ["kwh_annui", "smc_annuo"]:
            st.session_state[key] = 2000.0 if key == "kwh_annui" else 700.0
        else:
            st.session_state[key] = 0.0
    st.session_state.kw = 3.0
    st.session_state.tipo_accisa_luce = DEFAULT_ACCISA_LUCE_KEY
    st.rerun()

# ==============================
# CALCOLO BOLLETTA E DOWNLOAD PDF
# ==============================
if calcola:
    st.markdown("#### 🧾 Box dell'offerta")
    
    try:
        if not st.session_state.cliente:
            st.warning("⚠️ Per favore, inserisci il Nome Cliente per procedere con la simulazione.")
            st.stop()
        
        # Calcolo degli indici del mese (1-indexed per PUN/PSV)
        mesi_idx = [MESI.index(mese1) + 1]
        periodo_str = mese1
        if periodo=="Bimestrale":
            if mese2 is None:
                st.error("Selezionare il secondo mese per il periodo bimestrale.")
                raise ValueError("Secondo mese non selezionato.")
            mesi_idx.append(MESI.index(mese2) + 1)
            periodo_str = f"{mese1} e {mese2}"
        
        num_mesi = len(mesi_idx)
        righe = [] # Unico scontrino
        
        # --- Dati offerta ---
        if tipo == "Luce":
            SPREAD, COMM_ANNUO = OFFERTE_LUCE[offerta] # COMM_ANNUO è in €/anno
            unita_prezzo = "kWh"
            lista_prezzi = PUN
            consumo = kwh
            consumo_annuo_ref = kwh_annui # Uso kWh annui per riferimento accisa
            unita_misura = "kWh"
            costo_indicizzato_base = "PUN"
            costo_annuo_commercializzazione = COMM_ANNUO
        else:
            SPREAD, COMM_ANNUO = OFFERTE_GAS[offerta] # COMM_ANNUO è in €/anno
            unita_prezzo = "m³"
            lista_prezzi = PSV
            consumo = smc
            consumo_annuo_ref = smc_annuo # Uso smc annui per riferimento accisa gas
            unita_misura = "m³"
            costo_indicizzato_base = "PSV"
            costo_annuo_commercializzazione = COMM_ANNUO


        # Costo Commercializzazione Mensile
        COMM_MENSILE = COMM_ANNUO / 12
        COMM_TOT = COMM_MENSILE * num_mesi

        # --- Calcolo costi variabili ---
        prezzo_medio_indicizzato = sum([lista_prezzi[m] for m in mesi_idx])/num_mesi
        
        if tipo=="Luce":
            # Calcolo corretto che include tutti i costi variabili (Dispacciamento e ASOS inclusi)
            prezzo_unitario_materia = prezzo_medio_indicizzato + SPREAD + DISPACCIAMENTO + ASOS
            materia = consumo * prezzo_unitario_materia
            
            # Descrizione Semplificata per Luce 
            materia_descrizione = f"Materia Energia (variabile) ({consumo:.2f} {unita_misura})"
        else:
            # Costo materia prima: PSV + Spread + Quota Consumo Gas (Variabile)
            prezzo_unitario_materia = prezzo_medio_indicizzato + SPREAD + QUOTA_CONSUMO_GAS
            materia = consumo * prezzo_unitario_materia
            
            # Descrizione Semplificata per Gas
            materia_descrizione = f"Materia Energia/PSV (variabile) ({consumo:.2f} {unita_misura})"


        # Funzione helper per formattare l'unità o N/A (Usa € nel codice Streamlit)
        def fmt_unit(val, unit=""):
            # Gestisce il caso di costo unitario per voce fissa (costo €/unità di tempo o €/kW)
            if unit == "mese" or unit == "kW":
                return f"{val:.2f} €/{unit}"
            # Gestisce il caso di costo unitario per voce variabile (costo €/kWh o €/m³)
            elif unit:
                return f"{val:.4f} €/{unit}"
            # Per l'IVA nel Gas, mostriamo la percentuale
            elif unit == "%":
                return f"{val*100:.0f} %" 
            # NUOVA UNITÀ: Costo Annuale di Commercializzazione
            elif unit == "anno": 
                return f"{val:.2f} €/{unit}"
            # Per voci fisse senza unità di tempo specifica (es. Ricalcoli)
            return "N/A"

        # --- BOX DETTAGLIO COSTI (AGGIORNATO) ---
        
        # 1. Costo Unitario Totale Materia
        costo_totale_materia_text = (
            f"Costo Totale Materia ({costo_indicizzato_base} + spread ): "
            f"{prezzo_unitario_materia:.4f} €/{unita_misura}"
        )

        # 2. Dettaglio Spread
        spread_text = f"Spread Consumo: **{SPREAD:.4f} €/{unita_prezzo}**"

        # 3. Dettaglio Commercializzazione
        comm_annua_text = f"Costo Comm. Anno: **{costo_annuo_commercializzazione:.2f} €/anno** ({COMM_MENSILE:.2f} €/mese)"
        
        st.markdown(f"""
        <div class="box-offerta-custom">
            <h6 style="margin:0;">**{st.session_state.cliente}** - Offerta: **{offerta}**</h6>
            <p style="margin:0; font-size:14px;">Periodo: {periodo_str}</p>
            <p style="margin:5px 0 0 0;">{spread_text}</p>
            <p style="margin:5px 0 0 0;">{comm_annua_text}</p>
            <p style="margin:5px 0 0 0; font-weight:bold;">{costo_totale_materia_text}</p>
        </div>
        """, unsafe_allow_html=True)

        totale = 0.0
        accise_iva_tot = 0.0

        # ---------------- VOCI DI FORNITURA ----------------
        if tipo=="Luce":
            # Spesa per la Rete (Quota Variabile)
            sp_rete_variabile = consumo * SPESA_RETE_VAR_LUCE_UNITARIO
            # Quota Potenza (Fissa)
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            # Oneri di Sistema (Fissi)
            oneri = ONERI_SISTEMA * num_mesi
            
            # --- CALCOLO ACCISA LUCE CON RIFERIMENTO ANNUO ---
            accisa_config = ACCISA_LUCE_TIPI[st.session_state.tipo_accisa_luce]
            accisa_aliquota = accisa_config["aliquota"]
            accisa_soglia_annua = accisa_config["soglia_annua"]
            
            accisa_luce = 0.0
            if accisa_aliquota > 0 and consumo_annuo_ref > 0:
                # Quota di consumo annuo eccedente la soglia annuale
                consumo_annuo_tassabile = max(0, consumo_annuo_ref - accisa_soglia_annua)
                
                # Calcolo della quota di consumo tassabile annua in percentuale
                rapporto_tassabile = consumo_annuo_tassabile / consumo_annuo_ref
                
                # Consumo del periodo tassabile con l'aliquota piena
                consumo_tassabile = consumo * rapporto_tassabile
            
                accisa_luce = consumo_tassabile * accisa_aliquota
            
            # Base Imponibile IVA 10%
            totale_imponibile = materia + sp_rete_variabile + quota_pot + oneri + COMM_TOT
            # L'IVA si applica su (Base Imponibile + Accisa)
            iva = (totale_imponibile + accisa_luce) * 0.10
            
            # Totale Accise e IVA per la riga riepilogativa
            accise_iva_tot = accisa_luce + iva
            
            # Voci Luce (Dispacciamento rimosso da qui)
            righe += [
                {"Descrizione":materia_descrizione, "Costo Unitario (€)": fmt_unit(prezzo_unitario_materia, "kWh"), "Importo (€)": f"{materia:.2f} €"},
                # Commercializzazione mostra il costo annuo dell'offerta
                {"Descrizione":"Commercializzazione", "Costo Unitario (€)": fmt_unit(costo_annuo_commercializzazione, "anno"), "Importo (€)": f"{COMM_TOT:.2f} €"},
                {"Descrizione":f"Quota Potenza ({kw:.1f} kW) (Fissa)", "Costo Unitario (€)": fmt_unit(QUOTA_POTENZA, "kW"), "Importo (€)": f"{quota_pot:.2f} €"},
                {"Descrizione":"Oneri di sistema (Fissi)", "Costo Unitario (€)": fmt_unit(ONERI_SISTEMA, "mese"), "Importo (€)": f"{oneri:.2f} €"},
                {"Descrizione":"Spesa Rete e gli oneri generali di sistema ", "Costo Unitario (€)": fmt_unit(SPESA_RETE_VAR_LUCE_UNITARIO, "kWh"), "Importo (€)": f"{sp_rete_variabile:.2f} €"},
            ]
            
            totale = totale_imponibile + accise_iva_tot

        # ---------------- GAS (Gas Naturale) ----------------
        else:
            # Spesa per la Rete (Fissa + Variabile)
            sp_rete_var_unitario = QUOTA_VAR_DIST_GAS 
            sp_rete = sp_rete_var_unitario * consumo + QUOTA_DIST_GAS
            
            # Oneri di Sistema (Fissi + Variabili)
            oneri_fissi = ONERI_SISTEMA_GAS * num_mesi
            oneri_var_unitario = (0.07 + 0.12)
            oneri_var = oneri_var_unitario * consumo
            
            # Accise (Variabili)
            accisa_unitario = accisa_annua_gas(smc_annuo)
            accisa_gas = accisa_unitario * consumo
            
            # IVA
            aliquota_iva = aliquota_iva_gas(smc_annuo)
            totale_imponibile_iva = materia + sp_rete + oneri_var + oneri_fissi + COMM_TOT
            # L'IVA si applica su (Base Imponibile + Accisa)
            iva = (totale_imponibile_iva + accisa_gas) * aliquota_iva
            
            # Totale Accise e IVA (per visualizzazione unificata nel Gas)
            accise_iva_tot = accisa_gas + iva
            
            # Voci Gas
            righe += [
                {"Descrizione":materia_descrizione, "Costo Unitario (€)": fmt_unit(prezzo_unitario_materia, "m³"), "Importo (€)": f"{materia:.2f} €"},
                # Commercializzazione mostra il costo annuo dell'offerta
                {"Descrizione":"Commercializzazione", "Costo Unitario (€)": fmt_unit(costo_annuo_commercializzazione, "anno"), "Importo (€)": f"{COMM_TOT:.2f} €"},
                {"Descrizione":f"Spesa Rete ({QUOTA_DIST_GAS:.2f} Fissa + Variabile)", "Costo Unitario (€)": fmt_unit(sp_rete_var_unitario, "m³"), "Importo (€)": f"{sp_rete:.2f} €"},
                {"Descrizione":f"Oneri di sistema ({oneri_fissi:.2f} Fissi + Variabili)", "Costo Unitario (€)": fmt_unit(oneri_var_unitario, "m³"), "Importo (€)": f"{oneri_fissi + oneri_var:.2f} €"},
            ]
            
            totale = totale_imponibile_iva + accise_iva_tot

        # ---------------- VOCI FISCALI (TASSE) ----------------

        if tipo == "Luce":
            # Luce: Accisa e IVA unite
            righe.append({"Descrizione":"Accise + IVA (10%)", 
                          "Costo Unitario (€)": "N/A", 
                          "Importo (€)": f"{accise_iva_tot:.2f} €"})
        else:
            # Gas: Accisa + IVA sono già calcolate e visualizzate insieme per il gas
            aliquota_iva_gas_attuale = aliquota_iva_gas(smc_annuo) # Recupera l'aliquota Gas corretta
            righe.append({"Descrizione":f"Accisa + IVA ({aliquota_iva_gas_attuale*100:.0f}%)", "Costo Unitario (€)": fmt_unit(aliquota_iva_gas_attuale, "%"), "Importo (€)": f"{accise_iva_tot:.2f} €"})


        # ---------------- VOCI EXTRA ----------------
        
        # Voci Aggiuntive/Sottrattive
        if canone_tv > 0:
            # Il canone TV viene visualizzato come costo unitario di sé stesso
            righe.append({"Descrizione": "Canone TV", "Costo Unitario (€)": f"{canone_tv:.2f} €", "Importo (€)": f"{canone_tv:.2f} €"})
            totale += canone_tv

        for voce, val in [("Ricalcoli", ricalcoli), ("Altre Partite", altre)]:
            if val != 0:
                righe.append({"Descrizione": voce, "Costo Unitario (€)": "N/A", "Importo (€)": f"{val:.2f} €"})
                totale += val
        
        # Il bonus sociale va sempre sottratto
        if bonus > 0:
            righe.append({"Descrizione": "Bonus Sociale", "Costo Unitario (€)": "N/A", "Importo (€)": f"{-abs(bonus):.2f} €"})
            totale -= abs(bonus)
        
        # --- STAMPA FINALE ---
        
        st.markdown("#### 🧾 SCONTRINO DELL'ENERGIA")

        df = pd.DataFrame(righe)
        # Rimuoviamo il simbolo Euro dal DataFrame qui, per visualizzare il numero puro 
        # (altrimenti Streamlit lo formatta male nel dataframe).
        df_display = df.copy()
        for col in ['Costo Unitario (€)', 'Importo (€)']:
            df_display[col] = df_display[col].str.replace('€', '').str.replace('Eur', '').str.strip()

        st.dataframe(df_display, hide_index=True, use_container_width=True)
        
        totale_finale = max(0, totale) # Il totale non può essere negativo
        
        # Confronto con la fattura attuale
        diff = fatt_attuale - totale_finale
        
        st.markdown(f"### 💰 Totale stimato: **{totale_finale:.2f} €**")
        
        if fatt_attuale > 0:
            st.markdown("---")
            st.markdown(f"**Importo Fattura Attuale inserita:** **{fatt_attuale:.2f} €**")
            
            if diff > 0:
                st.success(f"🎉 Risparmio stimato: **{diff:.2f} €**")
            elif diff < 0:
                st.error(f"⚠️ Aumento stimato: **{-diff:.2f} €**")
            else:
                st.info("Totale simulato uguale alla fattura attuale.")

        # ==================================================
        # LOGICA DI DOWNLOAD PDF
        # ==================================================
        
        # Genera i byte del PDF chiamando la funzione
        # La funzione genera_pdf_simulazione gestisce internamente la conversione € -> Eur
        pdf_output = genera_pdf_simulazione(
            cliente,
            periodo_str,
            tipo,
            offerta,
            df, # DataFrame dei risultati
            totale_finale,
            fatt_attuale,
            diff
        )

        # Codifica in Base64
        b64_pdf = base64.b64encode(pdf_output).decode('latin-1')
        filename = f"Report_Simulazione_{tipo}_{cliente.replace(' ', '_')}.pdf"
        
        # Crea il link di download
        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{filename}" style="background-color: #1d6600; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px; font-weight: bold; width:100%; box-sizing:border-box;">⬇️ Scarica Scontrino PDF</a>'
        
        # Mostra il pulsante di download nella terza colonna
        col3.markdown(href, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Errore nel calcolo o generazione PDF: {e}")

st.markdown("---")
st.info("La simulazione è indicativa e non ha valore contrattuale.")
