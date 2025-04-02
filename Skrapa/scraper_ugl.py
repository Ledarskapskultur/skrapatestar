import requests
from bs4 import BeautifulSoup
import re
import urllib.parse

def skrapa_ugl_kurser():
    url = "https://www.ugl-guiden.se/"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    kursrader = soup.select("table.kurser tr")[1:]  # Hoppa över rubrikraden
    kurser = []

    for rad in kursrader:
        kolumner = rad.find_all("td")
        if len(kolumner) < 5:
            continue

        try:
            # Datum & Vecka
            datum_och_vecka = kolumner[0].get_text(strip=True)
            vecka_match = re.search(r"Vecka (\\d+)", datum_och_vecka)
            vecka = f"v{vecka_match.group(1)}" if vecka_match else "?"
            datum = datum_och_vecka.split("Vecka")[0].strip()

            # Anläggning & Ort
            länkar = kolumner[1].find_all("a")
            anläggning = länkar[0].get_text(strip=True) if len(länkar) > 0 else "?"
            ort = länkar[1].get_text(strip=True) if len(länkar) > 1 else "?"
            plats = f"{anläggning}, {ort}"

            # Handledare
            handledare_text = kolumner[2].get_text(strip=True)
            handledare_split = [h.strip() for h in handledare_text.split(",")]
            handledare1 = handledare_split[0] if len(handledare_split) > 0 else "?"
            handledare2 = handledare_split[1] if len(handledare_split) > 1 else "?"

            # Pris
            pris_rå = kolumner[3].get_text(strip=True)
            pris = re.sub(r"[^\\d]", "", pris_rå) + " kr" if pris_rå else "?"

            # Platser kvar
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

            maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(plats)}"

            kurser.append({
                "vecka": vecka,
                "datum": datum,
                "anläggning": anläggning,
                "ort": ort,
                "handledare1": handledare1,
                "handledare2": handledare2,
                "pris": pris,
                "platser": platser,
                "hemsida": url,
                "maps": maps_url
            })

        except Exception as e:
            continue

    return kurser
