import streamlit as st
import pandas as pd
from fpdf import FPDF
from streamlit_option_menu import option_menu
from io import BytesIO
import smtplib
from email.message import EmailMessage

# ==============================
# STILE
# ==============================
st.markdown("""
<style>
body { background-color: #E7F5FF; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
.header-container {
    background: linear-gradient(90deg,#101447,#0077b6);
    padding: 20px; text-align: center; border-radius: 12px; margin-bottom: 20px;
}
.stTable td, .stTable th { padding: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <h2 style="color:white; margin:0;">Simulatore Luce & Gas 💡🔥</h2>
    <h4 style="color:white; margin:0;">Daniele Lettera Consulenza</h4>
</div>
""", unsafe_allow_html=True)

# ==============================
# COSTANTI
# ==============================
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90
ASOS = 0.03
PUN = [0,0.14303,0.15036,0.12055,0.09985,0.09358,0.11178,0.11313,0.10879,0.10908,0.11104,0.11709,0.10800]
OFFERTE_LUCE = {"Fast":(0.010,10),"F&F":(0.008,8.5),"Sind":(0.005,7),"Smart":(0.010,12.5)}
PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,10),"F&F":(0.08,8.5),"Sind":(0.05,7),"Smart":(0.10,12.5)}
QUOTA_CONSUMO_GAS = 0.025
QUOTA_DIST_GAS = 31*0.140658
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
# FUNZIONI
# ==============================
def reset_inputs():
    for key in st.session_state.keys():
        st.session_state[key] = None

def genera_scontrino(cliente, tipo, mesi_idx, offerta, dati, extra):
    SPREAD, COMM = offerta
    box_offerta = f"Offerta: {tipo}\nSpread: {SPREAD}\nCommercializzazione: {COMM}"
    righe = []
    totale = 0

    if tipo=="Luce":
        prezzo_medio = sum([dati["PUN"][m] for m in mesi_idx])/len(mesi_idx)+SPREAD+DISPACCIAMENTO+ASOS
        materia = dati["kwh"]*prezzo_medio
        sp_rete = dati["kwh"]*0.0445*len(mesi_idx)
        quota_pot = dati["kw"]*QUOTA_POTENZA*len(mesi_idx)
        oneri = ONERI_SISTEMA*len(mesi_idx)
        comm_tot = COMM*len(mesi_idx)
        iva = (materia+sp_rete+quota_pot+oneri+comm_tot)*0.10
        righe += [
            {"Voce":f"Spesa energia ({dati['kwh']} kWh)","Importo (€)":f"{materia:.2f}"},
            {"Voce":"Rete e oneri","Importo (€)":f"{sp_rete:.2f}"},
            {"Voce":"Quota potenza","Importo (€)":f"{quota_pot:.2f}"},
            {"Voce":"Oneri di sistema","Importo (€)":f"{oneri:.2f}"},
            {"Voce":"Commercializ.","Importo (€)":f"{comm_tot:.2f}"},
            {"Voce":"IVA","Importo (€)":f"{iva:.2f}"}
        ]
        totale = materia+sp_rete+quota_pot+oneri+comm_tot+iva
    else:
        psv_avg = sum([PSV[m] for m in mesi_idx])/len(mesi_idx)
        materia = dati["smc"]*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
        sp_rete = QUOTA_VAR_DIST_GAS*dati["smc"]+QUOTA_DIST_GAS
        oneri = ONERI_SISTEMA_GAS*len(mesi_idx)+(0.07*dati["smc"])+(0.12*dati["smc"])
        comm_tot = COMM*len(mesi_idx)
        iva = accisa_annua_gas(dati["smc_annuo"])*dati["smc"]+(materia+sp_rete+oneri+comm_tot)*aliquota_iva_gas(dati["smc_annuo"])
        righe += [
            {"Voce":"Materia Energia/PSV","Importo (€)":f"{materia:.2f}"},
            {"Voce":"Rete e oneri","Importo (€)":f"{sp_rete:.2f}"},
            {"Voce":"Oneri di sistema","Importo (€)":f"{oneri:.2f}"},
            {"Voce":"Commercializ.","Importo (€)":f"{comm_tot:.2f}"},
            {"Voce":"IVA","Importo (€)":f"{iva:.2f}"}
        ]
        totale = materia+sp_rete+oneri+comm_tot+iva

    for voce, val in extra.items():
        if val>0:
            if voce=="Bonus Sociale":
                righe.append({"Voce":voce,"Importo (€)":f"-{val:.2f}"})
                totale -= val
            else:
                righe.append({"Voce":voce,"Importo (€)":f"{val:.2f}"})
                totale += val

    df = pd.DataFrame(righe)
    return df, box_offerta, totale

def crea_pdf(df, box_offerta, totale, cliente):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",14)
    pdf.cell(0,10,f"Bolleta Simulata - {cliente}",ln=True,align="C")
    pdf.ln(5)
    pdf.set_font("Arial","B",12)
    pdf.multi_cell(0,6,f"Box Offerta:\n{box_offerta}")
    pdf.ln(5)
    pdf.set_font("Arial","",12)
    for i,row in df.iterrows():
        pdf.cell(0,6,f"{row['Voce']}: {row['Importo (€)']}",ln=True)
    pdf.ln(5)
    pdf.set_font("Arial","B",12)
    pdf.cell(0,6,f"Totale: {totale:.2f} €",ln=True)
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

def invia_mail(destinatario, soggetto, corpo, allegato_bytes=None, allegato_nome="scontrino.pdf"):
    msg = EmailMessage()
    msg['Subject'] = soggetto
    msg['From'] = "tuo@email.com"
    msg['To'] = destinatario
    msg.set_content(corpo)
    if allegato_bytes:
        msg.add_attachment(allegato_bytes.getvalue(), maintype="application", subtype="pdf", filename=allegato_nome)
    with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
        smtp.login("tuo@email.com","password_app")
        smtp.send_message(msg)

# ==============================
# FORM INPUT
# ==============================
with st.form("form_bolletta"):
    cliente = st.text_input("Cliente")
    periodo = st.selectbox("Periodo",["Mensile","Bimestrale"])
    mese1 = st.selectbox("Mese 1", MESI)
    mese2 = st.selectbox("Mese 2", MESI) if periodo=="Bimestrale" else None
    tipo = st.selectbox("Tipo Fornitura", ["Luce","Gas"])
    if tipo=="Luce":
        kwh = st.number_input("Consumo kWh")
        kw = st.number_input("Potenza kW")
        offerta_sel = st.selectbox("Offerta", list(OFFERTE_LUCE.keys()))
    else:
        smc = st.number_input("Consumo Gas")
        smc_annuo = st.number_input("Consumo annuo Gas")
        offerta_sel = st.selectbox("Offerta", list(OFFERTE_GAS.keys()))
    canone_tv = st.number_input("Canone TV (€)")
    bonus = st.number_input("Bonus Sociale (€)")
    ricalcoli = st.number_input("Ricalcoli (€)")
    altre = st.number_input("Altre Partite (€)")
    fatt_attuale = st.number_input("Fattura Attuale (€)")
    col1,col2 = st.columns(2)
    with col1:
        calcola = st.form_submit_button("Calcola")
    with col2:
        reset = st.form_submit_button("Reset")

if reset:
    reset_inputs()

if calcola:
    mesi_idx = [MESI.index(mese1)] if periodo=="Mensile" else [MESI.index(mese1),MESI.index(mese2)]
    extra = {"Bonus Sociale":bonus,"Ricalcoli":ricalcoli,"Altre Partite":altre,"Canone TV":canone_tv}
    off_val = OFFERTE_LUCE[offerta_sel] if tipo=="Luce" else OFFERTE_GAS[offerta_sel]
    dati = {"PUN":PUN,"DISPACCIAMENTO":DISPACCIAMENTO,"ASOS":ASOS,"QUOTA_POTENZA":QUOTA_POTENZA,
            "ONERI_SISTEMA":ONERI_SISTEMA,"PSV":PSV,"QUOTA_CONSUMO_GAS":QUOTA_CONSUMO_GAS,
            "QUOTA_DIST_GAS":QUOTA_DIST_GAS,"QUOTA_VAR_DIST_GAS":QUOTA_VAR_DIST_GAS,
            "ONERI_SISTEMA_GAS":ONERI_SISTEMA_GAS,"accisa_annua_gas":accisa_annua_gas,
            "aliquota_iva_gas":aliquota_iva_gas}
    if tipo=="Luce": dati["kwh"]=kwh; dati["kw"]=kw
    else: dati["smc"]=smc; dati["smc_annuo"]=smc_annuo

    df, box_offerta, totale = genera_scontrino(cliente,tipo,mesi_idx,off_val,dati,extra)

    col1,col2 = st.columns(2)
    with col1:
        st.subheader("📦 Box Offerta")
        st.text(box_offerta)
    with col2:
        st.subheader("📄 Scontrino Energia")
        st.dataframe(df)
    st.markdown(f"### 💰 Totale Bolletta: {totale:.2f} €")

    # PDF + invio mail
    pdf_file = crea_pdf(df,box_offerta,totale,cliente)
    st.download_button("📥 Scarica PDF", pdf_file, file_name="scontrino.pdf", mime="application/pdf")
    email_dest = st.text_input("Invia a (email)")
    if st.button("📧 Invia Email"):
        invia_mail(email_dest,f"Bolletta {cliente}","Ecco la bolletta simulata.",pdf_file)
        st.success("Email inviata!")