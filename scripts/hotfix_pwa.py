from pathlib import Path
import re

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

# 1) Corrige o vazamento de código da v0.5, caso ainda esteja presente.
start_marker = "<script>window.onload=()=>setTimeout(()=>window.print(),200)<\\/script>\n<script>\n(function(){"
end_marker = "</script>\n</body></html>`);w.document.close();"
start = text.find(start_marker)
if start != -1:
    end = text.find(end_marker, start)
    if end == -1:
        raise SystemExit('v0.7: fim do bloco vazado não encontrado')
    replacement = "<script>window.onload=()=>setTimeout(()=>window.print(),200)<\\/script></body></html>`);w.document.close();"
    text = text[:start] + replacement + text[end + len(end_marker):]

# 2) Wrapper robusto: nunca deixa uma palavra/URL atravessar a coluna.
wrap_new = r'''function takeWrappedLine(doc,tokens,maxW){
  let line='';
  while(tokens.length){
    let token=tokens[0],candidate=line?line+' '+token:token;
    if(doc.getTextWidth(candidate)<=maxW){line=candidate;tokens.shift();continue}
    if(line)break;
    let part='',i=0;
    while(i<token.length){let test=part+token[i];if(doc.getTextWidth(test)>maxW&&part)break;part=test;i++}
    if(!part){part=token[0]||'';i=1}
    line=part;
    if(i>=token.length)tokens.shift();else tokens[0]=token.slice(i);
    break
  }
  return line
}
function wrapLines(doc,text,maxW){
  let tokens=String(text||'').split(/\s+/).filter(Boolean),lines=[];
  while(tokens.length){let line=takeWrappedLine(doc,tokens,maxW);if(!line)break;lines.push(line)}
  return lines
}
function wrapFirst(doc,text,firstW,fullW){
  let tokens=String(text||'').split(/\s+/).filter(Boolean);
  let first=takeWrappedLine(doc,tokens,firstW),rest=[];
  while(tokens.length){let line=takeWrappedLine(doc,tokens,fullW);if(!line)break;rest.push(line)}
  return{first,rest}
}'''
text, n = re.subn(r'function wrapFirst\(doc,text,firstW,fullW\)\{.*?\nfunction qMeasure', lambda m: wrap_new + '\nfunction qMeasure', text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'v0.7: não consegui substituir wrapFirst ({n})')

# 3) Perfis de diagramação + motor de PDF v0.7.
make_pdf_new = r'''const PROOF_PROFILES={
  economica:{label:'Econômica',fontSize:10,lead:3.72,questionGap:2.15,stemGap:1.15,sourceGap:.70,altGap:.40},
  compacta:{label:'Compacta',fontSize:11,lead:4.05,questionGap:4.30,stemGap:2.30,sourceGap:1.40,altGap:.80},
  normal:{label:'Normal',fontSize:12,lead:4.38,questionGap:8.60,stemGap:4.60,sourceGap:2.80,altGap:1.60}
};
function proofProfileName(){
  const select=document.getElementById('proofProfileSelect');
  const value=select?.value;
  if(value&&PROOF_PROFILES[value])return value;
  try{
    const saved=localStorage.getItem('adelita-proof-profile');
    if(saved&&PROOF_PROFILES[saved])return saved
  }catch(_){}
  return'compacta'
}
function getProofProfile(){return PROOF_PROFILES[proofProfileName()]||PROOF_PROFILES.compacta}
function installProofProfileControl(){
  if(document.getElementById('proofProfileSelect'))return;
  const wrap=document.createElement('label');
  wrap.id='proofProfileControl';
  wrap.style.cssText='display:inline-flex;align-items:center;gap:7px;flex-wrap:wrap;font:600 12px/1.2 system-ui,-apple-system,Segoe UI,sans-serif;color:inherit;margin:4px 8px 4px 0';
  const title=document.createElement('span');
  title.textContent='Formato da prova';
  const select=document.createElement('select');
  select.id='proofProfileSelect';
  select.setAttribute('aria-label','Formato da prova');
  select.style.cssText='font:600 12px/1 system-ui,-apple-system,Segoe UI,sans-serif;padding:8px 10px;border:1px solid #bbb;border-radius:8px;background:#fff;color:#222;max-width:230px';
  [
    ['normal','Normal · 12 pt · respiro 4×'],
    ['compacta','Compacta · 11 pt · respiro 2×'],
    ['economica','Econômica · 10 pt · respiro 1×']
  ].forEach(([value,label])=>{
    const option=document.createElement('option');
    option.value=value;option.textContent=label;select.appendChild(option)
  });
  let initial='compacta';
  try{
    const saved=localStorage.getItem('adelita-proof-profile');
    if(saved&&PROOF_PROFILES[saved])initial=saved
  }catch(_){}
  select.value=initial;
  select.addEventListener('change',()=>{
    try{localStorage.setItem('adelita-proof-profile',select.value)}catch(_){}
  });
  wrap.append(title,select);
  const buttons=[...document.querySelectorAll('button')];
  const anchor=buttons.find(b=>/(pdf|imprim|gerar.*(prova|avalia)|prova.*pdf)/i.test((b.textContent||'').trim()));
  if(anchor&&anchor.parentElement)anchor.parentElement.insertBefore(wrap,anchor);
  else (document.querySelector('main')||document.body).appendChild(wrap)
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installProofProfileControl);
else setTimeout(installProofProfileControl,0);

function makePdf(key=false){
  if(!pdfAvailable()){alert('O gerador de PDF não carregou. Use a opção de impressão do navegador ou abra com internet.');return null}
  let {jsPDF}=window.jspdf,h=headerData();
  if(key){
    let doc=new jsPDF({unit:'mm',format:'a4'});
    doc.setFont('helvetica','bold');doc.setFontSize(13);doc.text('GABARITO - '+h.title.toUpperCase(),105,15,{align:'center'});
    doc.setFontSize(8.5);doc.text(`${h.component} · ${h.className} · ${formatDate(h.date)}`,105,21,{align:'center'});
    doc.setFont('helvetica','normal');let y=31;
    state.exam.forEach((q,i)=>{let line=`${String(i+1).padStart(2,'0')}. ${q.o[q.c]?.l||'?'}   (${bancaAno(q)})   [${q.id}]`;let ls=doc.splitTextToSize(line,184);if(y+ls.length*4>287){doc.addPage();y=16}doc.text(ls,13,y);y+=ls.length*4+1.5});
    return doc
  }

  const p=getProofProfile();
  const margin=7,gap=4,colW=(210-margin*2-gap)/2,bottom=291,topNext=7.2;
  let doc=new jsPDF({unit:'mm',format:'a4'}),topFirst=addHeader(doc,h),col=0,y=topFirst;
  const xcol=()=>margin+col*(colW+gap);
  const pageTop=()=>doc.getNumberOfPages()===1?topFirst:topNext;
  function drawRule(){doc.setDrawColor(220);doc.setLineWidth(.12);doc.line(105,doc.getNumberOfPages()===1?topFirst:topNext,105,bottom)}
  drawRule();
  function nextCol(){if(col===0){col=1;y=pageTop()}else{doc.addPage();col=0;y=topNext;drawRule()}}
  function ensureLine(lead=p.lead){if(y+lead>bottom)nextCol()}
  function drawLines(lines,lead=p.lead,fontSize=p.fontSize,bold=false,indent=0){
    doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(fontSize);
    for(let line of lines){
      ensureLine(lead);
      const x=xcol();
      doc.text(line,x+indent,y);
      y+=lead
    }
  }

  state.exam.forEach((q,i)=>{
    // Evita começar uma questão no rodapé com espaço insuficiente para leitura.
    if(bottom-y<Math.max(10.5,p.lead*2.6))nextCol();

    doc.setFontSize(p.fontSize);doc.setFont('helvetica','bold');
    let prefix=`${i+1}. (${bancaAno(q)}) `,pw=doc.getTextWidth(prefix);
    doc.setFont('helvetica','normal');
    let wrapped=wrapFirst(doc,cleanText(q.t),Math.max(18,colW-pw),colW);

    ensureLine();
    let x=xcol();
    doc.setFont('helvetica','bold');doc.setFontSize(p.fontSize);doc.text(prefix,x,y);
    doc.setFont('helvetica','normal');if(wrapped.first)doc.text(wrapped.first,x+pw,y);
    y+=p.lead;
    drawLines(wrapped.rest);

    if(q.s){
      y+=p.sourceGap;
      drawLines(wrapLines(doc,cleanText(q.s),colW-1.4),p.lead,p.fontSize,false,1.4);
      y+=p.sourceGap;
    }

    // Respiro entre enunciado e alternativas.
    y+=p.stemGap;
    for(let o of q.o){
      doc.setFontSize(p.fontSize);doc.setFont('helvetica','bold');
      let letter=`${o.l}) `,lw=doc.getTextWidth(letter),txt=cleanText(o.t);
      doc.setFont('helvetica','normal');
      let wr=wrapFirst(doc,txt,Math.max(15,colW-lw),colW),linesN=(wr.first?1:0)+wr.rest.length,altH=linesN*p.lead+p.altGap;

      // Mantém a alternativa inteira quando ela cabe numa coluna limpa.
      if(y+altH>bottom && altH<(bottom-topNext-2))nextCol();
      ensureLine();
      x=xcol();
      doc.setFont('helvetica','bold');doc.setFontSize(p.fontSize);doc.text(letter,x,y);
      doc.setFont('helvetica','normal');if(wr.first)doc.text(wr.first,x+lw,y);
      y+=p.lead;
      drawLines(wr.rest);
      y+=p.altGap;
    }

    // Respiro entre a última alternativa e a questão seguinte.
    y+=p.questionGap;
  });
  return doc
}'''
text, n = re.subn(r'function makePdf\(key=false\)\{.*?\n\}\nasync function shareDoc', lambda m: make_pdf_new + '\nasync function shareDoc', text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'v0.7: não consegui substituir makePdf ({n})')

# 4) Impressão do navegador: mantém a mesma escolha de perfil.
text = text.replace(
    '.pqt{margin-bottom:1.15mm;orphans:2;widows:2}',
    '.pqt{margin-bottom:${getProofProfile().questionGap}mm;font-size:${getProofProfile().fontSize}pt;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}'
)
text = text.replace(
    '.pqt{margin-bottom:1.15mm;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}',
    '.pqt{margin-bottom:${getProofProfile().questionGap}mm;font-size:${getProofProfile().fontSize}pt;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}'
)
text = text.replace(
    '.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:.7mm 0 1.15mm;font-size:11pt;line-height:1.16}',
    '.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:${getProofProfile().sourceGap}mm 0 ${getProofProfile().stemGap}mm;font-size:${getProofProfile().fontSize}pt;line-height:1.16;overflow-wrap:anywhere;word-break:break-word}'
)
text = text.replace(
    '.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:.7mm 0 1.15mm;font-size:11pt;line-height:1.16;overflow-wrap:anywhere;word-break:break-word}',
    '.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:${getProofProfile().sourceGap}mm 0 ${getProofProfile().stemGap}mm;font-size:${getProofProfile().fontSize}pt;line-height:1.16;overflow-wrap:anywhere;word-break:break-word}'
)
text = text.replace(
    '.pa{margin:.4mm 0;break-inside:avoid-column;orphans:2;widows:2}',
    '.pa{margin:${getProofProfile().altGap}mm 0;break-inside:avoid-column;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word;font-size:${getProofProfile().fontSize}pt}'
)
text = text.replace(
    '.pa{margin:.4mm 0;break-inside:avoid-column;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}',
    '.pa{margin:${getProofProfile().altGap}mm 0;break-inside:avoid-column;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word;font-size:${getProofProfile().fontSize}pt}'
)

# 5) PWA e rótulo da versão.
marker = '// PWA-HOTFIX-v0.7'
text = re.sub(r'\n// PWA-HOTFIX-v0\.(?:5(?:\.1)?|6|7).*?(?=</script></body></html>)', '\n', text, flags=re.S)
if marker not in text:
    pwa_js = r'''
// PWA-HOTFIX-v0.7
let deferredPrompt=null;
const installButton=document.getElementById('installBtn');
window.addEventListener('beforeinstallprompt',e=>{
  e.preventDefault();deferredPrompt=e;
  if(installButton)installButton.style.display='inline-flex';
});
if(installButton)installButton.addEventListener('click',async()=>{
  if(!deferredPrompt)return;
  deferredPrompt.prompt();await deferredPrompt.userChoice;
  deferredPrompt=null;installButton.style.display='none';
});
window.addEventListener('appinstalled',()=>{if(installButton)installButton.style.display='none'});
if('serviceWorker' in navigator){window.addEventListener('load',async()=>{try{const reg=await navigator.serviceWorker.register('./sw.js');reg.update().catch(()=>{})}catch(err){console.warn('Service worker não registrado',err)}})}
'''
    outer_end = text.rfind('</script></body></html>')
    if outer_end == -1:
        raise SystemExit('v0.7: fechamento do script principal não encontrado')
    text = text[:outer_end] + pwa_js + text[outer_end:]

for old in ('0.5.1','0.5','0.6'):
    text = text.replace(f'Adelita v{old}</title>', 'Adelita v0.7</title>')
    text = text.replace(f'para a Profa. Adelita · v{old}</small>', 'para a Profa. Adelita · v0.7</small>')

# Guardas.
if start_marker in text:
    raise SystemExit('v0.7: bloco PWA vazado ainda presente')
if marker not in text:
    raise SystemExit('v0.7: registro PWA não inserido')
if 'drawLines(wrapped.rest,x' in text or 'drawLines(wr.rest,x' in text:
    raise SystemExit('v0.7: chamada antiga de drawLines permaneceu')
if 'function wrapLines' not in text:
    raise SystemExit('v0.7: wrapper robusto ausente')
if 'PROOF_PROFILES' not in text or 'proofProfileSelect' not in text:
    raise SystemExit('v0.7: perfis de prova não inseridos')

path.write_text(text, encoding='utf-8')
print('Hotfix v0.7 aplicado: Normal, Compacta e Econômica')
