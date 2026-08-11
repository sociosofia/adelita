from pathlib import Path

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

marker = '// DOCX-EXPORT-v0.9'

if marker not in text:
    js = r'''

// DOCX-EXPORT-v0.9
const ADELITA_DOCX_LIB='https://cdn.jsdelivr.net/npm/docx@9.7.1/dist/index.iife.js';

function loadAdelitaDocx(){
  if(window.docx?.Document&&window.docx?.Packer)return Promise.resolve(window.docx);
  if(window.__adelitaDocxPromise)return window.__adelitaDocxPromise;
  window.__adelitaDocxPromise=new Promise((resolve,reject)=>{
    const existing=document.querySelector('script[data-adelita-docx]');
    if(existing){
      existing.addEventListener('load',()=>window.docx?.Document?resolve(window.docx):reject(new Error('Biblioteca DOCX carregada sem API esperada')),{once:true});
      existing.addEventListener('error',()=>reject(new Error('Falha ao carregar biblioteca DOCX')),{once:true});
      return;
    }
    const script=document.createElement('script');
    script.src=ADELITA_DOCX_LIB;
    script.async=true;
    script.dataset.adelitaDocx='1';
    script.onload=()=>window.docx?.Document?resolve(window.docx):reject(new Error('Biblioteca DOCX carregada sem API esperada'));
    script.onerror=()=>reject(new Error('Falha ao carregar biblioteca DOCX'));
    document.head.appendChild(script);
  });
  return window.__adelitaDocxPromise;
}

function docxSafeName(value){
  return String(value||'avaliacao')
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-zA-Z0-9._-]+/g,'_')
    .replace(/^_+|_+$/g,'')||'avaliacao';
}

function downloadAdelitaBlob(blob,filename){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
}

async function exportEditableDocx(){
  if(!state?.exam?.length){
    alert('Gere ou selecione uma prova antes de exportar o DOCX.');
    return;
  }

  const d=await loadAdelitaDocx();
  const {Document,Paragraph,TextRun,Header,Packer,AlignmentType}=d;
  const h=headerData();
  const children=[];
  const baseSize=22; // 11 pt: propositalmente simples para edição fina no Word.

  function run(text,{bold=false,italics=false,size=baseSize}={}){
    return new TextRun({text:String(text||''),bold,italics,size,font:'Arial'});
  }

  state.exam.forEach((q,i)=>{
    const prefix=`${i+1}. (${bancaAno(q)}) `;
    children.push(new Paragraph({
      children:[run(prefix,{bold:true}),run(cleanText(q.t))],
      spacing:{before:i===0?0:120,after:70,line:276},
      widowControl:true
    }));

    if(q.s){
      children.push(new Paragraph({
        children:[run(cleanText(q.s),{italics:true,size:19})],
        indent:{left:140},
        spacing:{after:80,line:240},
        widowControl:true
      }));
    }

    (q.o||[]).forEach(o=>{
      children.push(new Paragraph({
        children:[run(`${o.l}) `,{bold:true}),run(cleanText(o.t))],
        spacing:{after:45,line:276},
        widowControl:true,
        keepLines:true
      }));
    });
  });

  const headerLines=[
    new Paragraph({
      alignment:AlignmentType.CENTER,
      children:[run(h.title||'AVALIAÇÃO',{bold:true,size:24})],
      spacing:{after:30}
    }),
    new Paragraph({
      alignment:AlignmentType.CENTER,
      children:[run([h.component,h.className,formatDate(h.date)].filter(Boolean).join(' · '),{size:18})],
      spacing:{after:60}
    })
  ];

  const doc=new Document({
    sections:[{
      properties:{
        page:{margin:{top:720,right:720,bottom:720,left:720,header:360,footer:360}},
        column:{count:2,space:360,equalWidth:true,separate:true}
      },
      headers:{default:new Header({children:headerLines})},
      children
    }]
  });

  const blob=await Packer.toBlob(doc);
  const parts=[h.title,h.className,'editavel'].filter(Boolean).map(docxSafeName);
  downloadAdelitaBlob(blob,`${parts.join('_')||'avaliacao_editavel'}.docx`);
}

function installDocxExportButton(){
  if(document.getElementById('docxExportBtn'))return;
  const buttons=[...document.querySelectorAll('button')];
  const anchor=buttons.find(b=>/(baixar|gerar|exportar).*(pdf)|pdf.*(prova|avalia)/i.test((b.textContent||'').trim()))
    || buttons.find(b=>/pdf/i.test((b.textContent||'').trim()));
  if(!anchor)return;

  const btn=document.createElement('button');
  btn.id='docxExportBtn';
  btn.type='button';
  btn.className=anchor.className;
  btn.textContent='DOCX editável';
  btn.title='Exportar a prova atual para Word com formatação mínima e editável';
  if(!btn.className)btn.style.cssText='margin-left:8px;padding:9px 12px;border:1px solid #bbb;border-radius:8px;background:#fff;cursor:pointer';
  btn.addEventListener('click',async()=>{
    const old=btn.textContent;
    btn.disabled=true;btn.textContent='Gerando DOCX…';
    try{await exportEditableDocx()}
    catch(err){console.error(err);alert('Não consegui gerar o DOCX. Verifique sua conexão e tente novamente.')}
    finally{btn.disabled=false;btn.textContent=old}
  });
  anchor.insertAdjacentElement('afterend',btn);
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(installDocxExportButton,0));
else setTimeout(installDocxExportButton,0);
'''

    outer_end = text.rfind('</script></body></html>')
    if outer_end == -1:
        raise SystemExit('v0.9: fechamento do script principal não encontrado')
    text = text[:outer_end] + js + text[outer_end:]

text = text.replace('Adelita v0.8</title>', 'Adelita v0.9</title>')
text = text.replace('para a Profa. Adelita · v0.8</small>', 'para a Profa. Adelita · v0.9</small>')

if marker not in text:
    raise SystemExit('v0.9: exportador DOCX não foi inserido')
if 'exportEditableDocx' not in text or 'docxExportBtn' not in text:
    raise SystemExit('v0.9: função ou botão DOCX ausente')

path.write_text(text, encoding='utf-8')
print('Hotfix v0.9 aplicado: exportação DOCX editável em duas colunas')
