import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# ==============================
# STILE GENERALE-
# ==============================
st.markdown("""
<style>
/* Corpo */
body {
    background: linear-gradient(90deg, #053c63, #87CEFA);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* HEADER */
.header-container {
    background: linear-gradient(90deg, #053c63, #87CEFA);
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 20px;
}
.header-container img {
    height: 60px;
    margin-right: 15px;
}

/* BUTTON PERSONALIZZATO */
.big-btn {
    background-color: #00BFFF;
    color: white;
    font-size: 18px;
    padding: 10px 0px;
    border-radius: 8px;
    width: 100%;
    font-weight: bold;
    margin-top: 10px;
    margin-bottom: 20px;
}
.big-btn:hover {
    background-color: #009ACD;
}

/* TABLE */
.stTable td, .stTable th {
    padding: 8px;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER
# ==============================
st.markdown("""
<div class="header-container">
    <span style="font-size:32px; font-weight:bold; color:#fff;">Simulatore Luce & Gas DL💡🔥</span>
</div>
""", unsafe_allow_html=True)

# ==============================
# MENU LATERALE
# ==============================
tipo = option_menu(
    menu_title="Seleziona Fornitura",
    options=["Luce", "Gas"],
    icons=["bolt", "fire"],
    menu_icon="solar-panel",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"background-color": "#013566"},
        "nav-link": {"font-size": "18px", "color": "#fafdff"},
        "nav-link:hover": {"background-color": "#0077b6"},
        "nav-link-selected": {"background-color": "#00BFFF", "color": "white"},
    }
)

# ==============================
# COSTANTI & FUNZIONI (uguali a prima)
# ==============================
QUOTA_FISSA_LUCE = 22.80 / 12
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90
ASOS = 0.03

PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178,
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

OFFERTE_LUCE = {"Fast":(0.010,10),"F&F":(0.008,8.5),"Sind":(0.005,7),"Smart":(0.010,12.5)}

PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,10),"F&F":(0.08,8.5),"Sind":(0.05,7),"Smart":(0.10,12.5)}
QUOTA_FISSA_GAS = 15/12
QUOTA_CONSUMO_GAS = 0.025
QUOTA_COMM_GAS = 31 * 0.005452
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50

MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO",
        "LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

def accisa_annua_gas(smc_annuo, regione="Centro-Nord"):
    if smc_annuo <= 120: return 0.044
    elif smc_annuo <= 480: return 0.175
    elif smc_annuo <= 1560: return 0.170 if regione=="Centro-Nord" else 0.120
    else: return 0.186 if regione=="Centro-Nord" else 0.150

def aliquota_iva_gas(smc_annuo):
    return 0.10 if smc_annuo <= 480 else 0.22

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### Inserisci i dati del cliente:")

cliente = st.text_input("Cliente")
periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo kWh")
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
# PULSANTE CALCOLO
# ==============================
if st.button("Calcola Bolletta", key="calc"):
    
    # (qui va IDENTICO il tuo calcolo già pronto)
    try:
        mesi_idx = [MESI.index(mese1)+1] if periodo=="Mensile" else [MESI.index(mese1)+1, MESI.index(mese2)+1]
        num_mesi = len(mesi_idx)
        totale = 0
        righe = []

        if tipo=="Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta]
            prezzo_medio = sum([PUN[m] for m in mesi_idx])/num_mesi + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            sp_rete = kwh * 0.0445
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            iva = max(0, kwh-150*num_mesi)*0.0227 + (materia+sp_rete+quota_pot+oneri+comm_tot)*0.10

            righe += [
                {"Voce":f"Materia Energia ({kwh} kWh)","Importo (€)":f"{materia:.2f}"},
                {"Voce":"Spese rete","Importo (€)":f"{sp_rete:.2f}"},
                {"Voce":"Quota potenza","Importo (€)":f"{quota_pot:.2f}"},
                {"Voce":"Oneri di sistema","Importo (€)":f"{oneri:.2f}"},
                {"Voce":"Commercializ.","Importo (€)":f"{comm_tot:.2f}"},
                {"Voce":"Accise+IVA","Importo (€)":f"{iva:.2f}"}
            ]
            totale += materia+sp_rete+quota_pot+oneri+iva+comm_tot

        else:
            SPREAD, COMM = OFFERTE_GAS[offerta]
            psv_avg = sum([PSV[m] for m in mesi_idx])/num_mesi
            materia = smc*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS
            oneri = ONERI_SISTEMA_GAS*num_mesi + (0.07*smc)+(0.12*smc)
            comm_tot = COMM*num_mesi
            iva = accisa_annua_gas(smc_annuo)*smc + (materia+sp_rete+oneri+comm_tot)*aliquota_iva_gas(smc_annuo)

            righe += [
                {"Voce":f"Materia Energia/PSV","Importo (€)":f"{materia:.2f}"},
                {"Voce":"Spese rete","Importo (€)":f"{sp_rete:.2f}"},
                {"Voce":"Oneri di sistema","Importo (€)":f"{oneri:.2f}"},
                {"Voce":"Commercializ.","Importo (€)":f"{comm_tot:.2f}"},
                {"Voce":"Accise+IVA","Importo (€)":f"{iva:.2f}"}
            ]
            totale += materia+sp_rete+oneri+iva+comm_tot

        for voce, val in [("Bonus Sociale",bonus),("Ricalcoli",ricalcoli),("Altre Partite",altre),("Canone TV",canone_tv)]:
            if val>0:
                righe.append({"Voce":voce,"Importo (€)":f"{val:.2f}"})
                totale+=val

        st.subheader("📊 Scontrino Bolletta DL CEI")
        st.table(pd.DataFrame(righe))
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















