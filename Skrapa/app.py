import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Kurs
from scraper_ugl import skrapa_ugl_kurser
from email_utils import generera_html_mail, skicka_mail
from datetime import datetime

# === Databasuppkoppling ===
engine = create_engine('sqlite:///kurser.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

st.title("🎓 UGL Kursbokningssystem")

# === Kundinformation ===
st.sidebar.header("📇 Kundinfo")
namn = st.sidebar.text_input("Ditt namn")
telefon = st.sidebar.text_input("Telefonnummer")
email = st.sidebar.text_input("E-postadress")

# === Filter ===
st.sidebar.header("🔎 Filtrering")
vald_ort = st.sidebar.text_input("Plats (valfritt)")
maxpris = st.sidebar.text_input("Maxpris (t.ex. 28000)")

# === Ladda och filtrera kurser ===
if st.button("🔄 Uppdatera kurser"):
    skrapa_ugl_kurser()
    st.success("Kurser uppdaterade!")

session = Session()
kurser = session.query(Kurs).all()
session.close()

# === Hjälpfunktion för att jämföra priser ===
def pris_som_siffra(pris_text):
    try:
        return int("".join(filter(str.isdigit, pris_text)))
    except:
        return 999999

# === Hjälpfunktion för att konvertera datum till veckonummer ===
def datum_till_vecka(datum_str):
    try:
        dt = datetime.strptime(datum_str.split("–")[0].strip(), "%Y-%m-%d")
        return dt.isocalendar().week
    except:
        return 999

# === Filtrering ===
try:
    maxpris_int = int(maxpris)
except:
    maxpris_int = None

if vald_ort.strip() or maxpris_int is not None:
    # ✅ Använd filter
    filtrerade = [
        k for k in kurser if
        (vald_ort.strip() == "" or vald_ort.lower() in k.plats.lower()) and
        (maxpris_int is None or pris_som_siffra(k.pris) <= maxpris_int)
    ]
else:
    # 🕒 Inget filter – visa de 10 kurserna med närmast startdatum
    def datum_sortering(kurs):
        try:
            return datetime.strptime(kurs.datum.split("–")[0].strip(), "%Y-%m-%d")
        except:
            return datetime.max

    filtrerade = sorted(kurser, key=datum_sortering)[:10]

# === Visa filtrerade kurser i 4 kolumner ===
st.subheader("✅ Välj kurser att inkludera i offert")

valda_kurser = []
cols = st.columns(4)

for i, kurs in enumerate(filtrerade):
    with cols[i % 4]:
        if st.checkbox(f"{kurs.namn}\n{kurs.datum}\n{kurs.plats} – {kurs.pris}", key=f"{kurs.id}"):
            valda_kurser.append(kurs)

# === Skicka offert ===
if st.button("✉️ Skicka offert"):
    if valda_kurser and namn and email:
        html_body = generera_html_mail(valda_kurser, namn)
        skicka_mail(email, html_body)
        st.success("✅ Offert skickad till " + email)
    else:
        st.warning("Fyll i namn, e-post och välj minst en kurs.")
