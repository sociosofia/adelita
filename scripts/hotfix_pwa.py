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
        raise SystemExit('v0.6: fim do bloco vazado não encontrado')
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
    raise SystemExit(f'v0.6: não consegui substituir wrapFirst ({n})')

# 3) Motor de PDF v0.6: cursor e coluna recalculados a cada linha.
make_pdf_new = r'''function makePdf(key=false){
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

  // v0.6: fluxo linear, fonte 11 e paginação estável.
  const margin=7,gap=4,colW=(210-margin*2-gap)/2,bottom=291,topNext=7.2;
  let doc=new jsPDF({unit:'mm',format:'a4'}),topFirst=addHeader(doc,h),col=0,y=topFirst;
  const xcol=()=>margin+col*(colW+gap);
  const pageTop=()=>doc.getNumberOfPages()===1?topFirst:topNext;
  function drawRule(){doc.setDrawColor(220);doc.setLineWidth(.12);doc.line(105,doc.getNumberOfPages()===1?topFirst:topNext,105,bottom)}
  drawRule();
  function nextCol(){if(col===0){col=1;y=pageTop()}else{doc.addPage();col=0;y=topNext;drawRule()}}
  function ensureLine(lead){if(y+lead>bottom)nextCol()}
  function drawLines(lines,lead,fontSize,bold=false,indent=0){
    doc.setFont('helvetica',bold?'bold':'normal');doc.setFontSize(fontSize);
    for(let line of lines){
      ensureLine(lead);
      const x=xcol();
      doc.text(line,x+indent,y);
      y+=lead
    }
  }

  state.exam.forEach((q,i)=>{
    // Não inicia uma questão no rodapé com só uma linha disponível.
    if(bottom-y<10.5)nextCol();

    doc.setFontSize(11);doc.setFont('helvetica','bold');
    let prefix=`${i+1}. (${bancaAno(q)}) `,pw=doc.getTextWidth(prefix);
    doc.setFont('helvetica','normal');
    let wrapped=wrapFirst(doc,cleanText(q.t),Math.max(18,colW-pw),colW);

    ensureLine(4.05);
    let x=xcol();
    doc.setFont('helvetica','bold');doc.text(prefix,x,y);
    doc.setFont('helvetica','normal');if(wrapped.first)doc.text(wrapped.first,x+pw,y);
    y+=4.05;
    drawLines(wrapped.rest,4.05,11,false);

    if(q.s){
      y+=.7;
      drawLines(wrapLines(doc,cleanText(q.s),colW-1.4),4.05,11,false,1.4);
      y+=.7;
    }

    // Respiro entre enunciado e alternativas.
    y+=1.15;
    for(let o of q.o){
      doc.setFontSize(11);doc.setFont('helvetica','bold');
      let letter=`${o.l}) `,lw=doc.getTextWidth(letter),txt=cleanText(o.t);
      doc.setFont('helvetica','normal');
      let wr=wrapFirst(doc,txt,Math.max(15,colW-lw),colW),linesN=(wr.first?1:0)+wr.rest.length,altH=linesN*4.05+.4;

      // Mantém a alternativa inteira quando ela cabe numa coluna limpa.
      if(y+altH>bottom && altH<(bottom-topNext-2))nextCol();
      ensureLine(4.05);
      x=xcol();
      doc.setFont('helvetica','bold');doc.setFontSize(11);doc.text(letter,x,y);
      doc.setFont('helvetica','normal');if(wr.first)doc.text(wr.first,x+lw,y);
      y+=4.05;
      drawLines(wr.rest,4.05,11,false);
      y+=.4;
    }
    // Respiro entre a última alternativa e a questão seguinte.
    y+=2.15;
  });
  return doc
}'''
text, n = re.subn(r'function makePdf\(key=false\)\{.*?\n\}\nasync function shareDoc', lambda m: make_pdf_new + '\nasync function shareDoc', text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'v0.6: não consegui substituir makePdf ({n})')

# 4) Impressão do navegador: URLs também podem quebrar sem invadir a outra coluna.
text = text.replace('.pqt{margin-bottom:1.15mm;orphans:2;widows:2}', '.pqt{margin-bottom:1.15mm;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}')
text = text.replace('.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:.7mm 0 1.15mm;font-size:11pt;line-height:1.16}', '.ps{border-left:1pt solid #aaa;padding-left:1.2mm;margin:.7mm 0 1.15mm;font-size:11pt;line-height:1.16;overflow-wrap:anywhere;word-break:break-word}')
text = text.replace('.pa{margin:.4mm 0;break-inside:avoid-column;orphans:2;widows:2}', '.pa{margin:.4mm 0;break-inside:avoid-column;orphans:2;widows:2;overflow-wrap:anywhere;word-break:break-word}')

# 5) PWA e rótulo da versão.
marker = '// PWA-HOTFIX-v0.6'
text = re.sub(r'\n// PWA-HOTFIX-v0\.5\.1.*?(?=</script></body></html>)', '\n', text, flags=re.S)
if marker not in text:
    pwa_js = r'''
// PWA-HOTFIX-v0.6
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
    if outer_end == -1: raise SystemExit('v0.6: fechamento do script principal não encontrado')
    text = text[:outer_end] + pwa_js + text[outer_end:]

text = text.replace('Adelita v0.5</title>', 'Adelita v0.6</title>')
text = text.replace('Adelita v0.5.1</title>', 'Adelita v0.6</title>')
text = text.replace('para a Profa. Adelita · v0.5</small>', 'para a Profa. Adelita · v0.6</small>')
text = text.replace('para a Profa. Adelita · v0.5.1</small>', 'para a Profa. Adelita · v0.6</small>')

# Guardas.
if start_marker in text: raise SystemExit('v0.6: bloco PWA vazado ainda presente')
if marker not in text: raise SystemExit('v0.6: registro PWA não inserido')
if 'drawLines(wrapped.rest,x' in text or 'drawLines(wr.rest,x' in text: raise SystemExit('v0.6: chamada antiga de drawLines permaneceu')
if 'function wrapLines' not in text: raise SystemExit('v0.6: wrapper robusto ausente')

path.write_text(text, encoding='utf-8')
print('Hotfix v0.6 aplicado')
