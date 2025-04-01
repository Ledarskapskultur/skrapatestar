def scrape_ugl_guiden():
    url = "https://www.ugl-guiden.se/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    kurser = []

    kursrader = soup.find_all("tr")
    for rad in kursrader:
        try:
            kolumner = rad.find_all("td")
            if len(kolumner) < 5:
                continue

            vecka_rå = kolumner[0].find("b")
            vecka = f"v{vecka_rå.text.strip().replace('Vecka ', '')}" if vecka_rå else "?"

            anläggning = kolumner[1].find_all("a")[0].text.strip()
            ort = kolumner[1].find_all("a")[1].text.strip()
            plats = f"{anläggning}, {ort}"

            handledare_rå = kolumner[2].text.strip()
            handledare_split = handledare_rå.split()
            handledare = handledare_split[0]
            if len(handledare_split) > 1:
                handledare += " " + handledare_split[1]

            # Fixa ihopklistrade namn
            handledare = re.sub(r'(?<=[a-zåäö])(?=[A-ZÅÄÖ])', ' ', handledare)

            pris = kolumner[3].text.strip()

            # Tolkning av platstillgång från <img>
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

            maps = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(plats)}"

            kurser.append({
                "namn": "UGL-utbildning",
                "datum": vecka,
                "plats": plats,
                "pris": pris,
                "platser": platser,
                "hemsida": url,
                "maps": maps,
                "handledare": handledare
            })

        except Exception as e:
            continue

    return kurser
