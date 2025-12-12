import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# ==============================
# STILE GENERALE
# ==============================
st.markdown("""
<style>
body { background-color: #E7F5FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.header-container { background: linear-gradient(90deg, #0b0c12, #253073); padding: 20px; text-align: center; border-radius: 12px; margin-bottom: 20px; }
.big-btn { background-color: #00BFFF; color: white; font-size: 18px; padding: 10px 0px; border-radius: 8px; width: 48%; font-weight: bold; margin-top: 10px; margin-bottom: 20px; }
.big-btn:hover { background-color: #009ACD; }
.stTable td, .stTable th { padding: 8px; }
</style>
""", unsafe_allow_html=True)

# ==============================
# HEADER (UNICO)
# ==============================
st.markdown("""
<div class="header-container">
    <span style="font-size:30px; font-weight:bold; color:#fff; display:block;">Simulatore Luce & Gas 💡🔥</span>
    <span style="font-size:18px; font-weight:bold; color:#fff; display:block;">Daniele Lettera Consulenza</span>
</div>
""", unsafe_allow_html=True)

# ==============================
# MENU ORIZZONTALE (UNICO)
# ==============================
# Aggiunto 'key' esplicito per evitare potenziali futuri conflitti, anche se ora non necessario.
tipo = option_menu(
    menu_title=None,
    options=["Luce", "Gas"],
    icons=["bolt", "fire"],
    default_index=0,
    orientation="horizontal",
    key="menu_tipo_energia",
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
PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178, 0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]
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
# INIZIALIZZAZIONE SESSION STATE
# ==============================
for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
    if key not in st.session_state:
        # Inizializza i valori numerici a 0 e gli altri a stringa vuota o valore di default
        if key in ["kwh","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
            st.session_state[key] = 0
        elif key == "kw":
            st.session_state[key] = 3 # Valore di default più comune per la potenza
        else:
            st.session_state[key] = ""

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### Inserisci i dati del cliente:")

cliente = st.text_input("Cliente", st.session_state.cliente).upper()
st.session_state.cliente = cliente

periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo Luce kWh", value=st.session_state.kwh)
    st.session_state.kwh = kwh
    kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6], index=[1,1.5,2,2.5,3,4.5,5,5.5,6].index(st.session_state.kw) if st.session_state.kw in [1,1.5,2,2.5,3,4.5,5,5.5,6] else 4)
    st.session_state.kw = kw
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)", value=0)
else:
    smc = st.number_input("Consumo Gas (m³)", value=st.session_state.smc)
    st.session_state.smc = smc
    smc_annuo = st.number_input("Consumo annuo Gas (m³)", value=st.session_state.smc_annuo)
    st.session_state.smc_annuo = smc_annuo
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()))
    canone_tv = 0

# Ho spostato questi input comuni fuori dall'if/else Luce/Gas e li ho consolidati
# Mantiene la leggibilità e riduce la duplicazione
bonus = st.number_input("Bonus Sociale (€)", value=st.session_state.bonus, key='input_bonus')
ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli, key='input_ricalcoli')
altre = st.number_input("Altre Partite (€)", value=st.session_state.altre, key='input_altre')
fatt_attuale = st.number_input("Importo fattura attuale (€)", value=st.session_state.fatt_attuale, key='input_fatt_attuale')

st.session_state.bonus = bonus
st.session_state.ricalcoli = ricalcoli
st.session_state.altre = altre
st.session_state.fatt_attuale = fatt_attuale

# ==============================
# PULSANTI CALCOLA E RESET
# ==============================
col1, col2 = st.columns(2)
calcola = col1.button("Calcola")
reset = col2.button("Reset")

if reset:
    # Resetta tutti i valori in session_state, inclusi gli input comuni
    for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
        if key in ["kwh","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
            st.session_state[key] = 0
        elif key == "kw":
            st.session_state[key] = 3
        else:
            st.session_state[key] = ""
    st.rerun() # Forza il refresh per resettare i widget

# ==============================
# CALCOLO BOLLETTA
# ==============================
if calcola:
    try:
        # Mesi sono 0-indexed, ma PUN/PSV sono 1-indexed (il primo elemento è 0 per non usarlo)
        # Quindi, se l'utente seleziona 'GENNAIO' (index 0), usiamo PUN[1]
        mesi_idx = [MESI.index(mese1) + 1]
        if periodo=="Bimestrale":
            mesi_idx.append(MESI.index(mese2) + 1)
        num_mesi = len(mesi_idx)
        righe = []

        # ---------------- CALCOLO OFFERTA ----------------
        if tipo == "Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta]
            lista_prezzi = PUN
        else:
            SPREAD, COMM = OFFERTE_GAS[offerta]
            lista_prezzi = PSV

        # ---------------- CALCOLO MATERIA ENERGIA ----------------
        prezzo_medio_indicizzato = sum([lista_prezzi[m] for m in mesi_idx])/num_mesi
        
        if tipo=="Luce":
            prezzo_medio = prezzo_medio_indicizzato + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            costo_unitario = materia / kwh if kwh != 0 else 0
            unita_misura = "kWh"
            consumo = kwh
        else:
            prezzo_medio = prezzo_medio_indicizzato + SPREAD + QUOTA_CONSUMO_GAS
            materia = smc * prezzo_medio
            costo_unitario = materia / smc if smc !=0 else 0
            unita_misura = "m³"
            consumo = smc

        # ---------------- BOX OFFERTA ----------------
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg,#063b0c,#615b02);
            color:white;
            padding:15px;
            border-radius:12px;
            margin-bottom:15px;
        ">
            <h6 style="margin:0;">Cliente: {cliente}</h6>
            <h8 style="margin:0;">Offerta Selezionata: **{offerta}**</h8>
            <p style="margin:0;">Potenza: {kw if tipo=='Luce' else 'N/A'} kW</p>
            <p style="margin:0;">Dettaglio costi:</p>
            <ul style="margin:5px 0 0 15px; padding:0;">
                <li>Costo materia energia per unità: **{prezzo_medio_indicizzato + SPREAD:.4f}** €/{unita_misura} (Indice + Spread)</li>
                <li>Spread: {SPREAD:.4f} €/{unita_misura}</li>
                <li>Commercializzazione: {COMM:.2f} €/mese</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- LUCE ----------------
        if tipo=="Luce":
            sp_rete = kwh * 0.0445 # Costo rete per kWh
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            totale_imponibile = materia + sp_rete + quota_pot + oneri + comm_tot
            iva = totale_imponibile * 0.10 # IVA 10%
            
            righe += [
                {"Descrizione":f"Materia Energia ({consumo:.2f} {unita_misura})", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Quota potenza", "Importo (€)": f"{quota_pot:.2f}"},
                {"Descrizione":"Commercializ. (Quota fissa)", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Spesa per la rete e oneri generali (Variabile)", "Importo (€)": f"{sp_rete + oneri:.2f}"},
                {"Descrizione":"IVA 10%", "Importo (€)": f"{iva:.2f}"}
            ]
            totale = totale_imponibile + iva

        # ---------------- GAS ----------------
        else:
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS # Distr. variabile + fissa
            oneri_var = (0.07*smc)+(0.12*smc) # Oneri variabili
            oneri_fissi = ONERI_SISTEMA_GAS*num_mesi # Oneri fissi
            comm_tot = COMM*num_mesi
            
            accisa = accisa_annua_gas(smc_annuo)*smc
            aliquota_iva = aliquota_iva_gas(smc_annuo)
            totale_imponibile_iva = materia + sp_rete + oneri_var + oneri_fissi + comm_tot # Base per l'IVA
            iva = totale_imponibile_iva * aliquota_iva
            
            righe += [
                {"Descrizione":f"Materia Energia ({consumo:.2f} {unita_misura})", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Spesa per la rete (Fissa+Variabile)", "Importo (€)": f"{sp_rete:.2f}"},
                {"Descrizione":"Commercializ. (Quota fissa)", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Oneri di sistema (Fissi+Variabili)", "Importo (€)": f"{oneri_fissi + oneri_var:.2f}"},
                {"Descrizione":f"Accisa + IVA ({aliquota_iva*100:.0f}%)", "Importo (€)": f"{accisa + iva:.2f}"}
            ]
            totale = totale_imponibile_iva + accisa + iva

        # ---------------- EXTRA ----------------
        if canone_tv > 0:
            righe.append({"Descrizione": "Canone TV", "Importo (€)": f"{canone_tv:.2f}"})
            totale += canone_tv

        for voce, val in [("Bonus Sociale", bonus), ("Ricalcoli", ricalcoli),
                          ("Altre Partite", altre)]:
            if val != 0:
                importo_formattato = f"-{abs(val):.2f}" if val < 0 or voce == "Bonus Sociale" else f"{val:.2f}"
                righe.append({"Descrizione": voce, "Importo (€)": importo_formattato})
                totale += val if voce != "Bonus Sociale" else -val

        # ---------------- RISULTATI ----------------
        df = pd.DataFrame(righe)
        st.subheader("📊 Scontrino Energia DL (Simulato)")
        st.dataframe(df, hide_index=True, width=500)
        st.markdown(f"### 💰 Totale stimato: **{totale:.2f} €**")
        
        if fatt_attuale > 0:
            diff = fatt_attuale - totale
            st.markdown("---")
            st.markdown(f"**Importo Fattura Attuale inserita:** {fatt_attuale:.2f} €")
            if diff > 0:
                st.success(f"🎉 Risparmio stimato: **{diff:.2f} €**")
            elif diff < 0:
                st.error(f"⚠️ Aumento stimato: **{-diff:.2f} €**")
            else:
                st.info("Totale simulato uguale alla fattura attuale.")

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")    styles={
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
PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178, 0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]
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
# SESSION STATE
# ==============================
for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
    if key not in st.session_state:
        if key in ["kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
            st.session_state[key] = 0
        else:
            st.session_state[key] = ""

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### Inserisci i dati del cliente:")
cliente = st.text_input("Cliente", st.session_state.cliente).upper()
st.session_state.cliente = cliente

periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo Luce kWh", value=st.session_state.kwh)
    st.session_state.kwh = kwh
    kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6], index=2)
    st.session_state.kw = kw
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)", value=0)
else:
    smc = st.number_input("Consumo Gas (m³)", value=st.session_state.smc)
    st.session_state.smc = smc
    smc_annuo = st.number_input("Consumo annuo Gas (m³)", value=st.session_state.smc_annuo)
    st.session_state.smc_annuo = smc_annuo
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()))
    canone_tv = 0
    bonus = st.number_input("Bonus Sociale (€)", value=st.session_state.bonus)
    ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli)
    altre = st.number_input("Altre Partite (€)", value=st.session_state.altre)
    fatt_attuale = st.number_input("Importo fattura attuale (€)", value=st.session_state.fatt_attuale)
    st.session_state.bonus = bonus
    st.session_state.ricalcoli = ricalcoli
    st.session_state.altre = altre
    st.session_state.fatt_attuale = fatt_attuale

# ==============================
# PULSANTI
# ==============================
col1, col2 = st.columns(2)
calcola = col1.button("Calcola")
reset = col2.button("Reset")
if reset:
    for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
        st.session_state[key] = 0 if key not in ["cliente"] else ""

# ==============================
# CALCOLO BOLLETTA
# ==============================
if calcola:
    try:
        mesi_idx = [MESI.index(mese1)] if periodo=="Mensile" else [MESI.index(mese1), MESI.index(mese2)]
        num_mesi = len(mesi_idx)
        totale = 0

        SPREAD, COMM = OFFERTE_LUCE[offerta] if tipo=="Luce" else OFFERTE_GAS[offerta]

        if tipo=="Luce":
            prezzo_medio = sum([PUN[m] for m in mesi_idx])/num_mesi + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            costo_unitario = materia / kwh if kwh !=0 else 0
            sp_rete = kwh * 0.0445 * num_mesi
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            iva = (materia+sp_rete+quota_pot+oneri+comm_tot)*0.10
        else:
            psv_avg = sum([PSV[m] for m in mesi_idx])/num_mesi
            materia = smc*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
            costo_unitario = materia / smc if smc !=0 else 0
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS
            oneri = ONERI_SISTEMA_GAS*num_mesi + (0.07*smc)+(0.12*smc)
            comm_tot = COMM*num_mesi
            iva = accisa_annua_gas(st.session_state.smc_annuo)*smc + (materia+sp_rete+oneri+comm_tot)*aliquota_iva_gas(st.session_state.smc_annuo)

        totale = materia + sp_rete + oneri + comm_tot + (iva if tipo=="Gas" else iva)

        # ==============================
        # SCONTRINO HTML
        # ==============================
        scontrino_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color:#F0F4F8; padding:15px; border-radius:12px; width:400px;">

            <!-- Quota per consumi -->
            <div style="background-color:#DFF6FF; padding:10px; border-radius:8px; margin-bottom:10px;">
                <strong>Quota per consumi</strong><br>
                Quantità: {kwh if tipo=='Luce' else smc} {'kWh' if tipo=='Luce' else 'm³'}<br>
                Prezzo medio: {costo_unitario:.4f} €/unità<br>
                Importo: {materia:.2f} €
            </div>

            <!-- Quota fissa e Potenza (solo luce) -->
            {"<div style='background-color:#FFF2CC; padding:10px; border-radius:8px; margin-bottom:10px;'>" +
             "<strong>Quota fissa e Quota Potenza</strong><br>" +
             f"Durata: {num_mesi} mesi<br>" +
             f"Potenza impegnata: {kw} kW<br>" +
             f"Importo: {quota_pot + COMM*num_mesi:.2f} €</div>" if tipo=='Luce' else ""}

            <!-- Spese rete e oneri -->
            <div style="padding:10px; border-radius:8px; margin-bottom:10px; border:1px solid #ccc;">
                Spesa per la rete e oneri generali: {sp_rete + oneri:.2f} €
            </div>

            <!-- Accise e IVA -->
            <div style="padding:10px; border-radius:8px; margin-bottom:10px; border:1px solid #ccc;">
                Accise e IVA: {iva:.2f} €
            </div>

            <!-- Totale -->
            <div style="background-color:#C4F0C5; padding:10px; border-radius:8px; font-weight:bold; font-size:18px; text-align:right;">
                Totale: {totale:.2f} €
            </div>
        </div>
        """
        st.markdown(scontrino_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")
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
# INIZIALIZZAZIONE SESSION STATE
# ==============================
for key in ["cliente","kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
    if key not in st.session_state:
        if key in ["kwh","kw","smc","smc_annuo","bonus","ricalcoli","altre","fatt_attuale"]:
            st.session_state[key] = 0
        else:
            st.session_state[key] = ""

# ==============================
# INPUT UTENTI
# ==============================
st.markdown("### Inserisci i dati del cliente:")

cliente = st.text_input("Cliente", st.session_state.cliente).upper()
st.session_state.cliente = cliente

periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"])
mese1 = st.selectbox("Mese 1", MESI)
mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None

if tipo == "Luce":
    kwh = st.number_input("Consumo Luce kWh", value=st.session_state.kwh)
    st.session_state.kwh = kwh
    kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6], index=2)
    st.session_state.kw = kw
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()))
    canone_tv = st.number_input("Canone TV (€)", value=0)
else:
    smc = st.number_input("Consumo Gas (m³)", value=st.session_state.smc)
    st.session_state.smc = smc
    smc_annuo = st.number_input("Consumo annuo Gas (m³)", value=st.session_state.smc_annuo)
    st.session_state.smc_annuo = smc_annuo
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()))
    canone_tv = 0

bonus = st.number_input("Bonus Sociale (€)", value=st.session_state.bonus)
ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli)
altre = st.number_input("Altre Partite (€)", value=st.session_state.altre)
fatt_attuale = st.number_input("Importo fattura attuale (€)", value=st.session_state.fatt_attuale)

st.session_state.bonus = bonus
st.session_state.ricalcoli = ricalcoli
st.session_state.altre = altre
st.session_state.fatt_attuale = fatt_attuale

# ==============================
# PULSANTI CALCOLA E RESET
# ==============================
col1, col2 = st.columns(2)
calcola = col1.button("Calcola")
reset = col2.button("Reset")

if reset:
    st.session_state.cliente = ""
    st.session_state.kwh = 0
    st.session_state.kw = 2
    st.session_state.smc = 0
    st.session_state.smc_annuo = 0
    st.session_state.bonus = 0
    st.session_state.ricalcoli = 0
    st.session_state.altre = 0
    st.session_state.fatt_attuale = 0

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

        # ---------------- CALCOLO MATERIA ENERGIA ----------------
        if tipo=="Luce":
            prezzo_medio = sum([PUN[m] for m in mesi_idx])/num_mesi + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            costo_unitario = materia / kwh if kwh != 0 else 0
        else:
            psv_avg = sum([PSV[m] for m in mesi_idx])/num_mesi
            materia = smc*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
            costo_unitario = materia / smc if smc !=0 else 0

        # ---------------- BOX OFFERTA ----------------
        st.markdown(f"""
        <div style="
            background: linear-gradient(90deg,#063b0c,#615b02);
            color:white;
            padding:15px;
            border-radius:12px;
            margin-bottom:15px;
        ">
            <h6 style="margin:0;">Cliente: {cliente}</h6>
            <h8 style="margin:0;">Offerta Selezionata: {offerta}</h8>
            <p style="margin:0;">Potenza: {kw if tipo=='Luce' else 'N/A'} kW</p>
            <p style="margin:0;">Dettaglio costi:</p>
            <ul style="margin:5px 0 0 15px; padding:0;">
                <li>Costo materia energia per unità: {costo_unitario:.4f} €/unità</li>
                <li>Spread: {SPREAD:.4f} €/unità</li>
                <li>Commercializzazione: {COMM:.2f} €/mese</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- LUCE ----------------
        if tipo=="Luce":
            sp_rete = kwh * 0.0445 * num_mesi
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            iva = (materia+sp_rete+quota_pot+oneri+comm_tot)*0.10
            righe += [
                {"Descrizione":f"Quota per consumi ({kwh} kWh)", "Importo (€)": f"{materia:.2f}"},
                {"Descrizione":"Spesa per la rete e gli oneri generali", "Importo (€)": f"{sp_rete:.2f}"},
                {"Descrizione":"Quota potenza", "Importo (€)": f"{quota_pot:.2f}"},
                {"Descrizione":"Oneri di sistema", "Importo (€)": f"{oneri:.2f}"},
                {"Descrizione":"Commercializ.", "Importo (€)": f"{comm_tot:.2f}"},
                {"Descrizione":"Accise+IVA", "Importo (€)": f"{iva:.2f}"}
            ]
            totale += materia+sp_rete+quota_pot+oneri+comm_tot+iva

        # ---------------- GAS ----------------
        else:
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
        st.subheader("📊 Scontrino Energia DL")
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
