#What to do:
#1. extracting the witnesses from the wikitext
#2. Checking for the specific F31
#3. Finding the [[File:F31x747.JPG]] for the facsimile attribute
#4. Generating a teiHeader with all the listWith

import re
import json
from pathlib import Path
import sys

#FIRST STEP: Setting the constants

input_file = "clean_corpus.json"
output_folder = Path("src/assets/data")
main_witness = "F31" #this than can be changed accordingly
#Wikidata tag to separate the header from the actual poem
poem_tag = "<poem>"

def make_safe_id(key: str) -> str:
    return (key
        .replace(' ', '_')
        .replace('.', '')
        .replace("'", '')
        .replace('(', '')        # (
        .replace(')', '')        # )
        .replace('\u2019', '')   # ’
        .replace(',', '')
        .replace('\u01c1', '')   # ǁ
        .replace('\u2016', '')   # ‖
        .lower())

##################################
#THE HEADER
##################################

#mapping a pattern for the other witnesses written in the Wikimedia link syntaxis [[R18]] or
#the [[separated by the | pipe]]
witness_pattern = re.compile(r"\[\[([A-Z]\d{2})(?:\|[^\]]*)?\]\]")

#pattern for the file imgs. It's really importat to make it strict because the code wasn't finding it
facsimile_pattern = re.compile(
    r'\[\[File:\s*([^\]|]+)(?:\|[^\]]+)?\]\]',
    flags=re.IGNORECASE
)

#<pb n="x"> moved
pb_pattern = re.compile(r'<pb\s+n="(\d+)"\s*/>')


##################################
#SECOND STEP: EXTRACTING

#extracting the witnesses and putting them into a list
#"le varianti prive di sigla esplicita vengono attribuite
#per default all'insieme dei testimoni dichiarati nell'header",
def extract_witnesses (header_block: str) -> list[str]:
  found = witness_pattern.findall(header_block)

  #avoiding duplicates
  seen = set()
  ordered = []
  for witness in found:
    if witness not in seen:
      seen.add(witness)
      ordered.append(witness)
  return ordered

#looking for the title in the wikidata link form [[F31 | title ]]
def extract_title (wikitext: str, fallback_title: str) -> str:
  match = re.search(r"\[\[Titolo:[^|]+\|([^\]]+)\]\]", wikitext)
  if match:
    raw_title = match.group(1)
    #removing the <lb>
    clean_title = re.sub(r"<lb/>\s*", " ", raw_title).strip()

    #PROBLEM; for some of the tiles it considers just the roman number (so we fallback on the json key)
    #the only solution i see is just to check for roman numbers as the only element in the title
    if not re.fullmatch(r'[IVXLCDM]+', clean_title):
      return clean_title

  clean_fallback = re.sub(r"\s+p\.\s*\d+$", "", fallback_title).strip()
  clean_fallback = re.sub(r"^[A-Z]\d{2}\s+", "", clean_fallback)
  return clean_fallback

#looking for all the [[File: f31xx.jpg]] and storing them into a LIST OF dictionaries, where we have xml_id and the filename
def extract_facsimiles (wikitext: str) -> list[dict[str, str]]:
  files = []
  for match in facsimile_pattern.finditer(wikitext):
    filename = match.group(1)
    xml_id = filename.rsplit(".", 1)[0]
    files.append({"xml_id": xml_id, "filename": filename})
  return files

#THIRD STEP:TEIHEADER GENERATION

#1. builing the <listWit> with every witness found
def build_witness_list (witnesses: list[str]) -> str:
  lines = ["<listWit>"]
  for witness in witnesses:
    lines.append(f'          <witness xml:id="{witness}">{witness}</witness>')
  lines.append(f"        </listWit>")
  return "\n".join(lines)

#2.builing the <facsimile> for the imgs
def build_facsimile (facsimile_files: list[dict]) -> str:
  if not facsimile_files:
    return ""
  lines = ["  <facsimile>"]
  for facsimile_file in facsimile_files:
    filename = facsimile_file["filename"] #retrieving the elements of the previous funcions
    xml_id = facsimile_file["xml_id"]

    lines.append(f'    <surface xml:id="{xml_id}">')
    lines.append(f'      <graphic url="./assets/img/{filename}"/>')
    lines.append('    </surface>')

  lines.append("  </facsimile>")
  return "\n".join(lines)

#3.generating the full header
def generate_tei_header (
    title: str,
    witnesses: list[str],
    encoder_name: str = "Chiara Picardi",
    publisher: str = "Progetto Canti - Edizione F31",
    year: str = "2024",
    source_bibl: str = "Edizione Fiorentina - F31 (1831)",
  ) -> str:

  list_wit = build_witness_list(witnesses)

  header = f"""  <teiHeader>
      <fileDesc>
        <titleStmt>
          <title>{title}</title>
          <author>Giacomo Leopardi</author>
          <respStmt>
            <resp>Encoded by</resp>
            <persName>{encoder_name}</persName>
          </respStmt>
        </titleStmt>
        <publicationStmt>
          <publisher>{publisher}</publisher>
          <date when="{year}">{year}</date>
          <availability status="free">
            <licence target="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</licence>
          </availability>
        </publicationStmt>
        <sourceDesc>
          <bibl>{source_bibl}</bibl>
        {list_wit}
        </sourceDesc>
      </fileDesc>
      <encodingDesc>
        <variantEncoding method="parallel-segmentation" location="internal"/>
      </encodingDesc>
    </teiHeader>"""

  return header

###############################
# BODY
##############################
def extract_structured_title(wikitext:str, default_title:str) -> str:
  #looking for all the tiles
  titles = re.findall(r"\[\[Titolo:([^|\]]+)\|([^\]]+)\]\]", wikitext, re.DOTALL)
  if not titles:
    return "<head> Title not found </head>"

  #the fist title is the lemm
  base_edition, base_text = titles[0]
  base_text = re.sub(r"<lb/>\s*", " ", base_text).strip()
  
  #PROBLEM: IF there no variants we don't need the apparatus, so we return just the head with the text
  if len(titles) == 1:
    return f'<head>{base_text}</head>'

  app_editions = []
  for edition, text, in titles[1:]:
    #an apparatus for the tiles
    text = re.sub(r"<lb/>\s*", " ", text).strip()
    app_editions.append(f'<rdg wit="#{edition}">{text}</rdg>')

  #if there are variants, othewise:
  if app_editions:
    return f'<head><app><lem wit="#{base_edition}">{base_text}</lem>{" ".join(app_editions)}</app></head>'

  return f'<head>{base_text}</head>'


def preprocess_body(text: str) -> str:

  #deleting empty links 
  text = re.sub(r'\[\[\s*Edizione critica\s*\|?\s*\]\]', '', text, flags=re.IGNORECASE)

  text = re.sub(r'F31\s+[IVXLCDM]+\.?<lb/>[IVXLCDM]+\.?<lb/>', '', text, flags=re.IGNORECASE)
  text = re.sub(r'[IVXLCDM]+\.\s+ALLA\s+PRIMAVERA,\s+O\s+DELLE\s+FAVOLE\s+ANTICHE\.', '', text)

  #1. deleting the patten with -< (few cases)
  text = re.sub(r'-\s*<\s*\n?', '<lb break="no"/>', text)

  #2. handling the sillabation at the end of the page
  text = re.sub(r'-\s*\n\s*', '<lb break="no"/>', text)
  
  #3.deleting the [[Title... ]] block
  text = re.sub(r"\[\[Titolo:[^\]]+\]\]", "", text)

  #4.removing the [File: ] from the body
  text = facsimile_pattern.sub("", text)

  #5.Removing the remaning witnesses in the text (they are explicited just in the title)
  text = re.sub(r"\[\[[A-Z]\d{2}[a-z]?\]\]", "", text)
  text = re.sub(r"\[\[[A-Z]\d{2}[a-z]?[^\]|]+\|[^\]]+\]\]", "", text)

  #4.Removing the tag <poem>
  text = re.sub(r'</?poem>', '', text, flags=re.IGNORECASE)
  text = re.sub(r'/?poem>', '', text, flags=re.IGNORECASE)
  text = re.sub(r"\b(NR25|CP25|NR26|CP26)\b", "", text, flags=re.IGNORECASE)  #these are critical apparatus that are not witnesses but they are written in the same way, so we need to remove them

  #removing the remaning HTML wikimedia tags
  text = re.sub(r'<DIV[^>]*>.*?</DIV>', '', text, flags=re.DOTALL|re.IGNORECASE)
  text = re.sub(r'<font[^>]*>.*?</font>', '', text, flags=re.DOTALL|re.IGNORECASE)
  text = text.replace('&emsp;', '&#x2003;').replace('&nbsp;', '&#x00A0;')

  #converting the italics 
  text = re.sub(r"&apos;&apos;(.*?)&apos;&apos;", r'<hi rend="italic">\1</hi>', text)
  text = re.sub(r"''(.*?)''", r'<hi rend="italic">\1</hi>', text)
  text = re.sub(r'\(\s*\)', '', text)

  text = re.sub(r'(NOTA|NOTE)\.?\s*(?:rend="indent")?\s*\(\)\s*', '', text, flags=re.IGNORECASE)
  text = re.sub(r'\s*rend="indent"\s*', ' ', text)

  text = text.replace("&apos;", "’")
  text = text.replace("'", "’")

  return text.strip()

#PROBLEM: sometimes the wikidata writes as a witness variant what is the same word,
#so it can be useful to check if the text are exactly the same
def avoid_repetition_appatatus (lem: str, rdg: str, wit:str) -> str:
  if lem == rdg:
    return lem
  return f'<app><lem wit="#{main_witness}">{lem}</lem><rdg wit="{wit}">{rdg}</rdg></app>'

#IMPORTANT STEP. Convering the wikilikins in the critical appratus
#cases:
  #1. [[Variant|Lem]] --> <app><lem>Lemma</lem><rdg wit="#WIT">Variante</rdg></app>
  #2. [[Acronym:Variante|Lemma]]--> <app><lem>Lemma</lem><rdg wit="#SIGLA">Variante</rdg></app>
  #3. [[text]] --> <app><lem>testo</lem><rdg wit="#WIT">testo</rdg></app>
      #  [in this case there is no alternative just a note or something marginal]
#re.sub does not relate to the text OUTSIDE SQUARE BRACKETS

def replace_wit(text: str, witnesses: list[str], main_witness: str) -> str:
  #PROBLEM: I NEED to clean the text before working on it
  def clean(text):
    text = re.sub(r"<lb/>\s*\n\s*", "<lb/>", text)
    return text.strip()

  #critical apparatus: PROBLEM most witnesses are not explicted in the text so MEANWHILE
  # we insert them all
  #to have the right TEI conformed id we must add the # to the whole string
  secondary_list = [f"#{w}" for w in witnesses if w != main_witness]
  secondary_wits_string = " ".join(secondary_list)

  #1.First case: the explicit witnesses [[Acronym:Variante|Lemma]]
  text = re.sub(
      r"\[\[([A-Z]\d{2}):([^\]|]+)\|([^\]]+)\]\]",
      lambda m: avoid_repetition_appatatus(
          clean(m.group(3)),
          clean(m.group(2)),
          f"#{m.group(1)}",
      ),
      text, flags=re.DOTALL
  )

  #2.Second case: Pipe case [[Variant|Lem]] this specific case needs a function
  #it contains <lb>
  def pipe(match: re.Match) -> str:
    lem = clean(match.group(2))
    rdg = clean(match.group(1))

    if "<lb/>" in rdg or "\n" in rdg:
      clean_rdg = rdg.replace("<lb/>", " ").replace("\n", " ")
      return (
                f'<!-- TRANSPOSITION: manual review needed -->'
                f'<app><lem wit="#{main_witness}">{lem}</lem>'
                f'<rdg wit="{secondary_wits_string}">{clean_rdg}</rdg></app>'
            )
    return avoid_repetition_appatatus(lem, rdg, secondary_wits_string)

  text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", pipe, text, flags=re.DOTALL)

  #Third case: the plain one [[testo]]
  text = re.sub(
        r"\[\[([^\]|]+)\]\]",
        lambda
        m: avoid_repetition_appatatus(
            clean(m.group(1)),
            clean(m.group(1)),
            secondary_wits_string,
        ),
        text,
        flags=re.DOTALL
    )

  return text

#reinserting the <pb> in the text and links them with the attribute facsimile to the images
#we already extracted them with the pre processing we just need to move them and connect them to the .jpg
def insert_pb(text:str, facs_files: list[dict]) -> str:
    facs_map = {}
    for f in facs_files:
      xml_id = f["xml_id"]
      page_num_match = re.search(r'\d{3}$', xml_id)
      if page_num_match:
        key = str(int(page_num_match.group(0)))
        facs_map[key] = f["xml_id"]

    def replacer(match):
      num = match.group(1)
      xml_id = facs_map.get(num)

      if xml_id:
        return f'<pb n="{num}" facs="#{xml_id}"/>'
      return f'<pb n="{num}"/>'

    return re.sub(r'<pb\s+n="(\d+)"\s*/>', replacer, text)

#chaning all the line in <l n="N"> or with the rend="indent"
def encode_verses(text:str) -> str:

  def verse_replacer(match):
    pb_part = match.group(1) if match.group(1) else ""
    num = match.group(2)
    rend = match.group(3)
    verse = match.group(4)
    rend_attribute = f' rend="indent"' if rend else ""
    rend_attribute = f' rend="indent"' if rend else ""
    return f'{pb_part}          <l n="{num}"{rend_attribute}>{verse}</l>'

  #Problem: deleting the roman number at the beginning 
  text = re.sub(r'^\s*[IVXLCDM]+\.\s*(?=\d+)', '', text, flags=re.MULTILINE)

  #extracting the verses num 
  return re.sub(
      r'^((?:<pb\s+[^>]+/>\s*)?)(\d+)(rend="indent")?\s*(.*)',
      verse_replacer,
      text,
      flags=re.MULTILINE,
  )

#complete ecoding of the body
def encode_body(text:str, witnesses: list[str], facs_files: list[dict], pb_extracted: str, json_key: str) -> str:

  #______ HANDLING PROSE _________ (critical note and letters)
  #PROBLEM the first try catched also "note" in poetry text
  jk_lower = json_key.lower()
  raw_text_stripped = text.strip()

  if "lettera" in jk_lower:
    div_type = "letter"
  elif "nota" in jk_lower or "note" in jk_lower or "annotazioni" in jk_lower or "commento" in jk_lower or raw_text_stripped.startswith("NOTA"):
    div_type = "note"
  else: #some poems start with a note, so if there is the word "nota" in the text but not in the title we consider it a note
    if not re.search(r'^\s*\d+\s+[A-Za-zÀ-ÿ]', text, re.MULTILINE):
      div_type = "nota"
    else: 
      div_type = "poem"

  is_prose = div_type in ["letter", "note"]

  if is_prose: 
    head_tag = extract_structured_title(text, witnesses[0] if witnesses else "")

    text = re.sub(r'(NOTA|NOTE)\.?(?:rend="indent")?\s*(?:\(\))?', '', text, flags=re.IGNORECASE)
    text = re.sub(r"\[\[Titolo:[^\]]*\]\]\s*", "", text)
    text = preprocess_body(text)
    text = replace_wit(text, witnesses, main_witness)
    text = text.replace("'", "’")

    text = re.sub(r'rend="indent"\s*', '', text) 
    text = re.sub(r'\(\)\s*', '', text)          
    text = re.sub(r'<font[^>]*>', '', text, flags=re.IGNORECASE)  
    text = re.sub(r'^\s*\(\)\s*', '', text)

    #in wikitext the paragraphs are divided by a double \n\n
    paragraphs = text.split("\n\n")
    p_blocks = []

    for p_text in paragraphs:
      if p_text.strip():
        #normalizing the text
        clean_p = re.sub(r'\s*\n\s*', ' ', p_text.strip())
        clean_p = re.sub(r'/?poem>', '', clean_p)
        p_blocks.append(f'        <p>{clean_p}</p>')

    body_prose = "\n".join(p_blocks)

    #I need a safe key for EVT visualization
    #deleting everything that is not a letter, number or underscore and replacing it with an underscore 
    head_label = ""
    if div_type == "letter":
      head_label = "LETTERA"
    elif "annotazioni" in jk_lower:
      head_label = "ANNOTAZIONI"
    elif "commento" in jk_lower:
      head_label = "COMMENTO"
    else: 
      head_label = "NOTA"

    safe_id = make_safe_id(json_key)
    corresp_attribute = ""
    if div_type == "note":
      #for the notes we also add a corresp attribute to link them to the canto
      canto_clean = re.sub(r'[\s_]*\(not[ae]\).*$', '', json_key, flags=re.IGNORECASE)
      canto_clean = re.sub(r'[\s_]*annotazioni.*$', '', canto_clean, flags=re.IGNORECASE)
      canto_clean = re.sub(r'[\s_]+p\.\s*\d+$', '', canto_clean, flags=re.IGNORECASE)
      canto_clean = re.sub(r'[\s_]+p_\d+$', '', canto_clean, flags=re.IGNORECASE)
      canto_id = make_safe_id(canto_clean)
      corresp_attribute = f' corresp="#{canto_id}"'

    return f"""  <text>
        <body>
          <div type="{div_type}" xml:id="{safe_id}" {corresp_attribute}>
            <head>{head_label}</head>
    {pb_extracted}        {body_prose}
          </div>
        </body>
      </text>"""

  #_______ HANDLING POETRY ____________

  #Saving the roman number to avoid losing it
  roman_match = re.search(r'^\s*([IVXLCDM]+\.)', text)
  roman_prefix = roman_match.group(1) if roman_match else ""

  #title management: extracting it and then deleting it from the text
  head_tag = extract_structured_title(text, witnesses[0] if witnesses else "")

  if ("Title not found" in head_tag or 
      ('wit="#' in head_tag and not re.search(r'wit="#[A-Z]\d{2}"', head_tag)) or 
      '<lb/>' in head_tag):
    #fallback title from the JSON key
    clean_key = re.sub(r'^[A-Z]\d{2}\s+', '', json_key)
    clean_key = re.sub(r'\s+p\.\s*\d+$', '', clean_key)
    head_tag =f'        <head>{clean_key.strip()}</head>'

    #removing the titile in the first line
    lines = text.split('\n')
    if lines and any(word in lines[0] for word in clean_key.split()): 
      lines.pop(0) # Remove the first line if it contains the title
    text = '\n'.join(lines) 
  
  elif roman_prefix:
    #if there is a title with a roman number before, we put it on the head tag
    head_tag = head_tag.replace("<head>", f"        <head>{roman_prefix} ")


  text = re.sub(r'^[IVXLCDM]+\.\s*', '', text)
  text = re.sub(r"\[\[Titolo:[^\]]*\]\]\s*", "", text)
  
  #normalizing preprocessing and noise removal
  text = preprocess_body(text)
  #removing the ()
  text = re.sub(r'^\s*\(\)\s*', '', text.strip())

  #encoding
  text = re.sub(r'<pb\s+[^>]+/>\s*', '', text) #removing the residual <pb>
  text = encode_verses(text)

  text = replace_wit(text, witnesses, main_witness)

  #cleaning the remaning tags
  text = re.sub(r"</?poem>", "", text)
  text = re.sub(r"\n{3,}", "\n\n", text).strip()

  #PROBLEM for EVT 3 visualization 
  safe_id = make_safe_id(json_key)
  
  return f"""  <text>
    <body>
      <div type="poem" xml:id="{safe_id}">
        {head_tag}
{pb_extracted}        <lg>
{text}
        </lg>
      </div>
    </body>
  </text>"""

#########################
#ASSEMBLY
########################
def assemble_tei(header:str, facsimile: str, body: str) -> str:
  facs_block = f"\n{facsimile}\n" if facsimile.strip() else ""
  return  (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">\n'
        f"{header}\n"
        f"{facs_block}\n"
        f"{body}\n"
        "</TEI>\n"
    )

def convert(json_key: str, raw_text: str, witnesses_body: list[str], witnesses_header: list[str]) -> str:
  if not raw_text:
    raw_text = ""

  raw_text = re.sub(r'\[\[\s*Edizione critica\s*\|?\s*\]\]', '', raw_text, flags=re.IGNORECASE)
  raw_text = re.sub(r'F31\s+[IVXLCDM]+\.?<lb/>[IVXLCDM]+\.?<lb/>', '', raw_text, flags=re.IGNORECASE)
  raw_text = re.sub(r'[IVXLCDM]+\.\s+ALLA\s+PRIMAVERA,\s+O\s+DELLE\s+FAVOLE\s+ANTICHE\.', '', raw_text)
  
  title = extract_title(raw_text, fallback_title=json_key)
  facs_files = extract_facsimiles(raw_text)

  #Try:
  raw_text_with_facs = insert_pb(raw_text, facs_files)

  #Pre-processing to isolate verse numbers
  def isolate_verse_num(text:str) -> str:
    #checking for the numbers in the end of a line and inserts \n
    #looking for verses num near the rend=tag
    text = re.sub(r'([^\n>])\s*(\d+)(rend=)', r'\1\n\2\3', text)
    #PROBLEMI, SPECIFIC CASE: the number is between two apparatus so the number
    #is not recognized. Must change re and use also an execption for the numbers
    #who have p. previously
    text = re.sub(
        r'(?<!p\.)(?<!p\.\s)(?<!n=\")(?<!facs=\")(?<!wit=\")\b(\d{1,3})\b\s+(?=[A-Za-zÀ-ÿ\[\(’"“<])',        
        r'\n\1 ',
        text
    )

    return text

  raw_text_with_facs = isolate_verse_num(raw_text_with_facs)

  #I must divide the header from the body for a more precise listing of the witnesses
  #using the <poem>
  pb_matches = re.findall(r'(<pb\s+[^>]+/>)', raw_text_with_facs)
  pb_extracted = ""
  if pb_matches:
    pb_extracted = "".join(f"        {pb}\n" for pb in pb_matches)

  #clean the text
  clean_text = re.sub(r'(<pb\s+[^>]+/>)', "", raw_text_with_facs)

  if poem_tag in clean_text:
    header_part, body_part = clean_text.split(poem_tag, 1)
  else:
    header_part = clean_text
    body_part = clean_text

  header = generate_tei_header(title, witnesses_header)
  facsimile = build_facsimile(facs_files)

  body = encode_body(body_part, witnesses_body, facs_files, pb_extracted, json_key)

  return assemble_tei(header, facsimile, body)

################
#Utility

def load_data():
  with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)
  return data

#exectuting the script
def run_all():

  output_folder.mkdir(exist_ok=True)
  data = load_data()

  #PROBLEM: if the page doesn't contain the witness list it does not link it to all the references.
  #for every canto find the witness of the first page
  #scanning the whole document
  canto_witnesses_set = {}
  canto_titles = {}

  global_witnesses = set()

  #global scan
  for key, text in data.items():
    #identifying the KEY of the canto
    canto_match = re.search(r"CANTO\s+\w+", key)
    if not canto_match:
      continue
    canto = canto_match.group(0)

    #1. Extracting the witnesses of the page
    header_part = text.split(poem_tag, 1)[0] if poem_tag in text else text
    page_witnesses = extract_witnesses(header_part)

    for wit in page_witnesses:
      global_witnesses.add(wit)

    if canto not in canto_witnesses_set:
      canto_witnesses_set[canto] = set()

    if page_witnesses:
      canto_witnesses_set[canto].update(page_witnesses)

    #2. Extracting the title
    title = extract_title(text, fallback_title="")
    if title:
      canto_titles[canto] = title

  #putting it again in the set
  canto_witnesses = {}
  for canto, wits in canto_witnesses_set.items():
      canto_witnesses[canto] = sorted(list(wits))

  #initizing the two fallback lists
  body_set = global_witnesses.copy()
  body_set.discard(main_witness)
  body_fallback_witnesses = sorted(list(body_set))

  head_set = global_witnesses.copy()
  head_fallback_witnesses = sorted(list(head_set))

  #conversion loop
  for key, text in data.items():
      try:
        m = re.search(r"CANTO\s+[IVXLC]+", key) #looking for the title
        canto_key = m.group(0) if m else None

        current_witnesses = canto_witnesses.get(canto_key, [])

        #handling the missing acronym for witnesses
        if not current_witnesses or current_witnesses == [main_witness]:
          body_witnesses = body_fallback_witnesses
          head_witnesses = sorted(list(set(head_fallback_witnesses + [main_witness])))
        else:
          body_witnesses = current_witnesses
          head_witnesses = list(current_witnesses)
          if main_witness not in head_witnesses:
            head_witnesses.append(main_witness)

        xml = convert(key, text, body_witnesses, head_witnesses)

        clean_name = f"{make_safe_id(key)}.xml"
        (output_folder / clean_name).write_text(xml, encoding="utf-8")
        print(f" ✓ {clean_name}")
      except Exception as e:
        print(f" ✗ {key}: {e}")

if __name__ == "__main__":
        run_all()

