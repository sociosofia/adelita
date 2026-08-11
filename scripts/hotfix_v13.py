from pathlib import Path
import shutil

site=Path('_site')
index=site/'index.html'
history=site/'history_v11.js'
text=index.read_text(encoding='utf-8')
h=history.read_text(encoding='utf-8')

lookup=Path(__file__).with_name('commentary_lookup_v13.js')
if not lookup.exists():
    raise SystemExit('v1.3: commentary_lookup_v13.js ausente')
shutil.copy2(lookup,site/'commentary_lookup_v13.js')

# A importação manual de JSON da v1.2 deixa de fazer parte da interface.
# Na v1.3 a consulta só acontece, questão por questão, quando a professora pede.
text=text.replace('<script src="./commentary_v12.js"></script>','')
script='<script src="./commentary_lookup_v13.js"></script>'
if script not in text:
    pos=text.rfind('</body>')
    if pos<0: raise SystemExit('v1.3: </body> não encontrado')
    text=text[:pos]+script+text[pos:]
text=text.replace('Adelita v1.2</title>','Adelita v1.3</title>')
text=text.replace('para a Profa. Adelita · v1.2</small>','para a Profa. Adelita · v1.3</small>')

old="""    if(commented&&!hasCommentary(qs)){
      alert('O banco atual contém os gabaritos, mas esta seleção ainda não possui comentários enriquecidos suficientes para gerar o gabarito comentado.');
      return;
    }
"""
new="""    let lookupStats=null;
    if(commented&&window.AdelitaCommentaryLookup?.enrichQuestions){
      const keyBtn=document.getElementById('keyDocxBtn');
      const oldLabel=keyBtn?.textContent;
      if(keyBtn){keyBtn.disabled=true;keyBtn.textContent='Buscando comentários…'}
      try{
        lookupStats=await window.AdelitaCommentaryLookup.enrichQuestions(qs,{onProgress:p=>{
          if(keyBtn&&p.total)keyBtn.textContent=`Buscando comentários ${p.done}/${p.total}…`;
        }});
      }catch(err){console.warn('Busca de comentários indisponível',err)}
      finally{if(keyBtn){keyBtn.disabled=false;keyBtn.textContent=oldLabel||'⬇️ Gerar gabarito DOCX'}}
    }
    // Falha de rede ou ausência de resolução nunca bloqueia a geração:
    // se nenhum comentário foi encontrado, cai automaticamente no gabarito simples.
    if(commented&&!hasCommentary(qs))commented=false;
"""
if old not in h:
    raise SystemExit('v1.3: guarda antiga do gabarito comentado não encontrada')
h=h.replace(old,new,1)

old_intro="""      children.push(new Paragraph({children:[run('Documento de revisão da professora. Os comentários abaixo só aparecem quando existem dados enriquecidos no banco; a Adelita não inventa justificativas ausentes.',{italics:true,size:18,color:'555555'})],spacing:{after:180}}));
      qs.forEach((q,i)=>{
        const correct=questionCorrectOption(q);
        children.push(new Paragraph({children:[run(`${i+1}. (${bancaAno(q)}) `,{bold:true,size:21}),run(cleanText(q.t),{size:21})],spacing:{before:i?180:0,after:90,line:276},widowControl:true}));
"""
new_intro="""      const found=lookupStats?.found;
      const note=Number.isInteger(found)?`Documento de revisão da professora. Comentários encontrados para ${found} de ${qs.length} questões; quando não há comentário disponível, aparece apenas o gabarito.`:'Documento de revisão da professora. Os comentários aparecem somente quando existem dados enriquecidos disponíveis; a Adelita não inventa justificativas ausentes.';
      children.push(new Paragraph({children:[run(note,{italics:true,size:18,color:'555555'})],spacing:{after:180}}));
      qs.forEach((q,i)=>{
        const correct=questionCorrectOption(q),answer=correct?String(correct.l):'—';
        const thisHas=!!(generalComment(q)||(q.o||[]).some((o,idx)=>optionComment(q,o,idx)));
        if(!thisHas){
          children.push(new Paragraph({children:[run(`${i+1}. ${answer}`,{bold:true,size:21}),run(` · ${bancaAno(q)} · comentário não disponível`,{size:18,color:'666666'})],spacing:{before:i?150:0,after:85,line:250}}));
          return;
        }
        children.push(new Paragraph({children:[run(`${i+1}. (${bancaAno(q)}) `,{bold:true,size:21}),run(cleanText(q.t),{size:21})],spacing:{before:i?180:0,after:90,line:276},widowControl:true}));
"""
if old_intro not in h:
    raise SystemExit('v1.3: bloco comentado não encontrado')
h=h.replace(old_intro,new_intro,1)

start=h.find('  function installKeyButtons(){')
end=h.find('\n  function updateKeyButtonState(){',start)
if start<0 or end<0:
    raise SystemExit('v1.3: installKeyButtons não encontrado')
new_install="""  function installKeyButtons(){
    const toolbar=document.getElementById('toolbar');if(!toolbar)return;
    document.getElementById('secondaryTools')?.remove();
    ['sharePdf','savePdf','printBrowser','shareKey','saveKey','apply','proofProfileControl','commentedKeyDocxBtn','commentaryImportBtn'].forEach(id=>document.getElementById(id)?.remove());
    let key=document.getElementById('keyDocxBtn');
    if(!key){key=document.createElement('button');key.id='keyDocxBtn';key.className='btn';toolbar.appendChild(key)}
    key.textContent='⬇️ Gerar gabarito DOCX';
    let wrap=document.getElementById('keyCommentLookupWrap');
    if(!wrap){
      wrap=document.createElement('label');wrap.id='keyCommentLookupWrap';wrap.className='key-comment-lookup';
      wrap.innerHTML='<input type="checkbox" id="keyCommentLookup"> <span>Buscar comentários disponíveis</span>';
      key.insertAdjacentElement('afterend',wrap);
    }
    key.onclick=()=>makeKeyDocx(currentKeySnapshot(),{commented:!!document.getElementById('keyCommentLookup')?.checked});
    updateKeyButtonState();
  }
"""
h=h[:start]+new_install+h[end:]

start=h.find('  function updateKeyButtonState(){')
end=h.find('\n  function installHistoryStyles(){',start)
if start<0 or end<0:
    raise SystemExit('v1.3: updateKeyButtonState não encontrado')
new_update="""  function updateKeyButtonState(){
    const n=(state.exam||[]).length;
    const key=document.getElementById('keyDocxBtn');if(key)key.disabled=!n;
    const lookup=document.getElementById('keyCommentLookup');if(lookup)lookup.disabled=!n;
  }
"""
h=h[:start]+new_update+h[end:]

# No histórico, o botão comentado também consulta sob demanda; não precisa saber
# previamente se aquela prova já tinha comentários gravados localmente.
h=h.replace("${comment?'':'disabled title=\"Comentários enriquecidos ainda indisponíveis\"'}",'title="Busca comentários disponíveis na hora"')

# Estilo do novo controle ao lado do gabarito.
h=h.replace('.toolbar>#commentedKeyDocxBtn{order:-1}', '.toolbar>#keyCommentLookupWrap{order:-1}')
h=h.replace('@media(max-width:600px){.hist-v11-head', '.key-comment-lookup{display:flex;align-items:center;gap:6px;padding:7px 9px;border:1px solid var(--line);border-radius:10px;background:#fff;font-size:12px;cursor:pointer;white-space:nowrap}.key-comment-lookup input{accent-color:#222}@media(max-width:600px){.hist-v11-head')
h=h.replace('.toolbar .btn{flex:1 1 100%}', '.toolbar .btn{flex:1 1 100%}.toolbar>#keyCommentLookupWrap{flex:1 1 100%;justify-content:center}')

if '// ADELITA-REMOTE-COMMENTS-v1.3' not in h:
    h=h.replace('// ADELITA-HISTORY-KEYS-v1.1','// ADELITA-HISTORY-KEYS-v1.1\n// ADELITA-REMOTE-COMMENTS-v1.3',1)

history.write_text(h,encoding='utf-8')
index.write_text(text,encoding='utf-8')

if 'keyCommentLookup' not in h:
    raise SystemExit('v1.3: checkbox de comentários não aplicado')
if './commentary_v12.js' in text:
    raise SystemExit('v1.3: importador antigo ainda está ativo')
if './commentary_lookup_v13.js' not in text:
    raise SystemExit('v1.3: lookup remoto não foi injetado')
print('Hotfix v1.3 aplicado: gabarito DOCX com busca opcional de comentários por questão')
