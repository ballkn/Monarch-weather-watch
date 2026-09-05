const LAT=35.7345, LON=-81.3445;

function dirName(d){
  const a=["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"];
  return a[Math.round((d%360)/22.5)%16];
}
function northerlyScore(d){
  let x=Math.abs(((d+180)%360)-180);
  if(x<=22.5) return 20;
  if(x<=67.5) return 16;
  if(x<=90) return 9;
  return 0;
}
async function loadWeather(){
  const u=`https://api.open-meteo.com/v1/forecast?latitude=${LAT}&longitude=${LON}&hourly=temperature_2m,dew_point_2m,precipitation_probability,precipitation,cloud_cover,wind_speed_10m,wind_direction_10m&temperature_unit=fahrenheit&wind_speed_unit=mph&precipitation_unit=inch&timezone=America%2FNew_York&past_days=2&forecast_days=2`;
  const r=await fetch(u); const j=await r.json(); const h=j.hourly;
  const now=new Date();
  const today=now.toISOString().slice(0,10);
  const idx=h.time.map((t,i)=>({t:new Date(t),i})).filter(x=>{
    const hr=x.t.getHours(); return x.t.toISOString().slice(0,10)===today && hr>=12 && hr<=17;
  });
  if(!idx.length) throw new Error("No afternoon forecast available");
  const vals=k=>idx.map(x=>h[k][x.i]);
  const temp=Math.max(...vals("temperature_2m"));
  const cloud=vals("cloud_cover").reduce((a,b)=>a+b,0)/idx.length;
  const rain=Math.max(...vals("precipitation_probability"));
  const wind=vals("wind_speed_10m").reduce((a,b)=>a+b,0)/idx.length;
  const dirs=vals("wind_direction_10m");
  const dir=dirs.reduce((a,b)=>a+b,0)/dirs.length;

  // Approximate post-front signal: compare recent 6h to 18–30h prior.
  const allTimes=h.time.map(t=>new Date(t));
  const recent=[], prior=[];
  allTimes.forEach((t,i)=>{
    const dh=(now-t)/3600000;
    if(dh>=0 && dh<=6) recent.push(i);
    if(dh>=18 && dh<=30) prior.push(i);
  });
  const avg=(arr,k)=>arr.reduce((s,i)=>s+h[k][i],0)/Math.max(1,arr.length);
  const dewDrop=avg(prior,"dew_point_2m")-avg(recent,"dew_point_2m");
  const tempDrop=avg(prior,"temperature_2m")-avg(recent,"temperature_2m");
  const postFront=Math.max(0, Math.min(25, dewDrop*1.6 + tempDrop*0.5));

  let score=0;
  score += temp>=72?20:temp>=68?16:temp>=64?8:0;
  score += cloud<=25?20:cloud<=50?15:cloud<=70?7:0;
  score += rain<=10?15:rain<=25?10:rain<=40?4:0;
  score += northerlyScore(dir);
  score += postFront;
  score=Math.round(Math.min(100,score));

  const cls=score>=75?"good":score>=55?"maybe":"poor";
  const status=score>=75?"High monarch lookout potential":score>=55?"Moderate potential":"Low potential";
  document.querySelector("#score").firstChild.nodeValue=score;
  const st=document.querySelector("#status"); st.textContent=status; st.className=cls;
  document.querySelector("#temp").textContent=`${Math.round(temp)}°F`;
  document.querySelector("#wind").textContent=`${dirName(dir)} ${Math.round(wind)} mph`;
  document.querySelector("#cloud").textContent=`${Math.round(cloud)}%`;
  document.querySelector("#rain").textContent=`${Math.round(rain)}%`;
  document.querySelector("#window").textContent=score>=75?"Best bet: watch sunny nectar patches from about 1–4 PM.":"Check again as the forecast changes.";
  const chips=[
    temp>=68?"Warm enough":"Cool",
    cloud<=50?"Good sun":"Cloudy",
    rain<=25?"Dry":"Rain risk",
    northerlyScore(dir)>=16?"Favorable north wind":"Wind not strongly northerly",
    postFront>=10?"Likely post-front":"Weak post-front signal"
  ];
  document.querySelector("#reasons").innerHTML=chips.map(x=>`<span class="pill">${x}</span>`).join("");
}
document.querySelector("#testBtn").addEventListener("click", async()=>{
  if(!("Notification" in window)){alert("Notifications are not supported here.");return;}
  const p=await Notification.requestPermission();
  if(p==="granted") new Notification("🦋 Monarch Weather Watch",{body:"Test successful. Your device can display Monarch Weather Watch notifications.",icon:"icon-192.png"});
  else alert("Notification permission was not granted.");
});
if("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js");
loadWeather().catch(e=>{document.querySelector("#status").textContent="Weather check failed: "+e.message;});
