from pathlib import Path
import shutil

site = Path('_site')
path = site / 'index.html'
text = path.read_text(encoding='utf-8')

# Cabeçalho v1.2: replica a composição aprovada manualmente pelo Luiz.
old = "children:[run([h.component,h.className,formatDate(h.date)].filter(Boolean).join(' · '),{size:17,color:'555555'})],"
new = "children:[run([h.component?`Disciplina: ${h.component}`:'',h.className&&h.className!=='__________'?`Turma: ${h.className}`:'',h.date?`Data: ${formatDate(h.date)}`:''].filter(Boolean).join(' · '),{size:17,color:'555555'})],"
if old not in text:
    raise SystemExit('v1.2: linha central do cabeçalho DOCX não encontrada')
text = text.replace(old, new, 1)

# O campo Nome/Nº vive dentro do cabeçalho do Word; um parágrafo real entre
# a faixa institucional e a identificação produz o respiro que o espaçamento
# do corpo não conseguia reproduzir de forma consistente.
old_header = "const firstHeader=new Header({children:[brandingTable,headerRule,nameLine]});"
new_header = "const firstHeader=new Header({children:[brandingTable,headerRule,new Paragraph({children:[run('')],spacing:{before:0,after:150}}),nameLine]});"
if old_header not in text:
    raise SystemExit('v1.2: firstHeader DOCX não encontrado')
text = text.replace(old_header, new_header, 1)

# Módulo local de comentários enriquecidos: nenhum comentário é publicado no
# repositório; o JSON é importado pelo usuário e permanece no IndexedDB local.
source = Path(__file__).with_name('commentary_v12.js')
if not source.exists():
    raise SystemExit('v1.2: commentary_v12.js ausente')
shutil.copy2(source, site / 'commentary_v12.js')
script = '<script src="./commentary_v12.js"></script>'
if script not in text:
    pos = text.rfind('</body>')
    if pos == -1:
        raise SystemExit('v1.2: fechamento </body> não encontrado')
    text = text[:pos] + script + text[pos:]

text = text.replace('Adelita v1.1</title>', 'Adelita v1.2</title>')
text = text.replace('para a Profa. Adelita · v1.1</small>', 'para a Profa. Adelita · v1.2</small>')

if 'Disciplina: ${h.component}' not in text:
    raise SystemExit('v1.2: identificação de disciplina não aplicada')
if 'commentary_v12.js' not in text:
    raise SystemExit('v1.2: importador de comentários não injetado')

path.write_text(text, encoding='utf-8')
print('Hotfix v1.2 aplicado: cabeçalho aprovado + comentários enriquecidos locais')
