from pathlib import Path

site=Path('_site')
index=site/'index.html'
history=site/'history_v11.js'
text=index.read_text(encoding='utf-8')
h=history.read_text(encoding='utf-8')

# O gabarito simples da v1.3 usava uma largura total ligeiramente maior que a
# área útil de uma página A4 e só fixava largura nas células do cabeçalho.
# O Word podia redistribuir as colunas e produzir a tabela visualmente comprimida.
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
if old not in h:
    raise SystemExit('v1.3.1: tabela antiga do gabarito não encontrada')
h=h.replace(old,new,1)

# Deixa o papel explicitamente A4 e a tabela sempre dentro da área útil.
old_page="properties:{page:{margin:{top:820,right:820,bottom:820,left:820,header:320,footer:360}}}"
new_page="properties:{page:{size:{width:11906,height:16838},margin:{top:820,right:820,bottom:820,left:820,header:320,footer:360}}}"
if old_page not in h:
    raise SystemExit('v1.3.1: propriedades da página do gabarito não encontradas')
h=h.replace(old_page,new_page,1)

text=text.replace('Adelita v1.3</title>','Adelita v1.3.1</title>')
text=text.replace('para a Profa. Adelita · v1.3</small>','para a Profa. Adelita · v1.3.1</small>')

history.write_text(h,encoding='utf-8')
index.write_text(text,encoding='utf-8')

if 'columnWidths:widths' not in h or 'width:{size:10200' not in h:
    raise SystemExit('v1.3.1: nova tabela não foi aplicada')
print('Hotfix v1.3.1 aplicado: tabela do gabarito alinhada e A4 explícito')
