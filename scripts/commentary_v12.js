// ADELITA-COMMENTARY-IMPORT-v1.2
(() => {
  const DB_NAME='adelita_commentary_v12';
  const DB_VERSION=1;
  const STORE='comments';
  const HISTORY_DB='adelita_history_v11';
  const HISTORY_STORE='assessments';
  let dbPromise=null;
  let commentaryMap=new Map();

  const sidOf=q=>String(q?.sid??q?.question_id??q?.id??'')
    .replace(/^(SOC|FIL|HIS|GEO)-/i,'')
    .trim();

  function htmlText(value){
    if(value==null)return'';
    const raw=String(value);
    if(!raw.trim())return'';
    const div=document.createElement('div');
    div.innerHTML=raw
      .replace(/<br\s*\/?\s*>/gi,'\n')
      .replace(/<\/p\s*>/gi,'\n')
      .replace(/<\/li\s*>/gi,'\n');
    return (div.textContent||div.innerText||'')
      .replace(/\u00a0/g,' ')
      .replace(/[\t ]+\n/g,'\n')
      .replace(/\n[\t ]+/g,'\n')
      .replace(/\n{3,}/g,'\n\n')
      .replace(/[ \t]{2,}/g,' ')
      .trim();
  }

  function usefulGeneral(text){
    const t=htmlText(text);
    if(!t)return'';
    if(/^GABARITO\s*:\s*ALTERNATIVA\s+[A-Z]\s*$/i.test(t))return'';
    return t;
  }

  function openDb(){
    if(dbPromise)return dbPromise;
    dbPromise=new Promise((resolve,reject)=>{
      const req=indexedDB.open(DB_NAME,DB_VERSION);
      req.onupgradeneeded=()=>{
        const db=req.result;
        if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'sid'});
      };
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Falha ao abrir comentários locais'));
    });
    return dbPromise;
  }

  async function putMany(entries){
    if(!entries.length)return 0;
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const tx=db.transaction(STORE,'readwrite');
      const store=tx.objectStore(STORE);
      entries.forEach(e=>store.put(e));
      tx.oncomplete=()=>resolve(entries.length);
      tx.onerror=()=>reject(tx.error||new Error('Falha ao salvar comentários'));
    });
  }

  async function loadAll(){
    const db=await openDb();
    return new Promise((resolve,reject)=>{
      const req=db.transaction(STORE,'readonly').objectStore(STORE).getAll();
      req.onsuccess=()=>resolve(req.result||[]);
      req.onerror=()=>reject(req.error||new Error('Falha ao ler comentários'));
    });
  }

  function questionArray(data){
    if(Array.isArray(data))return data;
    if(!data||typeof data!=='object')return[];
    for(const key of ['questions','questoes','items','results']){
      if(Array.isArray(data[key]))return data[key];
    }
    if(Array.isArray(data?.data?.questions))return data.data.questions;
    if(data?.response?.data?.question_id||data?.response?.data?.id)return[data.response.data];
    if(data?.data?.question_id||data?.data?.id)return[data.data];
    if(data.question_id||data.id)return[data];
    return[];
  }

  function normalizeEntry(q,sourceName=''){
    const sid=sidOf(q);if(!sid)return null;
    const sd=q.solution_data&&typeof q.solution_data==='object'?q.solution_data:null;
    const rawAlts=(Array.isArray(sd?.alternatives)&&sd.alternatives.length?sd.alternatives:q.alternatives)||[];
    const alternatives={};
    rawAlts.forEach((a,i)=>{
      if(!a||typeof a!=='object')return;
      const letter=String(a.letter??a.l??String.fromCharCode(65+i)).trim().toUpperCase();
      const text=htmlText(a.solution_html??a.commentary??a.comentario??a.feedback??'');
      if(letter&&text)alternatives[letter]=text;
    });
    const general=usefulGeneral(sd?.solution_html??q.solution_html??q.commentary??q.comentario??'');
    if(!general&&!Object.keys(alternatives).length)return null;
    return{
      sid,
      general,
      alternatives,
      answer:String(sd?.gabarito??q.gabarito??q.answer??'').trim().toUpperCase(),
      source:sourceName||'',
      importedAt:Date.now()
    };
  }

  function decorateQuestion(q){
    if(!q||typeof q!=='object')return false;
    const entry=commentaryMap.get(sidOf(q));if(!entry)return false;
    if(entry.general)q.commentary=entry.general;
    (q.o||[]).forEach((o,i)=>{
      const letter=String(o?.l??String.fromCharCode(65+i)).trim().toUpperCase();
      const text=entry.alternatives?.[letter];
      if(text)o.commentary=text;
    });
    q.__adelita_commentary_v12=true;
    return true;
  }

  function decorateLoaded(){
    let changed=0;
    Object.values(window.ADELITA_BANKS||{}).forEach(bank=>{
      if(Array.isArray(bank))bank.forEach(q=>{if(decorateQuestion(q))changed++});
    });
    (state?.exam||[]).forEach(q=>decorateQuestion(q));
    (state?.questions||[]).forEach(q=>decorateQuestion(q));
    return changed;
  }

  async function decorateHistory(){
    if(!('indexedDB'in window)||!commentaryMap.size)return;
    await new Promise(resolve=>{
      const req=indexedDB.open(HISTORY_DB);
      req.onerror=()=>resolve();
      req.onupgradeneeded=()=>{try{req.transaction.abort()}catch(_){}resolve()};
      req.onsuccess=()=>{
        const db=req.result;
        if(!db.objectStoreNames.contains(HISTORY_STORE)){db.close();resolve();return}
        const read=db.transaction(HISTORY_STORE,'readonly').objectStore(HISTORY_STORE).getAll();
        read.onerror=()=>{db.close();resolve()};
        read.onsuccess=()=>{
          const records=read.result||[];
          if(!records.length){db.close();resolve();return}
          const tx=db.transaction(HISTORY_STORE,'readwrite');
          const store=tx.objectStore(HISTORY_STORE);
          records.forEach(r=>{
            let changed=false;
            (r.questions||[]).forEach(q=>{if(decorateQuestion(q))changed=true});
            if(changed)store.put(r);
          });
          tx.oncomplete=()=>{db.close();resolve()};
          tx.onerror=()=>{db.close();resolve()};
        };
      };
    });
  }

  function updateImportButton(){
    const btn=document.getElementById('commentaryImportBtn');if(!btn)return;
    btn.textContent=commentaryMap.size?`Comentários locais · ${commentaryMap.size.toLocaleString('pt-BR')}`:'Importar comentários';
    btn.title=commentaryMap.size
      ?`${commentaryMap.size.toLocaleString('pt-BR')} questões com comentários enriquecidos armazenadas neste aparelho. Clique para importar/atualizar outros JSONs.`
      :'Importar JSON enriquecido com comentários. Os dados ficam somente neste aparelho.';
  }

  async function importFiles(files){
    const entries=[];let seen=0;
    for(const file of files){
      const text=await file.text();
      let data;
      try{data=JSON.parse(text)}catch(_){throw new Error(`Não consegui ler ${file.name} como JSON.`)}
      const qs=questionArray(data);seen+=qs.length;
      qs.forEach(q=>{const e=normalizeEntry(q,file.name);if(e)entries.push(e)});
    }
    const uniq=new Map();entries.forEach(e=>uniq.set(e.sid,e));
    await putMany([...uniq.values()]);
    const all=await loadAll();commentaryMap=new Map(all.map(e=>[String(e.sid),e]));
    decorateLoaded();await decorateHistory();updateImportButton();
    try{builderRenderSelected?.();builderSaveDraft?.()}catch(_){ }
    const dlg=document.getElementById('histDlg');if(dlg?.open)dlg.close();
    alert(`${uniq.size.toLocaleString('pt-BR')} questões com comentários foram importadas/atualizadas neste aparelho${seen?` (de ${seen.toLocaleString('pt-BR')} lidas)`:''}.\n\nA Adelita usará esses dados no gabarito comentado sempre que a questão correspondente estiver na avaliação.`);
  }

  function installImporter(){
    if(document.getElementById('commentaryImportBtn'))return;
    const toolbar=document.getElementById('toolbar');if(!toolbar)return;
    const input=document.createElement('input');
    input.type='file';input.accept='.json,application/json';input.multiple=true;input.hidden=true;input.id='commentaryImportInput';
    input.addEventListener('change',async()=>{
      if(!input.files?.length)return;
      const btn=document.getElementById('commentaryImportBtn');const old=btn?.textContent;
      if(btn){btn.disabled=true;btn.textContent='Importando comentários…'}
      try{await importFiles([...input.files])}
      catch(err){console.error(err);alert(err?.message||'Não consegui importar os comentários.')}
      finally{input.value='';if(btn)btn.disabled=false;updateImportButton();if(!commentaryMap.size&&btn)btn.textContent=old||'Importar comentários'}
    });
    document.body.appendChild(input);
    const btn=document.createElement('button');btn.id='commentaryImportBtn';btn.className='btn';btn.type='button';btn.onclick=()=>input.click();
    const anchor=document.getElementById('commentedKeyDocxBtn')||document.getElementById('keyDocxBtn')||document.getElementById('docxExportBtn');
    anchor?.insertAdjacentElement('afterend',btn);if(!anchor)toolbar.appendChild(btn);
    updateImportButton();
  }

  function patchBankLoader(){
    if(typeof loadScript!=='function'||loadScript.__commentaryV12)return;
    const base=loadScript;
    const wrapped=async function(d){const r=await base(d);const bank=window.ADELITA_BANKS?.[d];if(Array.isArray(bank))bank.forEach(q=>decorateQuestion(q));return r};
    wrapped.__commentaryV12=true;loadScript=wrapped;
  }

  async function init(){
    try{
      const all=await loadAll();commentaryMap=new Map(all.map(e=>[String(e.sid),e]));
      decorateLoaded();await decorateHistory();
    }catch(err){console.warn('Comentários locais indisponíveis',err)}
    patchBankLoader();installImporter();updateImportButton();
    try{builderRenderSelected?.()}catch(_){ }
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(init,260));
  else setTimeout(init,260);
})();
