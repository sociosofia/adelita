// ADELITA-COMMENTARY-LOOKUP-v1.3
(() => {
  const SOURCES={sociologia:'./comments/sociologia.json'};
  const cache=new Map();
  const sidOf=q=>String(q?.sid??q?.question_id??q?.id??'').replace(/^(SOC|FIL|HIS|GEO)-/i,'').trim();
  const discOf=q=>{
    const d=String(q?.d??q?.discipline??'').toLowerCase();
    if(SOURCES[d])return d;
    const id=String(q?.id??'').toUpperCase();
    if(id.startsWith('SOC-'))return'sociologia';
    if(id.startsWith('FIL-'))return'filosofia';
    if(id.startsWith('HIS-'))return'historia';
    if(id.startsWith('GEO-'))return'geografia';
    return d;
  };
  async function load(d){
    if(!SOURCES[d])return null;
    if(cache.has(d))return cache.get(d);
    const p=fetch(SOURCES[d],{cache:'default'}).then(async r=>{
      if(!r.ok)throw new Error(`Comentários ${d}: HTTP ${r.status}`);
      return r.json();
    }).catch(err=>{cache.delete(d);throw err});
    cache.set(d,p);return p;
  }
  function attach(q,entry){
    if(!q||!entry)return false;
    const general=Array.isArray(entry)?entry[0]:entry.g;
    const altList=Array.isArray(entry)?entry[1]:entry.o;
    if(general)q.commentary=general;
    (q.o||[]).forEach((o,i)=>{
      let text='';
      if(Array.isArray(altList))text=altList[i]||'';
      else if(altList&&typeof altList==='object')text=altList[String(o?.l||String.fromCharCode(65+i)).toUpperCase()]||'';
      if(text)o.commentary=text;
    });
    q.__adelita_remote_commentary_v13=true;
    return !!(general||(q.o||[]).some(o=>o.commentary));
  }
  async function enrichQuestions(questions,{quiet=false}={}){
    const qs=questions||[],groups=new Map();
    qs.forEach(q=>{const d=discOf(q);if(!SOURCES[d])return;if(!groups.has(d))groups.set(d,[]);groups.get(d).push(q)});
    let found=0,supported=0,failed=[];
    await Promise.all([...groups.entries()].map(async([d,list])=>{
      supported+=list.length;
      try{
        const data=await load(d)||{};
        list.forEach(q=>{const e=data[sidOf(q)];if(e&&attach(q,e))found++});
      }catch(err){console.warn(err);failed.push(d)}
    }));
    return{total:qs.length,supported,found,missing:Math.max(0,qs.length-found),failed:[...new Set(failed)]};
  }
  window.AdelitaCommentaryLookup={enrichQuestions,sources:Object.keys(SOURCES),clearMemory:()=>cache.clear()};
})();
