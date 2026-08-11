from pathlib import Path

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

marker = '// DOCX-EXPORT-v1.0.1'

if marker not in text:
    js = r'''

// DOCX-EXPORT-v1.0.1
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

function docxGenerationStamp(){
  const now=new Date();
  const pad=n=>String(n).padStart(2,'0');
  return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
}

function downloadAdelitaBlob(blob,filename){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;a.download=filename;
  document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),3000);
}

async function fetchDocxAsset(url){
  try{
    const r=await fetch(url);
    if(!r.ok)return null;
    return await r.arrayBuffer();
  }catch(_){return null}
}

async function exportEditableDocx(){
  if(!state?.exam?.length){
    alert('Gere ou selecione uma prova antes de exportar o DOCX.');
    return;
  }

  const d=await loadAdelitaDocx();
  const {
    Document,Paragraph,TextRun,Header,Packer,AlignmentType,
    Table,TableRow,TableCell,ImageRun,WidthType,BorderStyle,
    VerticalAlign,TableLayoutType
  }=d;
  const h=headerData();
  const professorName=String(h.professor||h.teacher||h.prof||'Profa. Adelita Xavier');
  const children=[];
  const baseSize=22; // 11 pt: simples para edição fina no Word.

  function run(text,{bold=false,italics=false,size=baseSize,color='000000'}={}){
    return new TextRun({text:String(text||''),bold,italics,size,color,font:'Arial'});
  }

  // Respiro exclusivo da primeira página entre identificação e questão 1.
  children.push(new Paragraph({children:[run('')],spacing:{before:0,after:150}}));

  state.exam.forEach((q,i)=>{
    const prefix=`${i+1}. (${bancaAno(q)}) `;
    children.push(new Paragraph({
      children:[run(prefix,{bold:true}),run(cleanText(q.t))],
      spacing:{before:i===0?0:120,after:70,line:276},
      widowControl:true
    }));

    if(q.s){
      children.push(new Paragraph({
        children:[run(cleanText(q.s),{italics:true,size:19,color:'444444'})],
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

  const [etecLogo,cpsLogo]=await Promise.all([
    fetchDocxAsset('./assets/logo_etec_bayeux.png'),
    fetchDocxAsset('./assets/logo_cps.png')
  ]);

  const none={style:BorderStyle.NONE,size:0,color:'FFFFFF'};
  const noBorders={top:none,bottom:none,left:none,right:none,insideHorizontal:none,insideVertical:none};
  const headerWidth=10466;
  const colWidths=[2150,6166,2150];

  function logoParagraph(buffer,side){
    const items=[];
    if(buffer){
      items.push(new ImageRun({
        type:'png',
        data:buffer,
        transformation:side==='left'?{width:72,height:29}:{width:76,height:30},
        altText:{
          title:side==='left'?'ETEC':'Centro Paula Souza',
          description:side==='left'?'Logotipo ETEC':'Logotipo Centro Paula Souza',
          name:side==='left'?'logo-etec':'logo-cps'
        }
      }));
    }else{
      items.push(run(side==='left'?'ETEC':'CPS',{bold:true,size:18,color:'666666'}));
    }
    return new Paragraph({
      alignment:side==='left'?AlignmentType.LEFT:AlignmentType.RIGHT,
      children:items,
      spacing:{before:0,after:0}
    });
  }

  const titleCell=new TableCell({
    width:{size:colWidths[1],type:WidthType.DXA},
    verticalAlign:VerticalAlign.CENTER,
    borders:noBorders,
    margins:{top:0,bottom:0,left:80,right:80},
    children:[
      new Paragraph({
        alignment:AlignmentType.CENTER,
        children:[run(h.title||'AVALIAÇÃO',{bold:true,size:24})],
        spacing:{before:0,after:18}
      }),
      new Paragraph({
        alignment:AlignmentType.CENTER,
        children:[run(professorName,{bold:true,size:18,color:'333333'})],
        spacing:{before:0,after:10}
      }),
      new Paragraph({
        alignment:AlignmentType.CENTER,
        children:[run([h.component,h.className,formatDate(h.date)].filter(Boolean).join(' · '),{size:17,color:'555555'})],
        spacing:{before:0,after:0}
      })
    ]
  });

  const brandingTable=new Table({
    width:{size:headerWidth,type:WidthType.DXA},
    columnWidths:colWidths,
    layout:TableLayoutType.FIXED,
    borders:noBorders,
    rows:[new TableRow({children:[
      new TableCell({
        width:{size:colWidths[0],type:WidthType.DXA},verticalAlign:VerticalAlign.CENTER,
        borders:noBorders,margins:{top:0,bottom:0,left:0,right:0},children:[logoParagraph(etecLogo,'left')]
      }),
      titleCell,
      new TableCell({
        width:{size:colWidths[2],type:WidthType.DXA},verticalAlign:VerticalAlign.CENTER,
        borders:noBorders,margins:{top:0,bottom:0,left:0,right:0},children:[logoParagraph(cpsLogo,'right')]
      })
    ]})]
  });

  const headerRule=new Paragraph({
    children:[run('')],
    spacing:{before:70,after:60},
    border:{bottom:{style:BorderStyle.SINGLE,size:4,color:'B7B7B7',space:1}}
  });

  const nameLine=new Paragraph({
    children:[
      run('Nome: ',{bold:true,size:19}),
      run('_______________________________________________',{size:19}),
      run('   Nº: ',{bold:true,size:19}),
      run('______',{size:19}),
      run(h.className?`   Turma: ${h.className}`:'',{bold:true,size:19})
    ],
    spacing:{before:35,after:55}
  });

  const firstHeader=new Header({children:[brandingTable,headerRule,nameLine]});

  const defaultHeader=new Header({children:[
    new Paragraph({
      alignment:AlignmentType.CENTER,
      children:[
        run(h.title||'AVALIAÇÃO',{bold:true,size:17,color:'333333'}),
        run(` · ${[h.component,h.className,formatDate(h.date)].filter(Boolean).join(' · ')}`,{size:16,color:'555555'})
      ],
      spacing:{before:0,after:0},
      border:{bottom:{style:BorderStyle.SINGLE,size:3,color:'D0D0D0',space:1}}
    })
  ]});

  const doc=new Document({
    sections:[{
      properties:{
        titlePage:true,
        page:{margin:{top:1040,right:720,bottom:720,left:720,header:220,footer:360}},
        column:{count:2,space:360,equalWidth:true,separate:true}
      },
      headers:{first:firstHeader,default:defaultHeader},
      children
    }]
  });

  const blob=await Packer.toBlob(doc);
  const parts=[h.title,h.className,docxGenerationStamp()].filter(Boolean).map(docxSafeName);
  downloadAdelitaBlob(blob,`${parts.join('_')||'avaliacao'}.docx`);
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
  btn.title='Exportar a prova atual para Word com cabeçalho e formatação leve, totalmente editável';
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
        raise SystemExit('v1.0.1: fechamento do script principal não encontrado')
    text = text[:outer_end] + js + text[outer_end:]

for old in ('0.8','0.9','0.9.1'):
    text = text.replace(f'Adelita v{old}</title>', 'Adelita v1.0</title>')
    text = text.replace(f'para a Profa. Adelita · v{old}</small>', 'para a Profa. Adelita · v1.0</small>')

if marker not in text:
    raise SystemExit('v1.0.1: exportador DOCX não foi inserido')
if 'exportEditableDocx' not in text or 'docxExportBtn' not in text:
    raise SystemExit('v1.0.1: função ou botão DOCX ausente')
if 'logo_etec_bayeux.png' not in text or 'logo_cps.png' not in text:
    raise SystemExit('v1.0.1: logos institucionais ausentes do exportador')
if 'Profa. Adelita Xavier' not in text or 'docxGenerationStamp' not in text:
    raise SystemExit('v1.0.1: professora padrão ou carimbo de geração ausente')

path.write_text(text, encoding='utf-8')
print('Hotfix v1.0.1 aplicado: cabeçalho refinado, professora padrão, respiro e nome único do DOCX')
