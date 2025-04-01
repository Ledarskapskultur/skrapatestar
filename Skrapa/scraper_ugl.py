import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def skrapa_ugl_kurser():
    url = "https://www.ugl-guiden.se/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    kurser = []

    # Hitta alla rader i tabellen som innehåller kursdata
    kursrader = soup.find_all("tr")
    for rad in kursrader:
        try:
            kolumner = rad.find_all("td")
            if len(kolumner) < 5:
                continue  # Hoppa över rader som inte har tillräcklig information

            # Vecka och Datum
            vecka_rå = kolumner[0].find("b")
            vecka = f"v{vecka_rå.text.strip().replace('Vecka ', '')}" if vecka_rå else "?"
            datum_rå = kolumner[0].text.strip()
            datum = datum_rå.split("–")[0].strip() if "–" in datum_rå else datum_rå

            # Kursgård (Anläggning och Ort)
            anläggning = kolumner[1].find_all("a")[0].text.strip()
            ort = kolumner[1].find_all("a")[1].text.strip()
            plats = f"{anläggning}, {ort}"

            # Handledare (Handledare1 och Handledare2)
            handledare1 = kolumner[2].text.strip().split(",")[0]  # Första handledaren
            handledare2 = kolumner[2].text.strip().split(",")[1] if len(kolumner[2].text.strip().split(",")) > 1 else "Okänd"  # Andra handledaren

            # Pris
            pris_rå = kolumner[3].text.strip()
            pris = re.sub(r'\D', '', pris_rå)  # Tar bort alla icke-siffriga tecken för att endast få priset

            # Platstillgång (t.ex. Fullbokad, Få platser)
            img = kolumner[4].find("img")
            if img:
                src = img["src"]
                if "100" in src:
                    platser = "Fullbokad"
                elif "80" in src or "90" in src:
                    platser = "Få"
                elif "50" in src or "60" in src:
                    platser = "Flera"
                else:
                    platser = "Okänt"
            else:
                platser = "Okänt"

            # Google Maps-länk
            maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(plats)}"

            # Lägg till kursinformation till listan
            kurser.append({
                "vecka": vecka,
                "datum": datum,
                "anläggning": anläggning,
                "ort": ort,
                "handledare1": handledare1,
                "handledare2": handledare2,
                "pris": f"{pris} kr",
                "platser": platser,
                "hemsida": url,
                "maps": maps
            })

        except Exception as e:
            continue  # Om något går fel i denna rad, hoppa över den

    return kurser
