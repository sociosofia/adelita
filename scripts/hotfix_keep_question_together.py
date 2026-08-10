from pathlib import Path

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

marker = '// KEEP-QUESTION-TOGETHER-v0.7.1'

if marker not in text:
    needle = """  state.exam.forEach((q,i)=>{\n    // Evita começar uma questão no rodapé com espaço insuficiente para leitura.\n"""
    if needle not in text:
        raise SystemExit('v0.7.1: ponto de inserção da paginação não encontrado')

    replacement = r'''  // KEEP-QUESTION-TOGETHER-v0.7.1
  function measureQuestionHeight(q,i){
    doc.setFontSize(p.fontSize);doc.setFont('helvetica','bold');
    const prefix=`${i+1}. (${bancaAno(q)}) `,pw=doc.getTextWidth(prefix);
    doc.setFont('helvetica','normal');
    const stem=wrapFirst(doc,cleanText(q.t),Math.max(18,colW-pw),colW);
    let total=((stem.first?1:0)+stem.rest.length)*p.lead;

    if(q.s){
      total+=p.sourceGap;
      total+=wrapLines(doc,cleanText(q.s),colW-1.4).length*p.lead;
      total+=p.sourceGap;
    }

    total+=p.stemGap;
    for(const o of q.o){
      doc.setFont('helvetica','bold');doc.setFontSize(p.fontSize);
      const letter=`${o.l}) `,lw=doc.getTextWidth(letter);
      doc.setFont('helvetica','normal');
      const wr=wrapFirst(doc,cleanText(o.t),Math.max(15,colW-lw),colW);
      total+=((wr.first?1:0)+wr.rest.length)*p.lead+p.altGap;
    }
    total+=p.questionGap;
    return total;
  }

  state.exam.forEach((q,i)=>{
    // Se a questão inteira cabe em uma coluna limpa, não a quebra por falta
    // de espaço residual na coluna atual. Questões maiores que uma coluna
    // continuam podendo fluir normalmente.
    const questionH=measureQuestionHeight(q,i);
    const cleanTop=(col===0?pageTop():topNext);
    const cleanCapacity=bottom-cleanTop;
    const remaining=bottom-y;
    if(questionH<=cleanCapacity && questionH>remaining)nextCol();

    // Evita começar uma questão no rodapé com espaço insuficiente para leitura.
'''
    text = text.replace(needle, replacement, 1)

text = text.replace('Adelita v0.7</title>', 'Adelita v0.7.1</title>')
text = text.replace('para a Profa. Adelita · v0.7</small>', 'para a Profa. Adelita · v0.7.1</small>')

if marker not in text:
    raise SystemExit('v0.7.1: regra de questão inteira não foi inserida')

path.write_text(text, encoding='utf-8')
print('Hotfix v0.7.1 aplicado: questões que cabem inteiras permanecem na mesma coluna')
