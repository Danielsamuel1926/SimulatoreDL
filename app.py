import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
from io import BytesIO
import smtplib
from email.message import EmailMessage

# ==============================
# CONFIG PAGE
# ==============================
st.set_page_config(page_title="Simulatore Luce & Gas", layout="centered")

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
.small-muted { color: #555; font-size:12px; }
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

OFFERTE_LUCE = {"Fast": (0.010, 10), "F&F": (0.008, 8.5), "Sind": (0.005, 7), "Smart": (0.010, 12.5)}

PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast": (0.10, 10), "F&F": (0.08, 8.5), "Sind": (0.05, 7), "Smart": (0.10, 12.5)}

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
# HELPERS
# ==============================
def reset_all():
    keys = ["cliente","periodo","mese1","mese2","kwh","kw","offerta","smc","smc_annuo",
            "canone_tv","bonus","ricalcoli","altre","fatt_attuale","email_dest"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    st.experimental_rerun()

def prepare_offerval_and_compute(mesi_idx, num_mesi, tipo_sel, inputs):
    """
    Returns: (righe_list, totale, SPREAD, COMM, costo_materia_unitario)
    costo_materia_unitario = materia / consumo (€/kWh or €/Smc) — version A requested
    """
    righe = []
    totale = 0.0
    if tipo_sel == "Luce":
        SPREAD, COMM = OFFERTE_LUCE[inputs['offerta']]
        prezzo_medio = sum([PUN[m] for m in mesi_idx]) / num_mesi + SPREAD + DISPACCIAMENTO + ASOS
        materia = inputs['kwh'] * prezzo_medio
        costo_materia_kwh = (materia / inputs['kwh']) if inputs['kwh'] > 0 else 0.0

        sp_rete = inputs['kwh'] * 0.0445 * num_mesi
        quota_pot = inputs['kw'] * QUOTA_POTENZA * num_mesi
        oneri = ONERI_SISTEMA * num_mesi
        comm_tot = COMM * num_mesi
        iva = (materia + sp_rete + quota_pot + oneri + comm_tot) * 0.10

        righe += [
            {"Descrizione": f"Materia Energia ({inputs['kwh']} kWh)", "Importo (€)": f"{materia:.2f}"},
            {"Descrizione": "Spesa per la rete e gli oneri generali", "Importo (€)": f"{sp_rete:.2f}"},
            {"Descrizione": "Quota potenza", "Importo (€)": f"{quota_pot:.2f}"},
            {"Descrizione": "Oneri di sistema", "Importo (€)": f"{oneri:.2f}"},
            {"Descrizione": "Commercializ.", "Importo (€)": f"{comm_tot:.2f}"},
            {"Descrizione": "Accise+IVA", "Importo (€)": f"{iva:.2f}"}
        ]
        totale = materia + sp_rete + quota_pot + oneri + comm_tot + iva
        return righe, totale, SPREAD, COMM, costo_materia_kwh

    else:  # Gas
        SPREAD, COMM = OFFERTE_GAS[inputs['offerta']]
        psv_avg = sum([PSV[m] for m in mesi_idx]) / num_mesi
        materia = inputs['smc'] * (psv_avg + SPREAD + QUOTA_CONSUMO_GAS)
        costo_materia_smc = (materia / inputs['smc']) if inputs['smc'] > 0 else 0.0

        sp_rete = QUOTA_VAR_DIST_GAS * inputs['smc'] + QUOTA_DIST_GAS
        oneri = ONERI_SISTEMA_GAS * num_mesi + (0.07 * inputs['smc']) + (0.12 * inputs['smc'])
        comm_tot = COMM * num_mesi
        iva = accisa_annua_gas(inputs.get('smc_annuo', 0)) * inputs['smc'] + (materia + sp_rete + oneri + comm_tot) * aliquota_iva_gas(inputs.get('smc_annuo', 0))

        righe += [
            {"Descrizione": "Materia Energia/PSV", "Importo (€)": f"{materia:.2f}"},
            {"Descrizione": "Spesa per la rete e gli oneri generali", "Importo (€)": f"{sp_rete:.2f}"},
            {"Descrizione": "Oneri di sistema", "Importo (€)": f"{oneri:.2f}"},
            {"Descrizione": "Commercializ.", "Importo (€)": f"{comm_tot:.2f}"},
            {"Descrizione": "Accise+IVA", "Importo (€)": f"{iva:.2f}"}
        ]
        totale = materia + sp_rete + oneri + comm_tot + iva
        return righe, totale, SPREAD, COMM, costo_materia_smc

def send_email_with_attachment(to_email: str, subject: str, body: str, attachment_bytes: BytesIO, attachment_name: str = "scontrino.xlsx"):
    """
    Sends email using SMTP details specified in st.secrets['smtp'].
    st.secrets['smtp'] must contain: host, port, username, password, from
    """
    if 'smtp' not in st.secrets:
        raise RuntimeError("SMTP non configurato. Metti i dati in st.secrets['smtp'] per abilitare l'invio.")
    cfg = st.secrets['smtp']
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = cfg.get('from', cfg.get('username'))
    msg['To'] = to_email
    msg.set_content(body)

    if attachment_bytes is not None:
        attachment_bytes.seek(0)
        data = attachment_bytes.read()
        msg.add_attachment(data, maintype='application', subtype='vnd.openxmlformats-officedocument.spreadsheetml.sheet', filename=attachment_name)

    host = cfg.get('host')
    port = int(cfg.get('port', 465))
    username = cfg.get('username')
    password = cfg.get('password')

    with smtplib.SMTP_SSL(host, port) as smtp:
        smtp.login(username, password)
        smtp.send_message(msg)

# ==============================
# INPUT UTENTI (session_state to allow reset)
# ==============================
if 'cliente' not in st.session_state: st.session_state.cliente = ""
cliente = st.text_input("Cliente", value=st.session_state.cliente).upper()
st.session_state.cliente = cliente

if 'periodo' not in st.session_state: st.session_state.periodo = "Mensile"
periodo = st.selectbox("Periodo", ["Mensile", "Bimestrale"], index=0, key="periodo")

if 'mese1' not in st.session_state: st.session_state.mese1 = MESI[0]
mese1 = st.selectbox("Mese 1", MESI, index=0, key="mese1")

if 'mese2' not in st.session_state: st.session_state.mese2 = MESI[0]
mese2 = st.selectbox("Mese 2", MESI, index=0, key="mese2") if periodo == "Bimestrale" else None

if tipo == "Luce":
    if 'kwh' not in st.session_state: st.session_state.kwh = 0.0
    kwh = st.number_input("Consumo Luce kWh", value=st.session_state.kwh, key="kwh")
    st.session_state.kwh = kwh

    POTENZE = [1,1.5,2,2.5,3,4.5,5,5.5,6]
    if 'kw' not in st.session_state: st.session_state.kw = POTENZE[0]
    kw = st.selectbox("Potenza impegnata (kW)", POTENZE, index=POTENZE.index(st.session_state.kw) if st.session_state.kw in POTENZE else 0, key="kw")
    st.session_state.kw = kw

    if 'offerta' not in st.session_state: st.session_state.offerta = list(OFFERTE_LUCE.keys())[0]
    offerta = st.selectbox("Offerta Luce", list(OFFERTE_LUCE.keys()), index=list(OFFERTE_LUCE.keys()).index(st.session_state.offerta), key="offerta")
    st.session_state.offerta = offerta

    if 'canone_tv' not in st.session_state: st.session_state.canone_tv = 0.0
    canone_tv = st.number_input("Canone TV (€)", value=st.session_state.canone_tv, key="canone_tv")
    st.session_state.canone_tv = canone_tv

else:
    if 'smc' not in st.session_state: st.session_state.smc = 0.0
    smc = st.number_input("Consumo Gas (m³)", value=st.session_state.smc, key="smc")
    st.session_state.smc = smc

    if 'smc_annuo' not in st.session_state: st.session_state.smc_annuo = 0.0
    smc_annuo = st.number_input("Consumo annuo Gas (m³)", value=st.session_state.smc_annuo, key="smc_annuo")
    st.session_state.smc_annuo = smc_annuo

    if 'offerta' not in st.session_state: st.session_state.offerta = list(OFFERTE_GAS.keys())[0]
    offerta = st.selectbox("Offerta Gas", list(OFFERTE_GAS.keys()), index=list(OFFERTE_GAS.keys()).index(st.session_state.offerta), key="offerta")
    st.session_state.offerta = offerta

    canone_tv = 0.0

if 'bonus' not in st.session_state: st.session_state.bonus = 0.0
bonus = st.number_input("Bonus Sociale (€)", value=st.session_state.bonus, key="bonus")
st.session_state.bonus = bonus

if 'ricalcoli' not in st.session_state: st.session_state.ricalcoli = 0.0
ricalcoli = st.number_input("Ricalcoli (€)", value=st.session_state.ricalcoli, key="ricalcoli")
st.session_state.ricalcoli = ricalcoli

if 'altre' not in st.session_state: st.session_state.altre = 0.0
altre = st.number_input("Altre Partite (€)", value=st.session_state.altre, key="altre")
st.session_state.altre = altre

if 'fatt_attuale' not in st.session_state: st.session_state.fatt_attuale = 0.0
fatt_attuale = st.number_input("Importo fattura attuale (€)", value=st.session_state.fatt_attuale, key="fatt_attuale")
st.session_state.fatt_attuale = fatt_attuale

# buttons row: calcola + reset
col1, col2 = st.columns(2)
calcola = col1.button("Calcola")
reset_btn = col2.button("Reset")

if reset_btn:
    reset_all()

# ==============================
# LOGICA CALCOLO
# ==============================
if calcola:
    try:
        mesi_idx = [MESI.index(mese1)] if periodo == "Mensile" else [MESI.index(mese1), MESI.index(mese2)]
        num_mesi = len(mesi_idx)

        inputs = {
            'offerta': offerta,
            'kwh': kwh if tipo == "Luce" else 0.0,
            'kw': kw if tipo == "Luce" else 0.0,
            'smc': smc if tipo == "Gas" else 0.0,
            'smc_annuo': smc_annuo if tipo == "Gas" else 0.0,
        }

        righe, totale, SPREAD, COMM, costo_materia_unit = prepare_offerval_and_compute(mesi_idx, num_mesi, tipo, inputs)

        # extras
        extras = [("Bonus Sociale", bonus), ("Ricalcoli", ricalcoli), ("Altre Partite", altre), ("Canone TV", canone_tv)]
        for voce, val in extras:
            if val and val != 0:
                if voce == "Bonus Sociale":
                    righe.append({"Descrizione": voce, "Importo (€)": f"-{val:.2f}"})
                    totale -= val
                else:
                    righe.append({"Descrizione": voce, "Importo (€)": f"{val:.2f}"})
                    totale += val

        # ---------------- BOX OFFERTA (with costo materia reale) ----------------
        if tipo == "Luce":
            costo_unit_label = f"{costo_materia_unit:.4f} €/kWh"
            potenza_display = f"{kw} kW"
        else:
            costo_unit_label = f"{costo_materia_unit:.4f} €/Smc"
            potenza_display = "N/A"

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
            <p style="margin:0;">Potenza: {potenza_display}</p>
            <p style="margin:0; margin-top:8px;">Dettaglio costi:</p>
            <ul style="margin:5px 0 0 15px; padding:0;">
                <li>Spread: {SPREAD:.4f} €/unità</li>
                <li>Commercializzazione: {COMM:.2f} €/mese</li>
                <li><b>Costo materia energia reale: {costo_unit_label}</b></li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ---------------- SCONTRINO / RISULTATI ----------------
        df = pd.DataFrame(righe)
        st.subheader("📊 Scontrino Bolletta")
        st.dataframe(df, hide_index=True)
        st.markdown(f"### 💰 Totale: **{totale:.2f} €**")

        diff = fatt_attuale - totale
        if diff > 0:
            st.success(f"Risparmio: {diff:.2f} €")
        elif diff < 0:
            st.error(f"Aumento: {-diff:.2f} €")
        else:
            st.info("Totale uguale alla fattura attuale.")

        # ---------------- DOWNLOAD / EMAIL ----------------
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False, sheet_name="Scontrino")
        excel_buffer.seek(0)

        st.download_button("📥 Scarica riepilogo (Excel)", excel_buffer, file_name="scontrino.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("----")
        st.markdown("### Invia risultati via email (opzionale)")
        st.markdown("Per invio automatico via SMTP: aggiungi st.secrets['smtp'] con host/port/username/password/from.")
        email_dest = st.text_input("Email destinatario", key="email_dest")
        if st.button("📧 Invia Email"):
            if not email_dest:
                st.error("Inserisci un'email destinatario.")
            else:
                try:
                    subject = f"Bolletta simulata - {cliente}"
                    body = f"Salve,\n\nin allegato trova il riepilogo della bolletta simulata per {cliente}.\nTotale: {totale:.2f} €\n\nCordiali saluti."
                    send_email_with_attachment(email_dest, subject, body, excel_buffer, "scontrino.xlsx")
                    st.success("Email inviata con allegato (verificare log del server).")
                except Exception as ex:
                    st.error(f"Impossibile inviare email: {ex}")
                    st.info("Se non vuoi/puoi configurare SMTP, scarica l'Excel e invialo manualmente.")

    except Exception as e:
        st.error(f"Errore nel calcolo: {e}")