import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# ================================
# STILE AZIENDALE (CSS)
# ================================
st.markdown("""
<style>
body { background-color: #E8F4FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.header-container { background: linear-gradient(90deg, #03529c, #00a8e8); padding: 25px; text-align: center; border-radius: 12px; margin-bottom: 25px; display: flex; align-items: center; justify-content: center; }
.header-container img { height: 55px; margin-right: 15px; }
.header-container span { font-size: 32px; font-weight: 700; color: white; letter-spacing: 1px; }
.card { background: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0,0,0,0.1); margin-bottom: 25px; border-left: 5px solid #0077b6; }
thead tr th { background-color: #0077b6 !important; color: white !important; }
tbody tr:nth-child(even) { background-color: #e0f0ff !important; }
</style>
""", unsafe_allow_html=True)

# ================================
# HEADER
# ================================
st.markdown("""
<div class="header-container">
    <span>Simulatore Luce & Gas 💡🔥</span>
</div>
""", unsafe_allow_html=True)

# ================================
# MENU
# ================================
tipo = option_menu(
    menu_title=None,
    options=["Luce", "Gas"],
    icons=["bolt", "fire"],
    orientation="horizontal",
    default_index=0
)

# ================================
# DATI E COSTI
# ================================
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90
ASOS = 0.03

PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178,
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

# Spread e commissione di commercializzazione separati per offerta
OFFERTA_LUCE = {
    "Fast": {"spread": 0.010, "comm": 10},
    "F&F": {"spread": 0.008, "comm": 8.5},
    "Sind": {"spread": 0.005, "comm": 7},
    "Smart": {"spread": 0.010, "comm": 12.5}
}

PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTA_GAS = {
    "Fast": {"spread": 0.10, "comm": 10},
    "F&F": {"spread": 0.08, "comm": 8.5},
    "Sind": {"spread": 0.05, "comm": 7},
    "Smart": {"spread": 0.10, "comm": 12.5}
}

MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO",
        "LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

def accisa_annua_gas(smc_annuo):
    if smc_annuo <= 120: return 0.044
    elif smc_annuo <= 480: return 0.175
    elif smc_annuo <= 1560: return 0.170
    else: return 0.186

def aliquota_iva_gas(smc_annuo):
    return 0.10 if smc_annuo <= 480 else 0.22

# ================================
# INPUT DATI
# ================================
st.markdown("<div class='card'><h3>Dati Cliente</h3></div>", unsafe_allow_html=True)

cliente = st.text_input("Cliente")
periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo kWh", min_value=0.0)
    kw = st.selectbox("Potenza impegnata", [1,1.5,2,2.5,3,4.5,5,5.5,6])
    offerta = st.selectbox("Offerta Luce", list(OFFERTA_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)", min_value=0.0)
else:
    smc = st.number_input("Consumo Gas (m³)")
    smc_annuo = st.number_input("Consumo annuo Gas (m³)")
    offerta = st.selectbox("Offerta Gas", list(OFFERTA_GAS.keys()))
    canone_tv = 0

bonus = st.number_input("Bonus Sociale (€)", min_value=0.0)
ricalcoli = st.number_input("Ricalcoli (€)", min_value=0.0)
altre = st.number_input("Altre Partite (€)", min_value=0.0)
fatt_attuale = st.number_input("Importo fattura attuale (€)", min_value=0.0)

# ================================
# CALCOLO
# ================================
if st.button("Calcola Bolletta"):

    try:
        mesi_idx = [MESI.index(mese1)] if periodo=="Mensile" else [MESI.index(mese1), MESI.index(mese2)]
        num_mesi = len(mesi_idx)
        totale = 0
        righe = []

        if tipo == "Luce":
            spread = OFFERTA_LUCE[offerta]["spread"]
            comm = OFFERTA_LUCE[offerta]["comm"]

            # Materia energia mese per mese (senza commissione)
            materia = sum(kwh * (PUN[m] + DISPACCIAMENTO + ASOS + spread) for m in mesi_idx)

            sp_rete = kwh * 0.0445 * num_mesi
            q_pot = kw * QUOTA_POTENZA * num_mesi
            comm_tot = comm * num_mesi
            iva = (materia + sp_rete + q_pot + comm_tot) * 0.10

            righe += [
                {"Voce":"Materia Energia", "Importo (€)":f"{materia:.2f}"},
                {"Voce":"Spese Rete", "Importo (€)":f"{sp_rete:.2f}"},
                {"Voce":"Quota Potenza", "Importo (€)":f"{q_pot:.2f}"},
                {"Voce":"Oneri di Sistema", "Importo (€)":f"{ONERI_SISTEMA*num_mesi:.2f}"},
                {"Voce":"Spread Offerta", "Importo (€)":f"{spread*kwh*num_mesi:.2f}"},
                {"Voce":"Commissione Commercializzazione", "Importo (€)":f"{comm_tot:.2f}"},
                {"Voce":"IVA", "Importo (€)":f"{iva:.2f}"}
            ]

            totale += materia + sp_rete + q_pot + ONERI_SISTEMA*num_mesi + spread*kwh*num_mesi + comm_tot + iva

        else:
            spread = OFFERTA_GAS[offerta]["spread"]
            comm = OFFERTA_GAS[offerta]["comm"]

            materia = sum(smc * (PSV[m] + 0.025 + spread) for m in mesi_idx)
            sp_rete = 0.171530 * smc + 31 * 0.140658
            oneri = 1.50 * num_mesi + (0.07 * smc) + (0.12 * smc)
            comm_tot = comm * num_mesi
            accise = accisa_annua_gas(smc_annuo) * smc
            iva = (materia + sp_rete + oneri + comm_tot) * aliquota_iva_gas(smc_annuo)

            righe += [
                {"Voce":"Materia Energia/PSV", "Importo (€)":f"{materia:.2f}"},
                {"Voce":"Spese Rete", "Importo (€)":f"{sp_rete:.2f}"},
                {"Voce":"Oneri di Sistema", "Importo (€)":f"{oneri:.2f}"},
                {"Voce":"Spread Offerta", "Importo (€)":f"{spread*smc*num_mesi:.2f}"},
                {"Voce":"Commissione Commercializzazione", "Importo (€)":f"{comm_tot:.2f}"},
                {"Voce":"Accise", "Importo (€)":f"{accise:.2f}"},
                {"Voce":"IVA", "Importo (€)":f"{iva:.2f}"}
            ]

            totale += materia + sp_rete + oneri + spread*smc*num_mesi + comm_tot + accise + iva

        # Extra
        for voce, val in [("Bonus Sociale", bonus), ("Ricalcoli", ricalcoli), ("Altre Partite", altre), ("Canone TV", canone_tv)]:
            if val > 0:
                righe.append({"Voce": voce, "Importo (€)": f"{val:.2f}"})
                totale += val

        # Risultati
        st.subheader("📊 Scontrino Bolletta")
        st.table(pd.DataFrame(righe))

        st.markdown(f"""
        <div style="
        background:#0077b6;
        color:white;
        padding:18px;
        border-radius:12px;
        font-size:22px;
        text-align:center;
        margin-top:25px;
        box-shadow:0px 4px 10px rgba(0,0,0,0.2);
        ">
        💰 Totale Bolletta: <b>{totale:.2f} €</b>
        </div>
        """, unsafe_allow_html=True)

        diff = fatt_attuale - totale
        if diff > 0:
            st.success(f"Risparmio: {diff:.2f} €")
        elif diff < 0:
            st.error(f"Aumento: {-diff:.2f} €")
        else:
            st.info("Totale uguale alla fattura attuale.")

    except Exception as e:
        st.error(f"Errore: {e}")

















