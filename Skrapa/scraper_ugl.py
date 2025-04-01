import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import sessionmaker
from models import Kurs
from sqlalchemy import create_engine
import urllib.parse

# Anslut till databasen
engine = create_engine("sqlite:///kurser.db")
Session = sessionmaker(bind=engine)

# 🔍 Tolka platstillgång utifrån bild-URL
def tolka_cirkelbild(url):
    if "100" in url or "full" in url:
        return "Fullbokad"
    elif any(x in url for x in ["75", "80", "90"]):
        return "Fåtal platser kvar"
    elif any(x in url for x in ["50", "60"]):
        return "Flera platser kvar"
    else:
        return "Okänt"

# 🟢 Skrapa från ugl-guiden.se
def scrape_ugl_guiden():
    url = "https://www.ugl-guiden.se/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    kurser = []

    kurskort = soup.find_all("div", class_="course-card")  # OBS! Justera efter aktuell HTML

    for kort in kurskort:
        try:
            namn = kort.find("h2").text.strip()
            datum = kort.find("span", class_="date").text.strip()
            plats = kort.find("span", class_="location").text.strip()
            pris = kort.find("span", class_="price").text.strip()
            handledare = kort.find("span", class_="teacher").text.strip()

            img = kort.find("img")
            platser = tolka_cirkelbild(img["src"]) if img else "Okänt"

            hemsida = url
            maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(plats)}"

            kurser.append({
                "namn": namn,
                "datum": datum,
                "plats": plats,
                "pris": pris,
                "platser": platser,
                "hemsida": hemsida,
                "maps": maps,
                "handledare": handledare
            })
        except:
            continue
    return kurser

# 🟡 Skrapa från uglkurser.se
def scrape_uglkurser():
    url = "https://www.uglkurser.se/datumochpriser.php"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    kurser = []

    rows = soup.find_all("tr")
    for row in rows[1:]:  # Skippa rubrikraden
        cols = row.find_all("td")
        if len(cols) >= 5:
            datum = cols[0].text.strip()
            plats = cols[1].text.strip()
            pris = cols[2].text.strip()
            handledare = cols[3].text.strip()

            hemsida = "https://www.uglkurser.se"
            maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(plats)}"

            kurser.append({
                "namn": "UGL-utbildning",
                "datum": datum,
                "plats": plats,
                "pris": pris,
                "platser": "Okänt",
                "hemsida": hemsida,
                "maps": maps,
                "handledare": handledare
            })
    return kurser

# 🧼 Rensa dubbletter
def rensa_dubletter(lista):
    unika = []
    sett = set()
    for k in lista:
        nyckel = (k["datum"], k["pris"], k["handledare"])
        if nyckel not in sett:
            unika.append(k)
            sett.add(nyckel)
    return unika

# 💾 Spara till databasen
def spara_kurser(kurser):
    session = Session()
    for k in kurser:
        finns = session.query(Kurs).filter_by(
            datum=k["datum"],
            pris=k["pris"],
            handledare=k["handledare"]
        ).first()

        if not finns:
            kurs = Kurs(
                namn=k["namn"],
                datum=k["datum"],
                plats=k["plats"],
                pris=k["pris"],
                platser=k["platser"],
                hemsida=k["hemsida"],
                maps=k["maps"],
                handledare=k["handledare"]
            )
            session.add(kurs)
    session.commit()
    session.close()

# 🔁 Huvudfunktion
def skrapa_ugl_kurser():
    alla = scrape_ugl_guiden() + scrape_uglkurser()
    unika = rensa_dubletter(alla)
    spara_kurser(unika)
