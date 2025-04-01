import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Kurs
from email_utils import generera_html_mail, skicka_mail
from datetime import datetime
from collections import Counter
import re
from scraper_ugl import skrapa_ugl_kurser

# === DB ===
engine = create_engine('sqlite:///kurser.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

st.set_page_config(page_title="UGL Kursbokningssystem", layout="wide")
st.title("🎓 UGL Kursbokningssystem")

# === Kundinfo ===
st.sidebar.header("📇 Kundinfo")
namn = st.sidebar.text_input("Ditt namn")
telefon = st.sidebar.text_input("Telefonnummer")
email = st.sidebar.text_input("E-postadress")

# === Filtrering ===
st.sidebar.header("🔎 Filtrering")
vald_ort = st.sidebar.text_input("Plats (valfritt)")
maxpris = st.sidebar.text_input("Maxpris (t.ex. 28000)")

# === Kurser från DB ===
if st.button("🔄 Uppdatera kurser"):
    kurser = skrapa_ugl_kurser()  # Hämtar kursdata från den uppdaterade funktionen
    st.success("Kurser uppdaterade!")
else:
    session = Session()
    kurser = session.query(Kurs).all()
    session.close()

# === Hjälpfunktioner ===
def pris_som_siffra(pris_text):
    try:
        siffror = re.findall(r'\d+', pris_text)
        return int("".join(siffror)) if siffror else 0
    except:
        return 0

# === Filtrering ===
try:
    maxpris_int = int(maxpris)
except:
    maxpris_int = None

if vald_ort.strip() or maxpris_int is not None:
    filtrerade = [
        k for k in kurser if
        (vald_ort.strip() == "" or vald_ort.lower() in k['ort'].lower()) and
        (maxpris_int is None or pris_som_siffra(k['pris']) <= maxpris_int)
    ]
else:
    def datum_sortering(kurs):
        try:
            return datetime.strptime(kurs['datum'].split("–")[0].strip(), "%Y-%m-%d")
        except:
            return datetime.max
    filtrerade = sorted(kurser, key=datum_sortering)[:10]

# === Visa kurser i 4 kolumner ===
st.subheader("✅ Välj kurser att inkludera i offert")
valda_kurser = []

if len(filtrerade) == 0:
    st.warning("🚫 Inga kurser matchar din sökning. Justera filtren.")
else:
    cols = st.columns(4)
    for i, kurs in enumerate(filtrerade):
        with cols[i % 4]:
            visning = (
                f"📆 Vecka {kurs['vecka']} | 📅 {kurs['datum']} | 💰 {kurs['pris']}\n"
                f"🏨 {kurs['anläggning']}, {kurs['ort']}\n"
                f"👨‍🏫 {kurs['handledare1']} & {kurs['handledare2']}\n"
                f"🟡 Platser kvar: {kurs['platser']}"
            )

            if st.checkbox(visning, key=kurs['vecka'] + kurs['datum']):
                valda_kurser.append(kurs)

# === Skicka offert ===
if st.button("✉️ Skicka offert"):
    if valda_kurser and namn and email:
        html_body = generera_html_mail(valda_kurser, namn)
        skicka_mail(email, html_body)
        st.success("✅ Offert skickad till " + email)
    else:
        st.warning("Fyll i namn, e-post och välj minst en kurs.")

# === Topp 5 plats & pris ===
st.markdown("---")
st.subheader("📊 Vanligaste platser & priser (topp 5)")

platser_lista = [k['ort'] for k in kurser if k['ort']]
priser_lista = [k['pris'] for k in kurser if k['pris']]

topp_orter = Counter(platser_lista).most_common(5)
topp_priser = Counter(priser_lista).most_common(5)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**🏙️ Vanligaste platser:**")
    for plats, antal in topp_orter:
        st.markdown(f"- {plats} ({antal} st)")

with col2:
    st.markdown("**💰 Vanligaste priser:**")
    for pris, antal in topp_priser:
        st.markdown(f"- {pris} ({antal} st)")
