import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Kurs
from email_utils import generera_html_mail, skicka_mail
from datetime import datetime
from collections import Counter
import re
from scraper_ugl import skrapa_ugl_kurser

# === DB Setup ===
engine = create_engine('sqlite:///kurser.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# === Sidans layout ===
st.set_page_config(page_title="UGL Kursbokningssystem", layout="wide")
st.title("🎓 UGL Kursbokningssystem")

# === Sidebar: Kundinfo ===
st.sidebar.header("📇 Kundinfo")
namn = st.sidebar.text_input("Ditt namn")
telefon = st.sidebar.text_input("Telefonnummer")
email = st.sidebar.text_input("E-postadress")

# === Sidebar: Filtrering ===
st.sidebar.header("🔎 Filtrering")
vald_ort = st.sidebar.text_input("Plats (t.ex. Stockholm)")
maxpris = st.sidebar.text_input("Maxpris (t.ex. 28000)")
valda_veckor = st.sidebar.text_input("Veckor (t.ex. 15,20 eller 35-37)")

# === Uppdatera kurser från webben ===
if st.button("🔄 Uppdatera kurser"):
    kurser = skrapa_ugl_kurser()
    session = Session()
    session.query(Kurs).delete()  # Rensa befintliga kurser
    for kurs_data in kurser:
        ny_kurs = Kurs(
            namn=f"UGL-kurs {kurs_data['vecka']}",
            datum=kurs_data['datum'],
            platser=kurs_data['platser'],
            plats=f"{kurs_data['anläggning']}, {kurs_data['ort']}",
            pris=kurs_data['pris'],
            hemsida=kurs_data['hemsida'],
            maps=kurs_data['maps'],
            handledare=f"{kurs_data['handledare1']}, {kurs_data['handledare2']}"
        )
        session.add(ny_kurs)
    session.commit()
    session.close()
    st.success("✅ Kurserna har uppdaterats!")

# === Ladda kurser från DB ===
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

# === Veckofiltrering ===
def vecka_matchar(kursvecka, filterveckor):
    try:
        veckor = set()
        for d in filterveckor.split(','):
            d = d.strip()
            if '-' in d:
                start, slut = map(int, d.split('-'))
                veckor.update(range(start, slut + 1))
            else:
                veckor.add(int(d))
        kursvecka_nummer = int(re.findall(r'\\d+', kursvecka)[0])
        return kursvecka_nummer in veckor
    except:
        return False
# === Tillämpa filtrering ===
filtrerade = []

for k in kurser:
    match_plats = (vald_ort.lower() in k.plats.lower()) if vald_ort.strip() else True
    match_pris = (pris_som_siffra(k.pris) <= int(maxpris)) if maxpris.strip().isdigit() else True
    match_vecka = vecka_matchar(k.namn, valda_veckor) if valda_veckor.strip() else True

    if match_plats and match_pris and match_vecka:
        filtrerade.append(k)

filtrerade.sort(key=lambda x: datetime.strptime(x.datum.split("–")[0].strip(), "%Y-%m-%d"))

# === Visa kurser ===
st.subheader("✅ Välj kurser att inkludera i offert")
valda_kurser = []

if len(filtrerade) == 0:
    st.warning("🚫 Inga kurser matchar din sökning. Justera filtren.")
else:
    cols = st.columns(4)
    for i, kurs in enumerate(filtrerade):
        with cols[i % 4]:
            visning = (
                f"📆 {kurs.namn} | 📅 {kurs.datum}\n"
                f"💰 {kurs.pris} | 🏨 {kurs.plats}\n"
                f"👨‍🏫 {kurs.handledare}\n"
                f"🟡 Platser kvar: {kurs.platser}"
            )

            if st.checkbox(visning, key=f"{kurs.id}"):
                valda_kurser.append(kurs)

# === Skicka offert ===
if st.button("✉️ Skicka offert"):
    if valda_kurser and namn and email:
        html_body = generera_html_mail(valda_kurser, namn)
        skicka_mail(email, html_body)
        st.success("✅ Offert skickad till " + email)
    else:
        st.warning("Fyll i namn, e-post och välj minst en kurs.")

# === Statistik ===
st.markdown("---")
st.subheader("📊 Vanligaste platser & priser (topp 5)")
platser_lista = [k.plats.split(', ')[1] for k in kurser if k.plats]
priser_lista = [k.pris for k in kurser if k.pris]

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
# === Visa skrapad rådata ===
st.markdown("---")
st.subheader("📑 Skrapad kursdata (rådata från UGL-guiden.se)")

if st.button("🔍 Visa skrapad kursdata"):
    skrapade_kurser = skrapa_ugl_kurser()

    if not skrapade_kurser:
        st.warning("⚠️ Inga kurser kunde skrapas från källan.")
    else:
        for kurs in skrapade_kurser:
            st.markdown(f"""
            ---
            📅 **Vecka:** {kurs['vecka']}  
            📆 **Datum:** {kurs['datum']}  
            🏨 **Plats:** {kurs['anläggning']}, {kurs['ort']}  
            💰 **Pris:** {kurs['pris']}  
            🟡 **Platstillgång:** {kurs['platser']}  
            👨‍🏫 **Handledare:** {kurs['handledare1']} och {kurs['handledare2']}  
            🔗 [Hemsida]({kurs['hemsida']}) | 📍 [Karta]({kurs['maps']})
            """, unsafe_allow_html=True)
