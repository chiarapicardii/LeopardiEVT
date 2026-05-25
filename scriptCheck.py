import re
import os
from lxml import etree

def fix_syntax_errors(content):
    """Corregge i tag intrecciati più comuni prima che il parser li legga."""
    print("-> Pulizia tag intrecciati in corso...")
    # Corregge i casi dove il tag l si chiude prima di app o lg
    content = content.replace('</l></app>', '</app></l>')
    content = content.replace('</l></lg>', '</lg></l>')
    return content

def process_all_in_one(input_path, output_path):
    # 1. Leggi il file originale
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 2. Pulisci la sintassi
    content = fix_syntax_errors(content)

    # 3. Parsa il file (con recover=True per ignorare errori minori)
    print("-> Parsing XML...")
    parser = etree.XMLParser(recover=True, remove_blank_text=True)
    tree = etree.fromstring(content.encode('utf-8'), parser)
    
    # 4. Suddivisione dei versi
    print("-> Suddivisione versi in corso...")
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    pattern = re.compile(r'[.\s]+(\d+)[.\s]+')
    lines = tree.xpath('//tei:l', namespaces=ns)

    for line in lines:
        if line.text and pattern.search(line.text):
            match = pattern.search(line.text)
            split_idx = match.start()
            new_verse_num = match.group(1)
            remaining_text = line.text[match.end():]
            
            # Tronca il verso originale
            line.text = line.text[:split_idx]
            
            # Crea nuovo verso
            new_l = etree.Element(f"{{{ns['tei']}}}l", n=new_verse_num)
            new_l.text = remaining_text
            
            # Inserisci dopo
            line.addnext(new_l)

    # 5. Salva
    print(f"-> Salvataggio in {output_path}...")
    with open(output_path, 'wb') as f:
        f.write(etree.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True))
    print("Operazione completata con successo!")

# Esecuzione
if __name__ == "__main__":
    input_file = "src/assets/data/preLeopardi.xml"
    output_file = "src/assets/data/canti_completi.xml"
    
    if os.path.exists(input_file):
        process_all_in_one(input_file, output_file)
    else:
        print(f"Errore: File non trovato in {input_file}")