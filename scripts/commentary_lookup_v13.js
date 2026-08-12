// ADELITA-COMMENTARY-LOOKUP-v1.3.2
(() => {
  const API_BASE='https://drivedepobre.com/api/questoes/q/';
  const DB_NAME='adelita_commentary_remote_v13';
  const DB_VERSION=1;
  const STORE='comments';
  const memory=new Map();
  let dbPromise=null;

  // Semente estática para validar o novo caminho sem CORS. A próxima etapa
  // amplia esta camada a partir dos quatro JSONs enriquecidos completos.
  // As chaves são IDs globais da questão, portanto funcionam em qualquer
  // disciplina em que aquela questão apareça.
  const STATIC={
    '4000331118':{
      sid:'4000331118',answer:'A',
      general:'A questão exige reconhecer a distinção feita por Foucault entre duas formas modernas de exercício do poder: uma voltada ao corpo individual e outra à regulação da população como conjunto biológico.',
      alternatives:{
        A:'Correta. O primeiro tipo corresponde ao poder disciplinar, que atua sobre os corpos individuais por meio de vigilância, normalização e controle; o segundo é o biopoder, que regula populações por meio de estatísticas, políticas de saúde e gestão da vida coletiva.',
        B:'Incorreta. “Dominação legal” é conceito associado a Weber, não a Foucault, e não corresponde ao primeiro tipo descrito.',
        C:'Incorreta. A alternativa é genérica e não utiliza os conceitos específicos formulados por Foucault.',
        D:'Incorreta. Panoptismo é um mecanismo do poder disciplinar, e genealogia é um método analítico, não uma forma de poder.'
      }
    },
    '4000000063':{
      sid:'4000000063',answer:'C',general:'',
      alternatives:{
        A:'Alternativa A está incorreta. Platão considera a Beleza uma ideia dotada de perfeição; nesse sentido, ela deve ser independente dos juízos particulares.',
        B:'Alternativa B está incorreta. Platão acredita que há uma Beleza superior; portanto, belo e feio se distinguem.',
        C:'Alternativa C está correta. A resposta está de acordo com a concepção platônica de conhecimento: é preciso conhecer a ideia de Beleza para julgar as coisas belas.',
        D:'Alternativa D está incorreta. Para Platão, o filósofo é capaz de ter acesso às ideias; o critério não é inacessível aos seres humanos.',
        E:'Alternativa E está incorreta. Para Platão, o objeto produzido pelo artista é aparência, não a Beleza em si.'
      }
    },
    '4000000266':{
      sid:'4000000266',answer:'B',alternatives:{},
      general:'A questão é interdisciplinar com Filosofia. O texto de Aristóteles associa virtude, prática e tornar-se bom, remetendo à reflexão ética. A estética se volta à arte, à aparência e à beleza; já a ética aristotélica trata das virtudes e da vida boa. Portanto, a resposta correta é B, ética.'
    },
    '4000000068':{
      sid:'4000000068',answer:'D',alternatives:{},
      general:'A projeção azimutal também é chamada de plana ou zenital; toda passagem de uma superfície tridimensional para um plano produz distorções; a projeção de Mercator foi criada para navegação; e a projeção azimutal é especialmente adequada à representação das regiões polares. Portanto, a alternativa correta é D.'
    }
  };

  const sidOf=q=>String(q?.sid??q?.question_id??q?.id??'')
    .replace(/^(SOC|FIL|HIS|GEO)-/i,'').trim();

  function htmlText(value){
    if(value==null)return'';
    let raw=String(value);
    if(!raw.trim())return'';
    if(typeof document!=='undefined'){
      const div=document.createElement('div');
      div.innerHTML=raw
        .replace(/<br\s*\/?\s*>/gi,'\n')
        .replace(/<\/p\s*>/gi,'\n')
        .replace(/<\/li\s*>/gi,'\n');
      raw=div.textContent||div.innerText||'';
    }else{
      raw=raw.replace(/<br\s*\/?\s*>/gi,'\n').replace(/<\/p\s*>/gi,'\n').replace(/<[^>]+>/g,' ');
    }
    return raw.replace(/\u00a0/g,' ')
      .replace(/[\t ]+\n/g,'\n').replace(/\n[\t ]+/g,'\n')
      .replace(/\n{3,}/g,'\n\n').replace(/[ \t]{2,}/g,' ').trim();
  }

  function usefulGeneral(value){
    const text=htmlText(value);
    if(!text)return'';
    if(/^GABARITO\s*:\s*ALTERNATIVA\s+[A-Z]\s*$/i.test(text))return'';
    return text;
  }

  function openDb(){
    if(dbPromise)return dbPromise;
    dbPromise=new Promise((resolve,reject)=>{
      if(!('indexedDB'in window)){reject(new Error('IndexedDB indisponível'));return}
      const req=indexedDB.open(DB_NAME,DB_VERSION);
      req.onupgradeneeded=()=>{
        const db=req.result;
        if(!db.objectStoreNames.contains(STORE))db.createObjectStore(STORE,{keyPath:'sid'});
      };
      req.onsuccess=()=>resolve(req.result);
      req.onerror=()=>reject(req.error||new Error('Falha no cache local de comentários'));
    });
    return dbPromise;
  }

  async function cacheGet(sid){
    if(STATIC[sid])return STATIC[sid];
    if(memory.has(sid))return memory.get(sid);
    try{
      const db=await openDb();
      const row=await new Promise(resolve=>{
        const req=db.transaction(STORE,'readonly').objectStore(STORE).get(sid);
        req.onsuccess=()=>resolve(req.result||null);req.onerror=()=>resolve(null);
      });
      if(row){memory.set(sid,row);return row}
    }catch(_){ }
    return null;
  }

  async function cachePut(row){
    memory.set(row.sid,row);
    try{
      const db=await openDb();
      await new Promise(resolve=>{
        const tx=db.transaction(STORE,'readwrite');tx.objectStore(STORE).put(row);
        tx.oncomplete=()=>resolve();tx.onerror=()=>resolve();
      });
    }catch(_){ }
  }

  function normalizePayload(sid,payload){
    const data=payload?.data??payload?.response?.data??payload;
    if(!data||typeof data!=='object')return null;
    const alternatives={};
    (data.alternatives||[]).forEach((a,i)=>{
      const letter=String(a?.letter??String.fromCharCode(65+i)).trim().toUpperCase();
      const text=htmlText(a?.solution_html??a?.commentary??'');
      if(letter&&text)alternatives[letter]=text;
    });
    const general=usefulGeneral(data.solution_html??'');
    if(!general&&!Object.keys(alternatives).length)return null;
    return{sid,general,alternatives,answer:String(data.gabarito??'').trim().toUpperCase(),fetchedAt:Date.now()};
  }

  async function fetchOne(sid){
    const cached=await cacheGet(sid);if(cached)return cached;
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),9000);
    try{
      const r=await fetch(`${API_BASE}${encodeURIComponent(sid)}/solucao`,{
        method:'GET',mode:'cors',credentials:'omit',headers:{Accept:'application/json'},signal:controller.signal,cache:'no-store'
      });
      if(!r.ok)return null;
      const payload=await r.json();
      const row=normalizePayload(sid,payload);
      if(row)await cachePut(row);
      return row;
    }finally{clearTimeout(timer)}
  }

  function attach(q,row){
    if(!q||!row)return false;
    if(row.general)q.commentary=row.general;
    (q.o||[]).forEach((o,i)=>{
      const letter=String(o?.l??String.fromCharCode(65+i)).trim().toUpperCase();
      const text=row.alternatives?.[letter];if(text)o.commentary=text;
    });
    q.__adelita_remote_commentary_v13=true;
    return !!(row.general||(q.o||[]).some(o=>o.commentary));
  }

  async function enrichQuestions(questions,{concurrency=5,onProgress=null}={}){
    const all=questions||[];
    const already=all.filter(q=>q?.commentary||(q?.o||[]).some(o=>o?.commentary)).length;
    const qs=all.filter(q=>/^\d+$/.test(sidOf(q))&&!(q?.commentary||(q?.o||[]).some(o=>o?.commentary)));
    let cursor=0,done=0,found=already,failed=0;
    async function worker(){
      while(cursor<qs.length){
        const q=qs[cursor++],sid=sidOf(q);
        try{const row=await fetchOne(sid);if(row&&attach(q,row))found++}
        catch(err){failed++;console.warn(`Comentário ${sid} indisponível`,err)}
        done++;try{onProgress?.({done,total:qs.length,found,failed})}catch(_){ }
      }
    }
    await Promise.all(Array.from({length:Math.min(Math.max(1,concurrency),qs.length||1)},worker));
    return{total:all.length,queried:qs.length,found,missing:Math.max(0,all.length-found),failed};
  }

  window.AdelitaCommentaryLookup={enrichQuestions,endpoint:API_BASE,staticCount:Object.keys(STATIC).length,clearMemory:()=>memory.clear()};
})();
