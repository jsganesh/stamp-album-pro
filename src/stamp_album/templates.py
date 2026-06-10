"""
Real-world stamp album templates organized by country, era, and theme.

Each template includes:
- id: unique identifier
- name: display name
- description: what the template is for
- category: organizing category
- dsl: the DSL content for the template
"""

TEMPLATES = [
    # === BRITISH COMMONWEALTH ===
    {
        "id": "uk_victorian",
        "name": "Great Britain — Victorian Era",
        "description": "Classic Victorian-era British stamp page with triple border, centered title, and structured rows for line-engraved issues.",
        "category": "British Commonwealth",
        "content": """# Great Britain — Victorian Era
ALBUM_TITLE("Great Britain — Victorian Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.5 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Great Britain — Victorian Era")
ALBUM_PAGES_FOOTER_NUMBER(HN 10 C 1 "Page " " of $PAGES$")

COLOUR_ALBUM_BORDER(darkred)
COLOUR_ALBUM_TITLE(darkblue)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Line Engraved Issues — 1840-1901")
PAGE_TEXT_CENTRE(HN 10 "The world's first postage stamp, the Penny Black, was issued on 6 May 1840.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Penny Black — 1840\\nUsed example" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "Penny Red — 1841\\nPlate 100" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "Twopence Blue — 1840" "SG 5" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Surface Printed Issues — 1855-1901")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "4d Carmine — 1855" "SG 57" "" "")
STAMP_ADD(32.0 37.0 "1s Green — 1862" "SG 88" "" "")
STAMP_ADD(32.0 37.0 "5s Rose — 1867" "SG 117" "" "")
""",
    },
    {
        "id": "uk_edward_vii",
        "name": "Great Britain — Edward VII",
        "description": "Edward VII era British stamps (1901-1910) with half-tone printing and distinctive color schemes.",
        "category": "British Commonwealth",
        "content": """# Great Britain — Edward VII
ALBUM_TITLE("Great Britain — Edward VII Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Great Britain — Edward VII")

COLOUR_ALBUM_BORDER(darkblue)
COLOUR_ALBUM_TITLE(darkblue)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Edward VII — 1901-1910")
PAGE_TEXT_CENTRE(HN 10 "Half-tone printing introduced new color possibilities.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1d Scarlet — 1902" "SG 219" "" "")
STAMP_ADD(32.0 37.0 "2d Green — 1902" "SG 221" "" "")
STAMP_ADD(32.0 37.0 "2½d Ultramarine — 1902" "SG 222" "" "")

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "3d Purple — 1902" "SG 223" "" "")
STAMP_ADD(32.0 37.0 "6d Purple — 1902" "SG 226" "" "")
STAMP_ADD(32.0 37.0 "1s Green & Carmine — 1902" "SG 228" "" "")
""",
    },
    {
        "id": "uk_george_v",
        "name": "Great Britain — George V",
        "description": "George V era (1910-1936) including the famous Seahorse high values and Wembley issues.",
        "category": "British Commonwealth",
        "content": """# Great Britain — George V
ALBUM_TITLE("Great Britain — George V Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Great Britain — George V")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "George V — 1910-1936")
PAGE_TEXT_CENTRE(HN 10 "Including the iconic Seahorse definitives and commemorative issues.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "½d Green — 1912" "SG 349" "" "")
STAMP_ADD(32.0 37.0 "1d Scarlet — 1912" "SG 350" "" "")
STAMP_ADD(32.0 37.0 "2½d Blue — 1912" "SG 352" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Seahorse High Values")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "2/6 Brown — 1913" "SG 399" "" "")
STAMP_ADD(32.0 37.0 "5/- Rose — 1913" "SG 400" "" "")
STAMP_ADD(32.0 37.0 "10/- Blue — 1913" "SG 401" "" "")
STAMP_ADD(32.0 37.0 "£1 Green — 1913" "SG 402" "" "")
""",
    },
    {
        "id": "australia_kangaroo",
        "name": "Australia — Kangaroo & Map",
        "description": "Australia's iconic Kangaroo & Map definitives (1913-1936) — the first stamps of the Commonwealth.",
        "category": "British Commonwealth",
        "content": """# Australia — Kangaroo & Map
ALBUM_TITLE("Australia — Kangaroo & Map Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Australia — Kangaroo & Map")

COLOUR_ALBUM_BORDER(darkgreen)
COLOUR_ALBUM_TITLE(darkgreen)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Kangaroo & Map Definitives — 1913-1936")
PAGE_TEXT_CENTRE(HN 10 "The first stamps of the Commonwealth of Australia.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1d Red — 1913\\nFirst issue" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "2d Red — 1913" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "6d Blue — 1913" "SG 5" "" "")

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1/- Green — 1914" "SG 10" "" "")
STAMP_ADD(32.0 37.0 "2/- Brown — 1914" "SG 11" "" "")
STAMP_ADD(32.0 37.0 "5/- Grey — 1914" "SG 12" "" "")
""",
    },
    {
        "id": "canada_queen",
        "name": "Canada — Queen Victoria",
        "description": "Canadian Victorian-era stamps including the famous 12½c and 21c values.",
        "category": "British Commonwealth",
        "content": """# Canada — Queen Victoria
ALBUM_TITLE("Canada — Victorian Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Canada — Queen Victoria")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Canadian Victorian Issues")
PAGE_TEXT_CENTRE(HN 10 "From the Province of Canada to Confederation and beyond.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1c Brown-Red — 1868" "SG 58" "" "")
STAMP_ADD(32.0 37.0 "2c Green — 1868" "SG 59" "" "")
STAMP_ADD(32.0 37.0 "3c Orange — 1868" "SG 60" "" "")

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "5c Olive — 1870" "SG 62" "" "")
STAMP_ADD(32.0 37.0 "10c Magenta — 1870" "SG 64" "" "")
STAMP_ADD(32.0 37.0 "12½c Blue — 1897" "SG 168" "" "")
""",
    },
    {
        "id": "india_british",
        "name": "India — British Raj",
        "description": "Stamps of British India from Queen Victoria through George V, including the famous Inverted Head 4 Annas.",
        "category": "British Commonwealth",
        "content": """# India — British Raj
ALBUM_TITLE("India — British Raj Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "India — British Raj")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "British India — 1854-1947")
PAGE_TEXT_CENTRE(HN 10 "From the first issues under Queen Victoria to independence.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "½a Blue — 1854\\nFirst issue" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "1a Brown — 1854" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "4a Green — 1854\\nInverted Head variety" "SG 4" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Edward VII & George V Issues")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1a Carmine — 1902" "SG 135" "" "")
STAMP_ADD(32.0 37.0 "2a Violet — 1902" "SG 137" "" "")
STAMP_ADD(32.0 37.0 "4a Olive — 1902" "SG 140" "" "")
""",
    },
    {
        "id": "south_africa",
        "name": "South Africa — Union Era",
        "description": "Stamps of the Union of South Africa (1910-1961) including the iconic triangular Cape issues.",
        "category": "British Commonwealth",
        "content": """# South Africa — Union Era
ALBUM_TITLE("South Africa — Union & Republic")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "South Africa — Union Era")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Union of South Africa — 1910-1961")
PAGE_TEXT_CENTRE(HN 10 "The Cape of Good Hope, Natal, Orange Free State and Transvaal united on 31 May 1910.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "½d Green — 1910" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "1d Scarlet — 1910" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "2½d Blue — 1910" "SG 4" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "King George V Issues")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "4d Orange — 1913" "SG 10" "" "")
STAMP_ADD(32.0 37.0 "6d Purple — 1913" "SG 12" "" "")
STAMP_ADD(32.0 37.0 "1/- Green — 1913" "SG 15" "" "")
""",
    },
    # === EUROPE ===
    {
        "id": "france_republic",
        "name": "France — Third Republic",
        "description": "French Third Republic stamps including the famous Sower series and Merson high values.",
        "category": "Europe",
        "content": """# France — Third Republic
ALBUM_TITLE("France — Third Republic Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "France — Third Republic")

COLOUR_ALBUM_BORDER(darkblue)
COLOUR_ALBUM_TITLE(darkblue)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Third Republic — 1870-1940")
PAGE_TEXT_CENTRE(HN 10 "From the Ceres series to the iconic Sower definitives.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1c Green — 1870\\nCeres issue" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "5c Green — 1870" "SG 3" "" "")
STAMP_ADD(32.0 37.0 "10c Blue — 1870" "SG 4" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "The Sower Series — 1903-1920s")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10c Red — 1906" "SG 220" "" "")
STAMP_ADD(32.0 37.0 "15c Green — 1906" "SG 221" "" "")
STAMP_ADD(32.0 37.0 "25c Blue — 1906" "SG 223" "" "")
STAMP_ADD(32.0 37.0 "30c Violet — 1906" "SG 224" "" "")
""",
    },
    {
        "id": "germany_empire",
        "name": "Germany — Imperial Era",
        "description": "German Empire stamps (1871-1918) including the Eagle and Reichspost issues.",
        "category": "Europe",
        "content": """# Germany — Imperial Era
ALBUM_TITLE("German Empire — 1871-1918")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "German Empire")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "German Empire — 1871-1918")
PAGE_TEXT_CENTRE(HN 10 "From unification under Bismarck to the end of the Great War.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10pf Green — 1872\\nEagle issue" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "20pf Blue — 1872" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "25pf Orange — 1875" "SG 5" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Reichspost Issues — 1875-1900")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10pf Carmine — 1875" "SG 20" "" "")
STAMP_ADD(32.0 37.0 "20pf Blue — 1875" "SG 21" "" "")
STAMP_ADD(32.0 37.0 "50pf Green — 1890" "SG 35" "" "")
""",
    },
    {
        "id": "netherlands_queen",
        "name": "Netherlands — Queen Wilhelmina",
        "description": "Dutch stamps from Queen Wilhelmina's long reign (1890-1948) including the iconic Arms series.",
        "category": "Europe",
        "content": """# Netherlands — Queen Wilhelmina
ALBUM_TITLE("Netherlands — Wilhelmina Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Netherlands — Wilhelmina")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Queen Wilhelmina — 1890-1948")
PAGE_TEXT_CENTRE(HN 10 "One of the longest reigns in philatelic history.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "2½c Blue — 1892" "SG 120" "" "")
STAMP_ADD(32.0 37.0 "5c Green — 1892" "SG 122" "" "")
STAMP_ADD(32.0 37.0 "10c Red — 1892" "SG 124" "" "")

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "25c Violet — 1892" "SG 126" "" "")
STAMP_ADD(32.0 37.0 "50c Brown — 1892" "SG 128" "" "")
STAMP_ADD(32.0 37.0 "1g Orange — 1892" "SG 130" "" "")
""",
    },
    {
        "id": "belgium_leopold",
        "name": "Belgium — Leopold Era",
        "description": "Belgian stamps from Leopold I through Leopold II, including the iconic Epaulettes series.",
        "category": "Europe",
        "content": """# Belgium — Leopold Era
ALBUM_TITLE("Belgium — Leopold I & II")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Belgium — Leopold Era")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Belgium — 1849-1909")
PAGE_TEXT_CENTRE(HN 10 "The Epaulettes — among the most iconic early European stamps.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10c Brown — 1849\\nEpaulettes" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "20c Blue — 1849" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "40c Red — 1849" "SG 3" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Leopold II Issues — 1865-1909")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10c Green — 1869" "SG 28" "" "")
STAMP_ADD(32.0 37.0 "20c Blue — 1869" "SG 29" "" "")
STAMP_ADD(32.0 37.0 "50c Rose — 1869" "SG 31" "" "")
""",
    },
    {
        "id": "switzerland_early",
        "name": "Switzerland — Early Issues",
        "description": "Swiss stamps from the cantonal issues through the first federal issues including the famous Double Geneva.",
        "category": "Europe",
        "content": """# Switzerland — Early Issues
ALBUM_TITLE("Switzerland — Cantonal & Federal")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Switzerland — Early Issues")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Switzerland — 1843-1862")
PAGE_TEXT_CENTRE(HN 10 "From cantonal issues to the first federal stamps.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "2½r Black/Zurich — 1843\\nCantonal issue" "SG Z1" "" "")
STAMP_ADD(32.0 37.0 "4r Red/Geneva — 1843\\nDouble Geneva" "SG G1" "" "")
STAMP_ADD(32.0 37.0 "5r Blue/Basel — 1845\\nBasel Dove" "SG B1" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Federal Issues — 1850-1862")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "2½r Black — 1850\\nEagle issue" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "5r Red — 1850" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "10r Blue — 1850" "SG 3" "" "")
""",
    },
    # === AMERICAS ===
    {
        "id": "usa_classic",
        "name": "USA — Classic Issues",
        "description": "American classic stamps (1847-1890) including the famous 1c Franklin and 3c Washington.",
        "category": "Americas",
        "content": """# USA — Classic Issues
ALBUM_TITLE("United States — Classic Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(215.9 279.4)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "United States — Classic Issues")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "United States — 1847-1890")
PAGE_TEXT_CENTRE(HN 10 "The first US postage stamps featured Benjamin Franklin and George Washington.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "5c Brown — 1847\\nBenjamin Franklin" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "10c Black — 1847\\nGeorge Washington" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "1c Blue — 1851\\nFranklin" "SG 10" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "1869 Pictorial Issue")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "1c Buff — 1869\\nPost Horse" "SG 113" "" "")
STAMP_ADD(32.0 37.0 "2c Brown — 1869\\nLocomotive" "SG 114" "" "")
STAMP_ADD(32.0 37.0 "3c Blue — 1869\\nShield" "SG 115" "" "")
STAMP_ADD(32.0 37.0 "15c Red/Blue — 1869\\nLanding of Columbus" "SG 121" "" "")
""",
    },
    {
        "id": "brazil_empire",
        "name": "Brazil — Empire Era",
        "description": "Brazilian Empire stamps including the famous Bull's Eyes — among the first stamps in the Americas.",
        "category": "Americas",
        "content": """# Brazil — Empire Era
ALBUM_TITLE("Brazil — Empire Issues")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Brazil — Empire Era")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Brazil — 1843-1889")
PAGE_TEXT_CENTRE(HN 10 "The Bull's Eyes — second country in the world to issue postage stamps.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "30r Black — 1843\\nBull's Eye" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "60r Black — 1843" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "90r Black — 1843" "SG 3" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Pedro II Issues — 1866-1889")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "10r Red — 1866\\nSlanted numerals" "SG 38" "" "")
STAMP_ADD(32.0 37.0 "20r Blue — 1866" "SG 39" "" "")
STAMP_ADD(32.0 37.0 "50r Green — 1866" "SG 40" "" "")
""",
    },
    {
        "id": "argentina_early",
        "name": "Argentina — Early Issues",
        "description": "Argentine stamps from the early confederation and republic periods.",
        "category": "Americas",
        "content": """# Argentina — Early Issues
ALBUM_TITLE("Argentina — Early Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Argentina — Early Issues")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Argentina — 1858-1890")
PAGE_TEXT_CENTRE(HN 10 "From the Argentine Confederation to the modern republic.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "5c Red — 1858\\nConfederation" "SG 1" "" "")
STAMP_ADD(32.0 37.0 "1p Blue — 1858" "SG 2" "" "")
STAMP_ADD(32.0 37.0 "4p Green — 1862" "SG 5" "" "")

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "5c Red — 1864\\nRepublic issue" "SG 10" "" "")
STAMP_ADD(32.0 37.0 "10c Blue — 1864" "SG 11" "" "")
STAMP_ADD(32.0 37.0 "1p Green — 1864" "SG 12" "" "")
""",
    },
    # === THEMATIC ===
    {
        "id": "thematic_birds",
        "name": "Thematic — Birds",
        "description": "A thematic collection page for bird stamps from around the world.",
        "category": "Thematic",
        "content": """# Thematic Collection — Birds
ALBUM_TITLE("Birds of the World on Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Birds of the World")

COLOUR_ALBUM_TITLE(darkgreen)
COLOUR_PAGE_TEXT(darkgreen)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Raptors & Birds of Prey")
PAGE_TEXT_CENTRE(HN 10 "Eagles, hawks, falcons, and owls from around the world.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Bald Eagle\\nUnited States" "SG 100" "" "")
STAMP_ADD(32.0 37.0 "Golden Eagle\\nGermany" "SG 200" "" "")
STAMP_ADD(32.0 37.0 "Peregrine Falcon\\nGreat Britain" "SG 300" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Tropical Birds")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Scarlet Macaw\\nBrazil" "SG 400" "" "")
STAMP_ADD(32.0 37.0 "Bird of Paradise\\nPapua New Guinea" "SG 500" "" "")
STAMP_ADD(32.0 37.0 "Toucan\\nCosta Rica" "SG 600" "" "")
""",
    },
    {
        "id": "thematic_ships",
        "name": "Thematic — Ships & Navigation",
        "description": "A thematic collection of maritime stamps including famous ships and lighthouses.",
        "category": "Thematic",
        "content": """# Thematic Collection — Ships
ALBUM_TITLE("Ships & Maritime History on Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Ships & Maritime History")

COLOUR_ALBUM_TITLE(darkblue)
COLOUR_PAGE_TEXT(darkblue)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Famous Sailing Ships")
PAGE_TEXT_CENTRE(HN 10 "From the Mayflower to the Cutty Sark.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Mayflower\\nUnited States" "" "" "")
STAMP_ADD(32.0 37.0 "Cutty Sark\\nGreat Britain" "" "" "")
STAMP_ADD(32.0 37.0 "Vasa\\nSweden" "" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Modern Ocean Liners")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "RMS Titanic\\nGreat Britain" "" "" "")
STAMP_ADD(32.0 37.0 "SS Normandie\\nFrance" "" "" "")
STAMP_ADD(32.0 37.0 "RMS Queen Mary\\nGreat Britain" "" "" "")
""",
    },
    {
        "id": "thematic_space",
        "name": "Thematic — Space Exploration",
        "description": "A thematic collection of space-themed stamps from around the world.",
        "category": "Thematic",
        "content": """# Thematic Collection — Space
ALBUM_TITLE("Space Exploration on Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Space Exploration")

COLOUR_ALBUM_TITLE(navy)
COLOUR_PAGE_TEXT(navy)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "The Space Race — 1957-1969")
PAGE_TEXT_CENTRE(HN 10 "From Sputnik to the Moon landing.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Sputnik 1\\nUSSR — 1957" "" "" "")
STAMP_ADD(32.0 370 "Yuri Gagarin\\nUSSR — 1961" "" "" "")
STAMP_ADD(32.0 37.0 "Apollo 11\\nUSA — 1969" "" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Space Stations & Shuttles")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Space Shuttle\\nUSA" "" "" "")
STAMP_ADD(32.0 37.0 "Mir Space Station\\nRussia" "" "" "")
STAMP_ADD(32.0 37.0 "International Space Station\\nInternational" "" "" "")
""",
    },
    {
        "id": "thematic_olympics",
        "name": "Thematic — Olympic Games",
        "description": "A thematic collection of Olympic Games stamps from various host nations.",
        "category": "Thematic",
        "content": """# Thematic Collection — Olympics
ALBUM_TITLE("Olympic Games on Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Olympic Games")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Modern Olympic Games")
PAGE_TEXT_CENTRE(HN 10 "From Athens 1896 to the present day.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Athens 1896\\nFirst modern Olympics" "" "" "")
STAMP_ADD(32.0 37.0 "Paris 1900\\nSecond Olympiad" "" "" "")
STAMP_ADD(32.0 37.0 "London 1908\\nFirst purpose-built stadium" "" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Winter Olympics")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Chamonix 1924\\nFirst Winter Games" "" "" "")
STAMP_ADD(32.0 37.0 "Lake Placid 1932\\nUSA" "" "" "")
STAMP_ADD(32.0 37.0 "Oslo 1952\\nNorway" "" "" "")
""",
    },
    {
        "id": "thematic_flowers",
        "name": "Thematic — Flowers & Plants",
        "description": "A thematic collection of flower and plant stamps from around the world.",
        "category": "Thematic",
        "content": """# Thematic Collection — Flowers
ALBUM_TITLE("Flowers & Plants on Stamps")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(6.0 6.0)
ALBUM_PAGES_TITLE(TB 16 "Flowers & Plants")

COLOUR_ALBUM_TITLE(darkgreen)

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Roses & Tulips")
PAGE_TEXT_CENTRE(HN 10 "The world's most beloved garden flowers on stamps.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 370 "Rose\\nGreat Britain" "" "" "")
STAMP_ADD(32.0 37.0 "Tulip\\nNetherlands" "" "" "")
STAMP_ADD(32.0 37.0 "Cherry Blossom\\nJapan" "" "" "")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Tropical Flowers")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 0.5 6.0)
STAMP_ADD(32.0 37.0 "Orchid\\nSingapore" "" "" "")
STAMP_ADD(32.0 37.0 "Hibiscus\\nHawaii" "" "" "")
STAMP_ADD(32.0 37.0 "Frangipani\\nCook Islands" "" "" "")
""",
    },
    # === COMPETITION LAYOUTS ===
    {
        "id": "competition_single",
        "name": "Competition — Single Frame",
        "description": "FIP-standard single frame layout for competitive exhibition with large margins and descriptive text.",
        "category": "Competition",
        "content": """# Competition Frame
ALBUM_TITLE("Exhibition Title")
ALBUM_AUTHOR("Exhibitor Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(25.0 25.0 25.0 25.0)
ALBUM_PAGES_BORDER(0.2 0.6 0.2 1.5)
ALBUM_PAGES_SPACING(8.0 8.0)
ALBUM_PAGES_TITLE(TB 18 "Exhibition Title")
ALBUM_PAGES_FOOTER_NUMBER(HN 10 C 1 "Page " " of $PAGES$")

COLOUR_ALBUM_BORDER(darkred)
COLOUR_ALBUM_TITLE(darkblue)

PAGE_START

PAGE_TEXT_CENTRE(HS 16 "Section Title")
PAGE_TEXT_CENTRE(HN 12 "Descriptive text providing context for this section of the exhibit.")

PAGE_RULE_H(0.5 4 0)

PAGE_VSPACE(3)

ROW_START_FS(HN 9 0.5 7.0)
STAMP_ADD(35.0 40.0 "Stamp description\\nCatalog reference" "SG 1" "" "")
STAMP_HEADING(HB 10 "Key Item")

PAGE_VSPACE(3)

PAGE_TEXT(HN 10 "Detailed description of the stamp above, including historical context, printing details, and significance to the collection.")

PAGE_VSPACE(5)

ROW_START_FS(HN 9 0.5 7.0)
STAMP_ADD(35.0 40.0 "Second stamp description" "SG 2" "" "")
STAMP_ADD(35.0 40.0 "Third stamp description" "SG 3" "" "")
""",
    },
    {
        "id": "competition_comparison",
        "name": "Competition — Comparison Page",
        "description": "Side-by-side comparison layout for showing varieties, proofs, or related stamps.",
        "category": "Competition",
        "content": """# Competition — Comparison Page
ALBUM_TITLE("Exhibition Title")
ALBUM_AUTHOR("Exhibitor Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 20.0 15.0)
ALBUM_PAGES_BORDER(0.2 0.6 0.2 1.5)
ALBUM_PAGES_SPACING(8.0 8.0)
ALBUM_PAGES_TITLE(TB 18 "Comparison Study")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Variety Comparison")
PAGE_TEXT_CENTRE(HN 11 "Side-by-side comparison of different printings or varieties.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 1.0 8.0)
STAMP_ADD(40.0 35.0 "First variety\\nPerforation 14" "SG 1a" "" "")
STAMP_ADD(40.0 35.0 "Second variety\\nPerforation 12" "SG 1b" "" "")

PAGE_VSPACE(3)

PAGE_TEXT(HN 10 "Detailed comparison notes explaining the differences between the two varieties, including paper type, watermark, perforation measurements, and printing characteristics.")

PAGE_VSPACE(5)

ROW_START_FS(HN 8 1.0 8.0)
STAMP_ADD(40.0 35.0 "Third variety\\nColor shade A" "SG 1c" "" "")
STAMP_ADD(40.0 35.0 "Fourth variety\\nColor shade B" "SG 1d" "" "")
""",
    },
    {
        "id": "competition_postal_history",
        "name": "Competition — Postal History",
        "description": "Postal history layout showing covers, postmarks, and routing information.",
        "category": "Competition",
        "content": """# Competition — Postal History
ALBUM_TITLE("Postal History Exhibit")
ALBUM_AUTHOR("Exhibitor Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(20.0 15.0 20.0 15.0)
ALBUM_PAGES_BORDER(0.2 0.6 0.2 1.5)
ALBUM_PAGES_SPACING(8.0 8.0)
ALBUM_PAGES_TITLE(TB 18 "Postal History")

PAGE_START

PAGE_TEXT_CENTRE(HS 14 "Cover Study")
PAGE_TEXT_CENTRE(HN 11 "Detailed analysis of postal usage and routing.")

PAGE_VSPACE(5)

ROW_START_FS(HN 9 0.5 7.0)
STAMP_ADD(60.0 40.0 "Front of cover\\nShowing stamps and postmarks" "" "" "")
STAMP_ADD(60.0 40.0 "Back of cover\\nShowing transit marks" "" "" "")

PAGE_VSPACE(5)

PAGE_TEXT(HN 10 "This cover demonstrates the postal route from London to Calcutta via the Suez Canal, with transit marks from Alexandria and Bombay. The 2/6 Seahorse stamp paid the double-weight rate for printed matter.")

PAGE_RULE_H(0.3 3 0)

PAGE_VSPACE(3)

PAGE_TEXT(HN 9 "Postmark analysis: London circular date stamp, 14 March 1924. Transit: Alexandria 18 March, Bombay 22 March. Arrival: Calcutta 25 March.")
""",
    },
    # === MODERN LAYOUTS ===
    {
        "id": "modern_minimal",
        "name": "Modern — Minimal",
        "description": "Clean, minimalist design with generous white space and subtle styling.",
        "category": "Modern",
        "content": """# Modern Minimal
ALBUM_TITLE("Collection")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(25.0 25.0 20.0 20.0)
ALBUM_PAGES_SPACING(10.0 10.0)
ALBUM_PAGES_TITLE(HN 14 "Collection")

COLOUR_ALBUM_TITLE(gray)

PAGE_START

PAGE_TEXT(HN 11 "Section heading — left aligned")

PAGE_VSPACE(8)

ROW_START_FS(HN 8 1.0 6.0)
STAMP_ADD(30.0 35.0 "Description" "" "" "")
STAMP_ADD(30.0 35.0 "Description" "" "" "")

PAGE_VSPACE(10)

PAGE_TEXT(HN 11 "Additional notes or context for this page.")
""",
    },
    {
        "id": "modern_grid",
        "name": "Modern — Grid Layout",
        "description": "Structured grid layout with quadrille background for precise stamp placement.",
        "category": "Modern",
        "content": """# Modern Grid Layout
ALBUM_TITLE("Collection")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(15.0 15.0 15.0 15.0)
ALBUM_PAGES_SPACING(5.0 5.0)
ALBUM_PAGES_TITLE(HN 14 "Grid Collection")

PAGE_START

PAGE_QUADRILLE(180.0 250.0 5.0)

PAGE_TEXT_CENTRE(HS 12 "Section Title")

PAGE_VSPACE(5)

ROW_START_FS(HN 7 0.3 5.0)
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")

ROW_START_FS(HN 7 0.3 5.0)
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
""",
    },
    {
        "id": "modern_two_column",
        "name": "Modern — Two Column",
        "description": "Two-column layout for dense information display with text alongside stamps.",
        "category": "Modern",
        "content": """# Two Column Layout
ALBUM_TITLE("Collection")
ALBUM_AUTHOR("Collector Name")

ALBUM_PAGES_SIZE(210.0 297.0)
ALBUM_PAGES_MARGINS(15.0 15.0 15.0 15.0)
ALBUM_PAGES_BORDER(0.1 0.3 0.1 1.0)
ALBUM_PAGES_SPACING(5.0 5.0)
ALBUM_PAGES_TITLE(TB 14 "Two Column Album")

PAGE_START

PAGE_COLUMN_START(10.0)

PAGE_TEXT_CENTRE(HS 12 "Left Column")
ROW_START_FS(HN 7 0.3 5.0)
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")

PAGE_COLUMN_NEXT

PAGE_TEXT_CENTRE(HS 12 "Right Column")
ROW_START_FS(HN 7 0.3 5.0)
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")
STAMP_ADD(25.0 28.0 "Stamp" "" "" "")

PAGE_COLUMN_STOP
""",
    },
]
