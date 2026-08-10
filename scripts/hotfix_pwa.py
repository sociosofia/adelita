from pathlib import Path

path = Path('_site/index.html')
text = path.read_text(encoding='utf-8')

# O bloco de instalação do PWA foi injetado acidentalmente dentro do template
# HTML usado pela função de impressão. Em HTML, um </script> literal encerra o
# script principal mesmo quando aparece dentro de uma template string JS.
start_marker = "<script>window.onload=()=>setTimeout(()=>window.print(),200)<\\/script>\n<script>\n(function(){"
end_marker = "</script>\n</body></html>`);w.document.close();"

start = text.find(start_marker)
if start != -1:
    end = text.find(end_marker, start)
    if end == -1:
        raise SystemExit('Hotfix: fim do bloco vazado não encontrado')
    replacement = "<script>window.onload=()=>setTimeout(()=>window.print(),200)<\\/script></body></html>`);w.document.close();"
    text = text[:start] + replacement + text[end + len(end_marker):]

marker = '// PWA-HOTFIX-v0.5.1'
if marker not in text:
    pwa_js = r'''
// PWA-HOTFIX-v0.5.1
let deferredPrompt=null;
const installButton=document.getElementById('installBtn');
window.addEventListener('beforeinstallprompt',e=>{
  e.preventDefault();
  deferredPrompt=e;
  if(installButton) installButton.style.display='inline-flex';
});
if(installButton) installButton.addEventListener('click',async()=>{
  if(!deferredPrompt)return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt=null;
  installButton.style.display='none';
});
window.addEventListener('appinstalled',()=>{if(installButton)installButton.style.display='none'});
if('serviceWorker' in navigator){
  window.addEventListener('load',async()=>{
    try{
      const reg=await navigator.serviceWorker.register('./sw.js');
      reg.update().catch(()=>{});
    }catch(err){console.warn('Service worker não registrado',err)}
  });
}
'''
    outer_end = text.rfind('</script></body></html>')
    if outer_end == -1:
        raise SystemExit('Hotfix: fechamento do script principal não encontrado')
    text = text[:outer_end] + pwa_js + text[outer_end:]

text = text.replace('Adelita v0.5</title>', 'Adelita v0.5.1</title>')
text = text.replace('para a Profa. Adelita · v0.5</small>', 'para a Profa. Adelita · v0.5.1</small>')

# Guardas simples para impedir que o mesmo vazamento volte a ser publicado.
if start_marker in text:
    raise SystemExit('Hotfix falhou: bloco PWA ainda está dentro do template de impressão')
if marker not in text:
    raise SystemExit('Hotfix falhou: registro do PWA não foi inserido no script principal')

path.write_text(text, encoding='utf-8')
print('Hotfix PWA v0.5.1 aplicado com sucesso')
