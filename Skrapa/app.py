import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Kurs
from scraper_ugl import skrapa_ugl_kurser
from email_utils import generera_html_mail, skicka_mail

# --- Databasuppkoppling ---
engine = create_engine('sqlite:///kurser.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# --- Titel ---
st.title("🎓 UGL Kursbokningssystem")

# --- Kundinformation ---
st.sidebar.header("📇 Kundinfo")
namn = st.sidebar.text_input("Ditt namn")
telefon = st.sidebar.text_input("Telefonnummer")
email = st.sidebar.text_input("E-postadress")

# --- Uppdatera kurser från webben ---
if st.button("🔄 Uppdatera kurser"):
    skrapa_ugl_kurser()
    st.success("Kurser uppdaterade!")

# --- Hämta alla kurser från DB ---
session = Session()
kurser = session.query(Kurs).all()
session.close()

# --- Filtrering ---
alla_orter = sorted(set([k.plats for k in kurser]))
alla_priser = sorted(set([k.pris for k in kurser]))

st.sidebar.header("🔎 Filtrering")
vald_ort = st.sidebar.selectbox("Plats", ["Alla"] + alla_orter)
vald_pris = st.sidebar.selectbox("Pris", ["Alla"] + alla_priser)

filtrerade = [
    k for k in kurser if
    (vald_ort == "Alla" or k.plats == vald_ort) and
    (vald_pris == "Alla" or k.pris == vald_pris)
]

# --- Visa kurser och välj vilka som ska med i offert ---
st.subheader("✅ Välj kurser att inkludera i offert")
valda_kurser = []
for kurs in filtrerade:
    if st.checkbox(f"{kurs.namn} – {kurs.datum} – {kurs.plats} ({kurs.platser})", key=kurs.id):
        valda_kurser.append(kurs)

# --- Skicka offert-knapp ---
if st.button("✉️ Skicka offert"):
    if valda_kurser and namn and email:
        html_body = generera_html_mail(valda_kurser, namn)
        skicka_mail(email, html_body)
        st.success("✅ Offert skickad till " + email)
    else:
        st.warning("Fyll i namn, e-post och välj minst en kurs.")
