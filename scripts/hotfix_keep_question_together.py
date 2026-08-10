from pathlib import Path
import re

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

marker = '// BLOCK-PAGINATION-v0.8'

replacement = r'''  // BLOCK-PAGINATION-v0.8
  // Cada questão passa a ter dois blocos lógicos internos:
  // q.N.e = enunciado + suporte; q.N.a = alternativas.
  function measureStemBlock(q,i){
    doc.setFontSize(p.fontSize);doc.setFont('helvetica','bold');
    const prefix=`${i+1}. (${bancaAno(q)}) `,pw=doc.getTextWidth(prefix);
    doc.setFont('helvetica','normal');
    const wrapped=wrapFirst(doc,cleanText(q.t),Math.max(18,colW-pw),colW);
    const sourceLines=q.s?wrapLines(doc,cleanText(q.s),colW-1.4):[];
    let height=((wrapped.first?1:0)+wrapped.rest.length)*p.lead;
    if(sourceLines.length)height+=p.sourceGap+sourceLines.length*p.lead+p.sourceGap;
    return{id:`q.${i+1}.e`,prefix,pw,wrapped,sourceLines,height};
  }

  function measureOptionsBlock(q,i){
    const options=q.o.map(o=>{
      doc.setFontSize(p.fontSize);doc.setFont('helvetica','bold');
      const letter=`${o.l}) `,lw=doc.getTextWidth(letter);
      doc.setFont('helvetica','normal');
      const wr=wrapFirst(doc,cleanText(o.t),Math.max(15,colW-lw),colW);
      const lines=(wr.first?1:0)+wr.rest.length;
      return{letter,lw,wr,height:lines*p.lead+p.altGap};
    });
    return{id:`q.${i+1}.a`,options,height:options.reduce((sum,o)=>sum+o.height,0)};
  }

  function nextColumnCapacity(){
    const nextTop=col===0?pageTop():topNext;
    return bottom-nextTop;
  }

  function addSoftGap(gap){
    y=Math.min(bottom,y+gap);
  }

  function placeStemBlock(block){
    ensureLine();
    let x=xcol();
    doc.setFont('helvetica','bold');doc.setFontSize(p.fontSize);doc.text(block.prefix,x,y);
    doc.setFont('helvetica','normal');
    if(block.wrapped.first)doc.text(block.wrapped.first,x+block.pw,y);
    y+=p.lead;

    drawLines(block.wrapped.rest);

    if(block.sourceLines.length){
      if(y+p.sourceGap+p.lead>bottom)nextCol();
      else y+=p.sourceGap;
      drawLines(block.sourceLines,p.lead,p.fontSize,false,1.4);
      addSoftGap(p.sourceGap);
    }
  }

  function placeOption(opt){
    const cleanCap=nextColumnCapacity();
    if(y+opt.height>bottom&&opt.height<=cleanCap)nextCol();

    ensureLine();
    let x=xcol();
    doc.setFont('helvetica','bold');doc.setFontSize(p.fontSize);doc.text(opt.letter,x,y);
    doc.setFont('helvetica','normal');
    if(opt.wr.first)doc.text(opt.wr.first,x+opt.lw,y);
    y+=p.lead;

    drawLines(opt.wr.rest);
    addSoftGap(p.altGap);
  }

  function placeOptionsBlock(block){
    for(const opt of block.options)placeOption(opt);
  }

  function paginateQuestion(q,i){
    const stem=measureStemBlock(q,i);
    const options=measureOptionsBlock(q,i);
    const fullHeight=stem.height+p.stemGap+options.height+p.questionGap;
    let remaining=bottom-y;
    let cleanCap=nextColumnCapacity();

    // 1) Preferência máxima: q.N.e + q.N.a juntos.
    if(fullHeight<=remaining){
      placeStemBlock(stem);
      addSoftGap(p.stemGap);
      placeOptionsBlock(options);
      addSoftGap(p.questionGap);
      return;
    }

    // 2) Se a questão inteira cabe na próxima coluna limpa, move tudo junto.
    if(fullHeight<=cleanCap){
      nextCol();
      placeStemBlock(stem);
      addSoftGap(p.stemGap);
      placeOptionsBlock(options);
      addSoftGap(p.questionGap);
      return;
    }

    // 3) A questão não cabe inteira em uma coluna: preserva q.N.e como bloco
    // quando possível. Só divide o enunciado se ele próprio for maior que
    // uma coluna; não deixa menos de três linhas úteis no rodapé.
    remaining=bottom-y;
    cleanCap=nextColumnCapacity();
    const minUsefulStem=Math.min(stem.height,p.lead*3);
    if(stem.height>remaining){
      if(stem.height<=cleanCap||remaining<minUsefulStem)nextCol();
    }else if(remaining<minUsefulStem){
      nextCol();
    }

    placeStemBlock(stem);
    addSoftGap(p.stemGap);

    // 4) q.N.a pode se desligar de q.N.e. Mantém o bloco inteiro na próxima
    // coluna se couber; quando o próprio bloco é alto demais, quebra somente
    // entre alternativas completas sempre que possível.
    remaining=bottom-y;
    cleanCap=nextColumnCapacity();
    if(options.height>remaining&&options.height<=cleanCap)nextCol();
    placeOptionsBlock(options);

    addSoftGap(p.questionGap);
  }

  state.exam.forEach((q,i)=>paginateQuestion(q,i));'''

pattern = r'''  state\.exam\.forEach\(\(q,i\)=>\{\n    // Evita começar uma questão no rodapé com espaço insuficiente para leitura\..*?\n  \}\);'''
text, n = re.subn(pattern, replacement, text, count=1, flags=re.S)
if n != 1:
    raise SystemExit(f'v0.8: não consegui substituir o paginador linear ({n})')

text = text.replace('Adelita v0.7</title>', 'Adelita v0.8</title>')
text = text.replace('para a Profa. Adelita · v0.7</small>', 'para a Profa. Adelita · v0.8</small>')

if marker not in text:
    raise SystemExit('v0.8: paginador em blocos não foi inserido')
if 'q.${i+1}.e' not in text or 'q.${i+1}.a' not in text:
    raise SystemExit('v0.8: identificadores internos e/a ausentes')

path.write_text(text, encoding='utf-8')
print('Hotfix v0.8 aplicado: enunciado e alternativas paginados como blocos independentes')
