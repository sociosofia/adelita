from pathlib import Path

site=Path('_site')
index=site/'index.html'
history=site/'history_v11.js'
sw=site/'sw.js'
text=index.read_text(encoding='utf-8')
h=history.read_text(encoding='utf-8')

# Se a professora marcou a busca, o DOCX permanece no formato comentado mesmo
# quando nenhum comentário foi localizado. Assim, 0/N fica visível e a falha
# nunca se confunde com a opção desmarcada.
h=h.replace("if(commented&&!hasCommentary(qs))commented=false;", "if(commented&&!hasCommentary(qs)&&lookupStats)console.info(`Nenhum comentário encontrado: 0/${qs.length}`);")

for oldv in ('v1.4','v1.3.2','v1.3.1','v1.3'):
    text=text.replace(f'Adelita {oldv}</title>','Adelita v1.4.1</title>')
    text=text.replace(f'para a Profa. Adelita · {oldv}</small>','para a Profa. Adelita · v1.4.1</small>')

# Força o navegador a buscar a nova versão de commentary_lookup_v13.js.
if sw.exists():
    s=sw.read_text(encoding='utf-8')
    for oldv in ('adelita-pwa-v1.4','adelita-pwa-v1.3.2','adelita-pwa-v1.3.1','adelita-pwa-v1.3'):
        s=s.replace(oldv,'adelita-pwa-v1.4.1')
    sw.write_text(s,encoding='utf-8')

history.write_text(h,encoding='utf-8')
index.write_text(text,encoding='utf-8')

if 'Nenhum comentário encontrado' not in h:
    raise SystemExit('v1.4.1: fallback explícito não aplicado')
print('Hotfix v1.4.1 aplicado: lookup corrigido e resultado da busca explícito no DOCX')
