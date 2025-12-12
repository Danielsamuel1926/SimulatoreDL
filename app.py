import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# ==============================
# STILE GENERALE
# ==============================
st.markdown("""
<style>
body { background-color: #E7F5FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }

.header-container {
    background: linear-gradient(90deg, #0b0c12, #253073);
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 20px;
}

.big-btn {
    background-color: #00BFFF;
    color: white;
    font-size: 18px;
    padding: 10px 0px;
    border-radius: 8px;
    width: 48%;
    font-weight: bold;
    margin-top: 10px;
    margin-bottom: 20px;
}
.big-btn:hover { background-color: #009ACD; }

.stTable td, .stTable th { padding: 8px; }
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown("""
<div class="header-container">
    <span style="font-size:30px; font-weight:bold; color:#fff; display:block;">
        Simulatore Luce & Gas 💡🔥
    </span>
    <span style="font-size:18px; font-weight:bold; color:#fff; display:block;">
        Daniele Lettera Consulenza
    </span>
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
    styles={
        "container": {"background-color": "#c4c4c4"},
        "nav-link": {"font-size": "18px", "color": "#005f91"},
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

PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178,
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

OFFERTE_LUCE = {"Fast":(0.010,10),"F&F":(0.008,8.5),"Sind":(0.005,7),"Smart":(0.010,12.5)}

PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,10),"F&F":(0.08,8.5),"Sind":(0.05,7),"Smart":(0.10,12.5)}

QUOTA_CONSUMO_GAS = 0.025
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50

MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO",
        "LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

def accisa_annua_gas(smc_annuo):
    if smc_annuo <= 120: return 0.044
    elif smc_annuo <= 480: return 0.175
    elif smc_annuo <= 1560: return 0.170
    else: return 0.186

def aliquota_iva_gas(smc_annuo):
    return 0.10 if smc_annuo <= 480 else 0.22

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### Inserisci i dati del cliente:")

cliente = st.text_input("Cliente").upper()
periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo Luce kWh")
    kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6])
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)")
else:
    smc = st.number_input("Consumo Gas (m³)")
    smc_annuo = st.number_input("Consumo annuo Gas (m³)")
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()))
    canone_tv = 0

bonus = st.number_input("Bonus Sociale (€)")
ricalcoli = st.number_input("Ricalcoli (€)")
altre = st.number_input("Altre Partite (€)")
fatt_attuale = st.number_input("Importo fattura attuale (€)")

# ==============================
# PULSANTI CALCOLA E RESET
# ==============================
col1, col2 = st.columns(2)
calcola = col1.button("Calcola", key="calcola")


# ==============================
# CALCOLO BOLLETTA
# ==============================
if calcola:
    try:
        mesi_idx = [MESI.index(mese1)] if periodo=="Mensile" else [MESI.index(mese1), MESI.index(mese2)]
        num_mesi = len(mesi_idx)
        totale = 0
        righe = []

        # ---------------- CALCOLO OFFERTA ----------------
        if tipo == "Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta]
        else:
            SPREAD, COMM = OFFERTE_GAS[offerta]

        # ---------------- BOX OFFERTA ----------------
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg,#00BFFF,#0077b6);
            color:white;
            padding:15px;
            border-radius:12px;
            margin-bottom:15px;
        ">
            <h4 style="margin:0;">Cliente: {cliente}</h4>
            <h4 style="margin:0;">Offerta Selezionata: {offerta}</h4>
            <p style="margin:0;">Potenza: {kw if tipo=='Luce' else 'N/A'} kW</p>
            <p style="margin:0;">Dettaglio costi:</p>
            <ul style="margin:5px 0 0 15px; padding:0;">
                <li>Spread: {SPREAD:.4f} €/unità</li>
                <li>Commercializzazione: {COMM:.2f} €/mese</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- LUCE ----------------
        if tipo=="Luce":
            prezzo_medio = sum([PUN[m] for m in mesi_idx])/num_mesi + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            sp_rete = kwh * 0.0445 * num_mesi
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            iva = (materia+sp_rete+quota_pot+oneri+comm_tot)*0.10

            righe += [
                {"Descrizione":f"Materia Energia ({kwh} kWh)", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Spesa per la rete e gli oneri generali", "Importo (€)": f"{sp_rete:.2f}"},
                {"Descrizione":"Quota potenza", "Importo (€)": f"{quota_pot:.2f}"},
                {"Descrizione":"Oneri di sistema", "Importo (€)": f"{oneri:.2f}"},
                {"Descrizione":"Commercializ.", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Accise+IVA", "Importo (€)": f"{iva:.2f}"}
            ]
            totale += materia+sp_rete+quota_pot+oneri+comm_tot+iva

        # ---------------- GAS ----------------
        else:
            psv_avg = sum([PSV[m] for m in mesi_idx])/num_mesi
            materia = smc*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS
            oneri = ONERI_SISTEMA_GAS*num_mesi + (0.07*smc)+(0.12*smc)
            comm_tot = COMM*num_mesi
            iva = accisa_annua_gas(smc_annuo)*smc + (materia+sp_rete+oneri+comm_tot)*aliquota_iva_gas(smc_annuo)

            righe += [
                {"Descrizione":"Materia Energia/PSV", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Spesa per la rete e gli oneri generali", "Importo (€)": f"{sp_rete:.2f}"},
                {"Descrizione":"Oneri di sistema", "Importo (€)": f"{oneri:.2f}"},
                {"Descrizione":"Commercializ.", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Accise+IVA", "Importo (€)": f"{iva:.2f}"}
            ]
            totale += materia+sp_rete+oneri+comm_tot+iva

        # ---------------- EXTRA ----------------
        for voce, val in [("Bonus Sociale", bonus), ("Ricalcoli", ricalcoli),
                          ("Altre Partite", altre), ("Canone TV", canone_tv)]:
            if val > 0:
                if voce == "Bonus Sociale":
                    righe.append({"Descrizione": voce, "Importo (€)": f"-{val:.2f}"})
                    totale -= val
                else:
                    righe.append({"Descrizione": voce, "Importo (€)": f"{val:.2f}"})
                    totale += val

        # ---------------- RISULTATI ----------------
        df = pd.DataFrame(righe)
        st.subheader("📊 Scontrino Bolletta DL")
        st.dataframe(df, hide_index=True)
        st.markdown(f"### 💰 Totale: **{totale:.2f} €**")
        
        diff = fatt_attuale - totale
        if diff > 0:
            st.success(f"Risparmio: {diff:.2f} €")
        elif diff < 0:
            st.error(f"Aumento: {-diff:.2f} €")
        else:
            st.info("Totale uguale alla fattura attuale.")

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")