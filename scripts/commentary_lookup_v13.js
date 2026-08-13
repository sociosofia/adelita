// ADELITA-COMMENTARY-LOOKUP-v1.4.1
(() => {
  const DB_NAME='adelita_commentary_remote_v141';
  const DB_VERSION=1, STORE='comments', memory=new Map();
  let dbPromise=null;

  // Questões-semente já validadas. O restante é consultado somente quando a professora pede.
  const STATIC={
    '4000331118':{sid:'4000331118',answer:'A',general:'A questão exige reconhecer a distinção feita por Foucault entre duas formas modernas de exercício do poder: uma voltada ao corpo individual e outra à regulação da população como conjunto biológico.',alternatives:{A:'Correta. O primeiro tipo corresponde ao poder disciplinar, que atua sobre os corpos individuais por meio de vigilância, normalização e controle; o segundo é o biopoder, que regula populações por meio de estatísticas, políticas de saúde e gestão da vida coletiva.',B:'Incorreta. “Dominação legal” é conceito associado a Weber, não a Foucault, e não corresponde ao primeiro tipo descrito.',C:'Incorreta. A alternativa é genérica e não utiliza os conceitos específicos formulados por Foucault.',D:'Incorreta. Panoptismo é um mecanismo do poder disciplinar, e genealogia é um método analítico, não uma forma de poder.'}},
    '4000000063':{sid:'4000000063',answer:'C',general:'',alternatives:{A:'Alternativa A está incorreta. Platão considera a Beleza uma ideia dotada de perfeição; nesse sentido, ela deve ser independente dos juízos particulares.',B:'Alternativa B está incorreta. Platão acredita que há uma Beleza superior; portanto, belo e feio se distinguem.',C:'Alternativa C está correta. A resposta está de acordo com a concepção platônica de conhecimento: é preciso conhecer a ideia de Beleza para julgar as coisas belas.',D:'Alternativa D está incorreta. Para Platão, o filósofo é capaz de ter acesso às ideias; o critério não é inacessível aos seres humanos.',E:'Alternativa E está incorreta. Para Platão, o objeto produzido pelo artista é aparência, não a Beleza em si.'}},
    '4000000266':{sid:'4000000266',answer:'B',alternatives:{},general:'A questão é interdisciplinar com Filosofia. O texto de Aristóteles associa virtude, prática e tornar-se bom, remetendo à reflexão ética. A estética se volta à arte, à aparência e à beleza; já a ética aristotélica trata das virtudes e da vida boa. Portanto, a resposta correta é B, ética.'},
    '4000000068':{sid:'4000000068',answer:'D',alternatives:{},general:'A projeção azimutal também é chamada de plana ou zenital; toda passagem de uma superfície tridimensional para um plano produz distorções; a projeção de Mercator foi criada para navegação; e a projeção azimutal é especialmente adequada à representação das regiões polares. Portanto, a alternativa correta é D.'}
  };

  const sidOf=q=>String(q?.sid??q?.question_id??q?.id??'').replace(/^(SOC|FIL|HIS|GEO)-/i,'').trim();
  function htmlText(value){
    if(value==null)return'';let raw=String(value);if(!raw.trim())return'';
    const div=document.createElement('div');
    div.innerHTML=raw.replace(/<br\s*\/?\s*>/gi,'\n').replace(/<\/p\s*>/gi,'\n').replace(/<\/li\s*>/gi,'\n');
    return (div.textContent||div.innerText||'').replace(/\u00a0/g,' ').replace(/[\t ]+\n/g,'\n').replace(/\n[\t ]+/g,'\n').replace(/\n{3,}/g,'\n\n').replace(/[ \t]{2,}/g,' ').trim();
  }
  function usefulGeneral(value){
    const t=htmlText(value);if(!t||/^GABARITO\s*:\s*ALTERNATIVA\s+[A-Z][\s.]*$/i.test(t))return'';
    return t.replace(/^GABARITO\s*:\s*ALTERNATIVA\s+[A-Z][\s.:-]*/i,'').trim();
  }
  function openDb(){
    if(dbPromise)return dbPromise;
    dbPromise=new Promise((resolve,reject)=>{
      if(!('indexedDB'in window)){reject(new Error('IndexedDB indisponível'));return}
      const req=indexedDB.open(DB_NAME,DB_VERSION);
      req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'sid'})};
      req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error||new Error('Falha no cache local'));
    });return dbPromise;
  }
  async function cacheGet(sid){
    if(STATIC[sid])return STATIC[sid];if(memory.has(sid))return memory.get(sid);
    try{const db=await openDb();const row=await new Promise(resolve=>{const r=db.transaction(STORE,'readonly').objectStore(STORE).get(sid);r.onsuccess=()=>resolve(r.result||null);r.onerror=()=>resolve(null)});if(row){memory.set(sid,row);return row}}catch(_){}
    return null;
  }
  async function cachePut(row){memory.set(row.sid,row);try{const db=await openDb();await new Promise(resolve=>{const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(row);tx.oncomplete=()=>resolve();tx.onerror=()=>resolve()})}catch(_){}}

  function normalizePayload(sid,payload){
    const data=payload?.response?.data??payload?.data??payload;
    if(!data||typeof data!=='object')return null;
    const alternatives={};
    (data.alternatives||data.solution_data?.alternatives||[]).forEach((a,i)=>{
      const letter=String(a?.letter??String.fromCharCode(65+i)).trim().toUpperCase();
      const t=htmlText(a?.solution_html??a?.commentary??'');if(letter&&t)alternatives[letter]=t;
    });
    const general=usefulGeneral(data.solution_html??data.solution_data?.solution_html??'');
    if(!general&&!Object.keys(alternatives).length)return null;
    return{sid,general,alternatives,answer:String(data.gabarito??data.solution_data?.gabarito??'').trim().toUpperCase(),fetchedAt:Date.now()};
  }
  function parseTextJson(text){
    const raw=String(text||'').trim();if(!raw)return null;
    try{return JSON.parse(raw)}catch(_){}
    const fenced=raw.match(/```(?:json)?\s*([\s\S]*?)```/i);if(fenced){try{return JSON.parse(fenced[1].trim())}catch(_){}}
    const a=raw.indexOf('{'),z=raw.lastIndexOf('}');if(a>=0&&z>a){try{return JSON.parse(raw.slice(a,z+1))}catch(_){}}
    return null;
  }
  function unwrapReader(value){
    if(!value)return null;
    if(typeof value==='string')return unwrapReader(parseTextJson(value));
    if(typeof value!=='object')return null;
    // Resposta original da API.
    const direct=value?.response?.data??value?.data??value;
    if(direct&&(direct.alternatives||direct.solution_data||direct.solution_html||direct.gabarito))return value;
    // Jina Reader em Accept: application/json guarda o conteúdo lido em data.content.
    const content=value?.data?.content??value?.content??value?.data?.text??value?.text;
    if(typeof content==='string')return unwrapReader(content);
    return null;
  }
  async function fetchOne(sid){
    const cached=await cacheGet(sid);if(cached)return cached;
    const target=`https://drivedepobre.com/api/questoes/q/${encodeURIComponent(sid)}/solucao`;
    const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),16000);
    try{
      const r=await fetch(`https://r.jina.ai/${target}`,{method:'GET',credentials:'omit',headers:{Accept:'application/json'},signal:controller.signal,cache:'default'});
      if(!r.ok)return null;
      const raw=await r.text();
      const outer=parseTextJson(raw)||raw;
      const payload=unwrapReader(outer);
      if(!payload)return null;
      const row=normalizePayload(sid,payload);if(row)await cachePut(row);return row;
    }catch(err){console.warn(`Comentário ${sid} indisponível`,err);return null}finally{clearTimeout(timer)}
  }
  function attach(q,row){
    if(!q||!row)return false;if(row.general)q.commentary=row.general;
    (q.o||[]).forEach((o,i)=>{const letter=String(o?.l??String.fromCharCode(65+i)).trim().toUpperCase();const t=row.alternatives?.[letter];if(t)o.commentary=t});
    q.__adelita_remote_commentary_v141=true;return !!(row.general||(q.o||[]).some(o=>o.commentary));
  }
  async function enrichQuestions(questions,{concurrency=3,onProgress=null}={}){
    const all=questions||[],already=all.filter(q=>q?.commentary||(q?.o||[]).some(o=>o?.commentary)).length;
    const qs=all.filter(q=>/^\d+$/.test(sidOf(q))&&!(q?.commentary||(q?.o||[]).some(o=>o?.commentary)));
    let cursor=0,done=0,found=already,failed=0;
    async function worker(){while(cursor<qs.length){const q=qs[cursor++],sid=sidOf(q);try{const row=await fetchOne(sid);if(row&&attach(q,row))found++;else failed++}catch(_){failed++}done++;try{onProgress?.({done,total:qs.length,found,failed})}catch(_){}}}
    await Promise.all(Array.from({length:Math.min(Math.max(1,concurrency),qs.length||1)},worker));
    return{total:all.length,queried:qs.length,found,missing:Math.max(0,all.length-found),failed};
  }
  window.AdelitaCommentaryLookup={enrichQuestions,staticCount:Object.keys(STATIC).length,clearMemory:()=>memory.clear()};
})();
