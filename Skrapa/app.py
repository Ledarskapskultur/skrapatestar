import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Kurs
from scraper_ugl import skrapa_ugl_kurser
from email_utils import generera_html_mail, skicka_mail
from datetime import datetime

# === Databas ===
engine = create_engine('sqlite:///kurser.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

st.set_page_config(page_title="UGL Kursbokning", layout="wide")

# === Titel & kundinfo ===
st.title("🎓 UGL Kursbokningssystem")

st.sidebar.header("📇 Kundinfo")
namn = st.sidebar.text_input("Ditt namn")
telefon = st.sidebar.text_input("Telefonnummer")
email = st.sidebar.text_input("E-postadress")

# === Filter ===
st.sidebar.header("🔎 Filtrering")
vald_ort = st.sidebar.text_input("Plats (valfritt)")
maxpris = st.sidebar.text_input("Maxpris (t.ex. 28000)")

# === Kurser från DB ===
if st.button("🔄 Uppdatera kurser"):
    skrapa_ugl_kurser()
    st.success("Kurser uppdaterade!")

session = Session()
kurser = session.query(Kurs).all()
session.close()

# === Hjälpfunktioner ===
def pris_som_siffra(pris_text):
    try:
        return int("".join(filter(str.isdigit, pris_text)))
    except:
        return 999999

def datum_sortering(kurs):
    try:
        return datetime.strptime(kurs.datum.split("–")[0].strip(), "%Y-%m-%d")
    except:
        return datetime.max

# === Filtrering ===
try:
    maxpris_int = int(maxpris)
except:
    maxpris_int = None

if vald_ort.strip() or maxpris_int is not None:
    filtrerade = [
        k for k in kurser if
        (vald_ort.strip() == "" or vald_ort.lower() in k.plats.lower()) and
        (maxpris_int is None or pris_som_siffra(k.pris) <= maxpris_int)
    ]
else:
    filtrerade = sorted(kurser, key=datum_sortering)[:10]

# === Visa kurser ===
st.subheader("✅ Välj kurser att inkludera i offert")

valda_kurser = []

if len(filtrerade) == 0:
    st.warning("🚫 Inga kurser matchar din sökning. Justera filtren och försök igen.")
else:
    cols = st.columns(4)
    for i, kurs in enumerate(filtrerade):
        with cols[i % 4]:
            if st.checkbox(f"{kurs.namn}\n{kurs.datum}\n{kurs.plats} – {kurs.pris}", key=kurs.id):
                valda_kurser.append(kurs)

# === Skicka offert ===
if st.button("✉️ Skicka offert"):
    if valda_kurser and namn and email:
        html_body = generera_html_mail(valda_kurser, namn)
        skicka_mail(email, html_body)
        st.success("✅ Offert skickad till " + email)
    else:
        st.warning("Fyll i namn, e-post och välj minst en kurs.")
from collections import Counter

st.markdown("---")
st.subheader("📊 Vanligaste platser & priser (topp 5)")

# 🔢 Lista alla platser
platser_lista = [k.plats for k in kurser if k.plats]
priser_lista = [k.pris for k in kurser if k.pris]

# 🔝 Räkna topp 5
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
