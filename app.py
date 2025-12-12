import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

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
}

/* Pulsanti */
div.stButton > button {
    width: 100%;
    border-radius: 8px;
    font-weight: bold;
    height: 40px;
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
ONERI_SISTEMA = 1.90
ASOS = 0.03

# PUN (1-indexed: 0=dummy, 1=Gennaio, ..., 12=Dicembre)
PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178, 
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

OFFERTE_LUCE = {"Fast":(0.010,10),"F&F":(0.008,8.5),"Sind":(0.005,7),"Smart":(0.010,12.5)}

# PSV (1-indexed: 0=dummy, 1=Gennaio, ..., 12=Dicembre)
PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,10),"F&F":(0.08,8.5),"Sind":(0.05,7),"Smart":(0.10,12.5)}

QUOTA_CONSUMO_GAS = 0.025
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50

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
# Inizializza i valori con chiavi univoche
for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
    if key not in st.session_state:
        if key == "kw":
            st.session_state[key] = 3.0
        elif key == "cliente":
            st.session_state[key] = ""
        else:
            st.session_state[key] = 0.0

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
    mese1 = st.selectbox("Mese di Inizio", MESI, key='input_mese1')
with col_mese2:
    if periodo == "Bimestrale":
        mese2 = st.selectbox("Mese di Fine", MESI, key='input_mese2')
    else:
        mese2 = None

# Input Dati Luce/Gas specifici
st.markdown("---")

col_cons_1, col_cons_2 = st.columns(2)

if tipo == "Luce":
    with col_cons_1:
        kwh = st.number_input("Consumo Luce kWh", value=st.session_state.kwh, min_value=0.0, key='input_kwh')
        st.session_state.kwh = kwh
    with col_cons_2:
        kw_options = [1.0, 1.5, 2.0, 2.5, 3.0, 4.5, 5.0, 5.5, 6.0]
        default_index = kw_options.index(st.session_state.kw) if st.session_state.kw in kw_options else 4
        kw = st.selectbox("Potenza impegnata (kW)", kw_options, index=default_index, key='input_kw')
        st.session_state.kw = kw
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()), key='input_offerta_luce')
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
st.markdown("### ➕ Voci Aggiuntive e Confronto:")

col_extra_1, col_extra_2 = st.columns(2)
with col_extra_1:
    bonus = st.number_input("Bonus Sociale (da sottrarre, €)", value=st.session_state.bonus, key='input_bonus')
    ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli, key='input_ricalcoli')
with col_extra_2:
    altre = st.number_input("Altre Partite (€)", value=st.session_state.altre, key='input_altre')
    fatt_attuale = st.number_input("Importo Fattura Attuale per Confronto (€)", value=st.session_state.fatt_attuale, key='input_fatt_attuale')

# Memorizzazione dello stato della sessione (assicura la persistenza dei dati)
# Nota: il cliente è già stato memorizzato sopra
st.session_state.bonus = bonus
st.session_state.ricalcoli = ricalcoli
st.session_state.altre = altre
st.session_state.fatt_attuale = fatt_attuale


# ==============================
# PULSANTI CALCOLA E RESET
# ==============================
st.markdown("---")
col1, col2 = st.columns(2)
calcola = col1.button("▶️ Calcola Simulazione")
reset = col2.button("🗑️ Reset Dati")

if reset:
    # Resetta tutti i valori e ricarica l'app
    for key in ["cliente","kwh","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
        if key == "cliente":
            st.session_state[key] = ""
        else:
            st.session_state[key] = 0.0
    st.session_state.kw = 3.0
    st.rerun()

# ==============================
# CALCOLO BOLLETTA
# ==============================
if calcola:
    st.markdown("## 🧾 Risultato della Simulazione")
    
    try:
        if not st.session_state.cliente:
            st.warning("⚠️ Per favore, inserisci il Nome Cliente per procedere con la simulazione.")
            st.stop()
        
        # Calcolo degli indici del mese (1-indexed per PUN/PSV)
        mesi_idx = [MESI.index(mese1) + 1]
        if periodo=="Bimestrale":
            if mese2 is None:
                st.error("Selezionare il secondo mese per il periodo bimestrale.")
                raise ValueError("Secondo mese non selezionato.")
            mesi_idx.append(MESI.index(mese2) + 1)
        
        num_mesi = len(mesi_idx)
        righe = []

        # --- Dati offerta ---
        if tipo == "Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta]
            lista_prezzi = PUN
            consumo = kwh
            unita_misura = "kWh"
            costo_indicizzato_base = "PUN"
        else:
            SPREAD, COMM = OFFERTE_GAS[offerta]
            lista_prezzi = PSV
            consumo = smc
            unita_misura = "m³"
            costo_indicizzato_base = "PSV"

        # --- Calcolo costi variabili ---
        prezzo_medio_indicizzato = sum([lista_prezzi[m] for m in mesi_idx])/num_mesi
        
        if tipo=="Luce":
            # Costo materia prima: PUN + Spread + Dispacciamento + ASOS (Variabile)
            prezzo_unitario = prezzo_medio_indicizzato + SPREAD + DISPACCIAMENTO + ASOS
            materia = consumo * prezzo_unitario
        else:
            # Costo materia prima: PSV + Spread + Quota Consumo Gas (Variabile)
            prezzo_unitario = prezzo_medio_indicizzato + SPREAD + QUOTA_CONSUMO_GAS
            materia = consumo * prezzo_unitario

        costo_unitario_display = materia / consumo if consumo != 0 else 0

        # --- BOX DETTAGLIO COSTI ---
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg, #186020, #968a11);
            color:white;
            padding:15px;
            border-radius:12px;
            margin-bottom:15px;
        ">
            <h6 style="margin:0;">**{st.session_state.cliente}** -  Offerta: **{offerta}**</h6>
            <p style="margin:0; font-size:14px;">Periodo: {mese1} {f"e {mese2}" if periodo=='Bimestrale' else ""}</p>
            <p style="margin:5px 0 0 0; font-weight:bold;">Costo Totale Materia ({costo_indicizzato_base} + spread): {prezzo_unitario:.4f} €/{unita_misura}</p>
        </div>
        """, unsafe_allow_html=True)

        totale = 0.0

        # ---------------- LUCE (Energia Elettrica) ----------------
        if tipo=="Luce":
            # Spesa per la Rete (Quota Variabile)
            sp_rete_variabile = consumo * 0.0445
            # Quota Potenza (Fissa)
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            # Oneri di Sistema (Fissi)
            oneri = ONERI_SISTEMA * num_mesi
            # Commercializzazione (Fissa)
            comm_tot = COMM * num_mesi
            
            # Base Imponibile IVA 10%
            totale_imponibile = materia + sp_rete_variabile + quota_pot + oneri + comm_tot
            iva = totale_imponibile * 0.10
            
            righe += [
                {"Descrizione":f"Materia Energia ({consumo:.2f} {unita_misura})", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Commercializ. (Fissa)", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Quota Potenza (Fissa)", "Importo (€)": f"{quota_pot:.2f}"},
                {"Descrizione":"Oneri di sistema (Fissi)", "Importo (€)": f"{oneri:.2f}"},
                {"Descrizione":"Spesa Rete (Variabile)", "Importo (€)": f"{sp_rete_variabile:.2f}"},
                {"Descrizione":"IVA 10%", "Importo (€)": f"{iva:.2f}"}
            ]
            totale = totale_imponibile + iva

        # ---------------- GAS (Gas Naturale) ----------------
        else:
            # Spesa per la Rete (Fissa + Variabile)
            sp_rete = QUOTA_VAR_DIST_GAS * consumo + QUOTA_DIST_GAS
            
            # Oneri di Sistema (Fissi + Variabili)
            oneri_fissi = ONERI_SISTEMA_GAS * num_mesi
            oneri_var = (0.07 * consumo) + (0.12 * consumo)
            
            # Commercializzazione (Fissa)
            comm_tot = COMM * num_mesi
            
            # Accise (Variabili)
            accisa = accisa_annua_gas(smc_annuo) * consumo
            
            # IVA
            aliquota_iva = aliquota_iva_gas(smc_annuo)
            totale_imponibile_iva = materia + sp_rete + oneri_var + oneri_fissi + comm_tot
            iva = totale_imponibile_iva * aliquota_iva
            
            righe += [
                {"Descrizione":f"Materia Energia/PSV ({consumo:.2f} {unita_misura})", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Commercializ. (Fissa)", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Spesa Rete (Fissa + Variabile)", "Importo (€)": f"{sp_rete:.2f}"},
                {"Descrizione":"Oneri di sistema (Fissi + Variabili)", "Importo (€)": f"{oneri_fissi + oneri_var:.2f}"},
                {"Descrizione":f"Accisa + IVA ({aliquota_iva*100:.0f}%)", "Importo (€)": f"{accisa + iva:.2f}"}
            ]
            totale = totale_imponibile_iva + accisa + iva

        # ---------------- EXTRA (Canone TV, Bonus, Ricalcoli) ----------------
        # Voci Aggiuntive/Sottrattive
        if canone_tv > 0:
            righe.append({"Descrizione": "Canone TV", "Importo (€)": f"{canone_tv:.2f}"})
            totale += canone_tv

        for voce, val in [("Ricalcoli", ricalcoli), ("Altre Partite", altre)]:
            if val != 0:
                righe.append({"Descrizione": voce, "Importo (€)": f"{val:.2f}"})
                totale += val
        
        # Il bonus sociale va sempre sottratto
        if bonus > 0:
             righe.append({"Descrizione": "Bonus Sociale", "Importo (€)": f"{-abs(bonus):.2f}"})
             totale -= abs(bonus)
        
        # --- RISULTATI ---
        df = pd.DataFrame(righe)
        st.dataframe(df, hide_index=True, use_container_width=True)
        
        totale_finale = max(0, totale) # Il totale non può essere negativo
        
        st.markdown(f"### 💰 Totale stimato: **{totale_finale:.2f} €**")
        
        # Confronto con la fattura attuale
        if fatt_attuale > 0:
            diff = fatt_attuale - totale_finale
            st.markdown("---")
            st.markdown(f"**Importo Fattura Attuale inserita:** **{fatt_attuale:.2f} €**")
            
            if diff > 0:
                st.success(f"🎉 Risparmio stimato: **{diff:.2f} €**")
            elif diff < 0:
                st.error(f"⚠️ Aumento stimato: **{-diff:.2f} €**")
            else:
                st.info("Totale simulato uguale alla fattura attuale.")

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")

st.markdown("---")
st.info("La simulazione è indicativa e ha valore contrattuale.")
