from pathlib import Path
import gzip, base64

site = Path('_site')
path = site / 'index.html'
text = path.read_text(encoding='utf-8')

# v1.1: mais espaço na primeira página sem alterar as páginas seguintes.
text = text.replace("children.push(new Paragraph({children:[run('')],spacing:{before:0,after:150}}));",
                    "children.push(new Paragraph({children:[run('')],spacing:{before:0,after:360}}));")
text = text.replace("spacing:{before:35,after:55}", "spacing:{before:60,after:120,line:300}")

# Professora padrão completa também para campos vazios/legados.
text = text.replace("teacher:$('#teacher').value.trim()||'Adelita'", "teacher:$('#teacher').value.trim()||'Profa. Adelita Xavier'")

parts = []
for name in ('history_v11.part1', 'history_v11.part2', 'history_v11.part3'):
    parts.append((Path(__file__).with_name(name)).read_text(encoding='utf-8').strip())
js = gzip.decompress(base64.b64decode(''.join(parts)))
(site / 'history_v11.js').write_bytes(js)

script = '<script src="./history_v11.js"></script>'
if script not in text:
    pos = text.rfind('</body>')
    if pos == -1:
        raise SystemExit('v1.1: fechamento </body> não encontrado')
    text = text[:pos] + script + text[pos:]

text = text.replace('Adelita v1.0</title>', 'Adelita v1.1</title>')
text = text.replace('para a Profa. Adelita · v1.0</small>', 'para a Profa. Adelita · v1.1</small>')

if './history_v11.js' not in text:
    raise SystemExit('v1.1: histórico não injetado')
if "after:360" not in text:
    raise SystemExit('v1.1: respiro da primeira página não aplicado')
if b'ADELITA-HISTORY-KEYS-v1.1' not in js:
    raise SystemExit('v1.1: módulo de histórico inválido')

path.write_text(text, encoding='utf-8')
print('Hotfix v1.1 aplicado: histórico local, gabaritos DOCX, PDF removido da interface e respiro ampliado')
