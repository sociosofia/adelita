from pathlib import Path

site=Path('_site')
index=site/'index.html'
history=site/'history_v11.js'
builder=site/'builder_v1.js'
sw=site/'sw.js'
text=index.read_text(encoding='utf-8')
h=history.read_text(encoding='utf-8')
b=builder.read_text(encoding='utf-8')

# Tabela do gabarito simples: A4, larguras estáveis e margens internas.
old="""      const border={style:BorderStyle.SINGLE,size:4,color:'D8DDE0'};
      const borders={top:border,bottom:border,left:border,right:border,insideHorizontal:border,insideVertical:border};
      const rows=[new TableRow({children:[
        new TableCell({width:{size:1300,type:WidthType.DXA},borders,children:[new Paragraph({children:[run('Questão',{bold:true})]})]}),
        new TableCell({width:{size:1400,type:WidthType.DXA},borders,children:[new Paragraph({children:[run('Gabarito',{bold:true})]})]}),
        new TableCell({width:{size:7760,type:WidthType.DXA},borders,children:[new Paragraph({children:[run('Referência',{bold:true})]})]})
      ]})];
      qs.forEach((q,i)=>{
        const opt=questionCorrectOption(q);const ans=opt?String(opt.l):'—';
        rows.push(new TableRow({children:[
          new TableCell({borders,children:[new Paragraph({children:[run(String(i+1),{bold:true})]})]}),
          new TableCell({borders,children:[new Paragraph({children:[run(ans,{bold:true})]})]}),
          new TableCell({borders,children:[new Paragraph({children:[run(bancaAno(q),{size:18})]})]})
        ]}));
      });
      children.push(new Table({width:{size:10460,type:WidthType.DXA},layout:TableLayoutType.FIXED,borders,rows}));
"""
new="""      const border={style:BorderStyle.SINGLE,size:3,color:'D8DDE0'};
      const borders={top:border,bottom:border,left:border,right:border,insideHorizontal:border,insideVertical:border};
      const cellMargins={top:85,bottom:85,left:110,right:110};
      const widths=[1450,1550,7200];
      const cell=(content,width,{center=false}={})=>new TableCell({
        width:{size:width,type:WidthType.DXA},borders,margins:cellMargins,
        verticalAlign:'center',
        children:[new Paragraph({alignment:center?AlignmentType.CENTER:AlignmentType.LEFT,children:content,spacing:{before:0,after:0,line:240}})]
      });
      const rows=[new TableRow({tableHeader:true,children:[
        cell([run('Questão',{bold:true,size:18})],widths[0],{center:true}),
        cell([run('Gabarito',{bold:true,size:18})],widths[1],{center:true}),
        cell([run('Referência',{bold:true,size:18})],widths[2])
      ]})];
      qs.forEach((q,i)=>{
        const opt=questionCorrectOption(q);const ans=opt?String(opt.l):'—';
        rows.push(new TableRow({cantSplit:true,children:[
          cell([run(String(i+1),{bold:true,size:18})],widths[0],{center:true}),
          cell([run(ans,{bold:true,size:18})],widths[1],{center:true}),
          cell([run(bancaAno(q),{size:18})],widths[2])
        ]}));
      });
      children.push(new Table({
        width:{size:10200,type:WidthType.DXA},columnWidths:widths,
        layout:TableLayoutType.FIXED,borders,rows
      }));
"""
if old not in h: raise SystemExit('v1.4: tabela antiga do gabarito não encontrada')
h=h.replace(old,new,1)

old_page="properties:{page:{margin:{top:820,right:820,bottom:820,left:820,header:320,footer:360}}}"
new_page="properties:{page:{size:{width:11906,height:16838},margin:{top:820,right:820,bottom:820,left:820,header:320,footer:360}}}"
if old_page not in h: raise SystemExit('v1.4: propriedades da página do gabarito não encontradas')
h=h.replace(old_page,new_page,1)

# 20 resultados por lote.
b=b.replace('let builderShown=60;','let builderShown=20;',1)
b=b.replace('builderShown=60;builderExpandedResults.clear()','builderShown=20;builderExpandedResults.clear()')
b=b.replace('builderShown=60;builderRenderResults()','builderShown=20;builderRenderResults()')
b=b.replace('builderShown+=60;builderRenderResults()','builderShown+=20;builderRenderResults()')
b=b.replace('Math.min(60,pool.length-builderShown)','Math.min(20,pool.length-builderShown)')
b=b.replace("dataCard.insertAdjacentHTML('afterbegin','<div class=\"builder-step-label\">Dados da avaliação</div>');", "dataCard.insertAdjacentHTML('afterbegin','<div class=\"builder-step-label\">3 · Painel da avaliação</div>');")
b=b.replace("firstCard.insertAdjacentHTML('afterbegin','<div class=\"builder-step-label\">Banco de questões</div>')", "firstCard.insertAdjacentHTML('afterbegin','<div class=\"builder-step-label\">1 · Escolha a disciplina</div>')")

# Separa os resultados em seu próprio cartão e põe o painel antes deles.
old_ui="""  const previewCard=$('#previewCard');
  if(previewCard){const h3=previewCard.querySelector('h3');if(h3)h3.textContent='Minha avaliação';const tip=previewCard.querySelector('.compact-tip');if(tip)tip.textContent='As questões permanecem na ordem em que você as adiciona. Use ↑ e ↓ para reorganizar; nada é sorteado novamente.'}
"""
new_ui="""  const previewCard=$('#previewCard');
  if(previewCard){const h3=previewCard.querySelector('h3');if(h3)h3.textContent='Minha avaliação';const tip=previewCard.querySelector('.compact-tip');if(tip)tip.textContent='As questões permanecem na ordem em que você as adiciona. Use ↑ e ↓ para reorganizar; nada é sorteado novamente.'}
  const filterCard=$('#builderCard'),results=$('#builderResults'),more=$('#builderMore'),toolbar=$('#toolbar');
  if(filterCard&&!filterCard.querySelector('.builder-filter-step'))filterCard.insertAdjacentHTML('afterbegin','<div class=\"builder-step-label builder-filter-step\">2 · Refine a busca</div>');
  let questionCard=$('#builderQuestionsCard');
  if(filterCard&&results&&!questionCard){
    questionCard=document.createElement('div');questionCard.className='card';questionCard.id='builderQuestionsCard';
    questionCard.innerHTML='<div class=\"preview-head builder-head\"><div><div class=\"builder-step-label\">4 · Questões disponíveis</div><h3>Escolha as questões</h3><div class=\"muted\">20 questões por vez. Ao adicionar, elas entram na avaliação acima na ordem escolhida.</div></div></div>';
    questionCard.appendChild(results);if(more?.parentElement)questionCard.appendChild(more.parentElement);
  }
"""
if old_ui not in b: raise SystemExit('v1.4: ponto de separação da lista não encontrado')
b=b.replace(old_ui,new_ui,1)

old_end="""  if(previewActions&&!$('#newAssessmentBtn')){
    const btn=document.createElement('button');btn.className='btn';btn.id='newAssessmentBtn';btn.textContent='Nova avaliação';previewActions.insertBefore(btn,previewActions.firstChild);
    btn.onclick=()=>{
      if(state.exam.length&&!confirm('Começar uma nova avaliação e limpar a seleção atual?'))return;
      state.exam=[];builderLastRemoved=null;builderExpandedSelected.clear();builderRenderSelected();builderRenderResults();
    };
  }
}
"""
new_end="""  if(previewActions&&!$('#newAssessmentBtn')){
    const btn=document.createElement('button');btn.className='btn';btn.id='newAssessmentBtn';btn.textContent='Nova avaliação';previewActions.insertBefore(btn,previewActions.firstChild);
    btn.onclick=()=>{
      if(state.exam.length&&!confirm('Começar uma nova avaliação e limpar a seleção atual?'))return;
      state.exam=[];builderLastRemoved=null;builderExpandedSelected.clear();builderRenderSelected();builderRenderResults();
    };
  }
  // Hierarquia v1.4: disciplina → filtros → painel da avaliação → questões disponíveis.
  if(firstCard&&filterCard)firstCard.insertAdjacentElement('afterend',filterCard);
  if(filterCard&&dataCard)filterCard.insertAdjacentElement('afterend',dataCard);
  if(dataCard&&previewCard)dataCard.insertAdjacentElement('afterend',previewCard);
  if(previewCard&&toolbar)previewCard.insertAdjacentElement('afterend',toolbar);
  if(toolbar&&questionCard)toolbar.insertAdjacentElement('afterend',questionCard);
}
"""
if old_end not in b: raise SystemExit('v1.4: final do painel não encontrado')
b=b.replace(old_end,new_end,1)

for oldv in ('v1.3','v1.3.1','v1.3.2'):
    text=text.replace(f'Adelita {oldv}</title>','Adelita v1.4</title>')
    text=text.replace(f'para a Profa. Adelita · {oldv}</small>','para a Profa. Adelita · v1.4</small>')

# No artefato publicado, força nova chave do cache.
if sw.exists():
    s=sw.read_text(encoding='utf-8')
    s=s.replace('adelita-pwa-v1.3.2','adelita-pwa-v1.4').replace('adelita-pwa-v1.3.1','adelita-pwa-v1.4').replace('adelita-pwa-v1.3','adelita-pwa-v1.4')
    sw.write_text(s,encoding='utf-8')

history.write_text(h,encoding='utf-8')
builder.write_text(b,encoding='utf-8')
index.write_text(text,encoding='utf-8')

if 'columnWidths:widths' not in h or 'let builderShown=20;' not in b or 'builderQuestionsCard' not in b:
    raise SystemExit('v1.4: validação final falhou')
print('Hotfix v1.4 aplicado: tabela estável, 20 por lote e painel acima das questões')
