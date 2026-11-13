# -*- coding: utf-8 -*-
"""
生成「国家统计局 · 十年主题」交互大屏（教育 / 旅游 / 工业）。

数据与口径
----------
旅游：文化和旅游部《2025 年文化和旅游发展统计公报》图 5，2015—2025 年
      国内居民出游人次与花费完整序列，本页取 2015—2024 十年。
教育：国家统计局历年《国民经济和社会发展统计公报》、教育部
      《全国教育事业发展统计公报》中的招生 / 在校生 / 毛入学率等指标。
工业：国家统计局历年《国民经济和社会发展统计公报》中的全部工业增加值、
      规模以上工业增加值增速、主要工业产品产量与分门类增速。

其中部分年份为按公报口径整理的可比约数，仅用于教学演示，
不作为统计引用依据。每屏均为单文件自包含 HTML（内联 ECharts），
双击即可离线打开，也可直接由 GitHub Pages 发布。

用法：python stats/build_decade_dashboards.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 数据
YEARS_EDU = [str(y) for y in range(2014, 2024)]
YEARS_TOUR = [str(y) for y in range(2015, 2025)]
YEARS_IND = [str(y) for y in range(2014, 2024)]

EDU = {
    "years": YEARS_EDU,
    "series": {
        "ug_enroll":  [721.4, 737.8, 748.6, 761.5, 791.0, 914.9, 967.5, 1001.3, 1014.5, 1042.2],
        "pg_enroll":  [62.1, 64.5, 66.7, 80.6, 85.8, 91.7, 110.7, 117.7, 124.2, 130.2],
        "ug_stock":   [2547.7, 2625.3, 2695.8, 2753.6, 2831.0, 3031.5, 3285.3, 3496.1, 3659.4, 3775.0],
        "pg_stock":   [184.8, 191.1, 198.1, 263.9, 273.1, 286.4, 314.0, 333.2, 365.4, 388.3],
        "gross":      [37.5, 40.0, 42.7, 45.7, 48.1, 51.6, 54.4, 57.8, 59.6, 60.2],
        "compulsory": [92.6, 93.0, 93.4, 93.8, 94.2, 94.8, 95.2, 95.4, 95.5, 95.7],
    },
    "meta": {
        "ug_enroll":  {"label": "普通本专科招生", "unit": "万人", "color": "#0e9f96"},
        "pg_enroll":  {"label": "研究生招生", "unit": "万人", "color": "#4b7fd0"},
        "ug_stock":   {"label": "本专科在校生", "unit": "万人", "color": "#ef9a45"},
        "pg_stock":   {"label": "在学研究生", "unit": "万人", "color": "#7b6cf6"},
        "gross":      {"label": "高等教育毛入学率", "unit": "%", "color": "#e2684f"},
        "compulsory": {"label": "九年义务教育巩固率", "unit": "%", "color": "#8fd3c7"},
    },
    "kpis": ["ug_enroll", "pg_enroll", "gross", "compulsory", "ug_stock"],
    "structure": {
        "title": "2023 年各级教育在校生规模",
        "items": [["普通小学", 10836.0], ["初中", 5243.7], ["普通高中", 2803.6],
                  ["中等职业教育", 1737.9], ["普通、职业本专科", 3775.0], ["研究生", 388.3]],
        "unit": "万人",
    },
    "ranking": {
        "title": "2023 年各学段招生规模",
        "items": [["普通小学", 1877.9], ["初中", 1754.6], ["普通、职业本专科", 1042.2],
                  ["普通高中", 967.8], ["中等职业教育", 616.5], ["研究生", 130.2]],
        "unit": "万人",
    },
    "insight": "十年间高等教育从「精英化」走到「普及化」：毛入学率抬升的同时，研究生招生规模翻倍，扩张重心从本专科向高层次人才培养上移。",
    "source": "国家统计局历年《国民经济和社会发展统计公报》、教育部《全国教育事业发展统计公报》",
}

TOUR_SPEND = [3.4, 3.9, 4.6, 5.1, 5.7, 2.2, 2.9, 2.0, 4.9, 5.8]
TOUR_TRIPS = [39.9, 44.4, 50.0, 55.4, 60.1, 28.8, 32.5, 25.3, 48.9, 56.2]
TOUR = {
    "years": YEARS_TOUR,
    "series": {
        "trips":   TOUR_TRIPS,
        "spend":   TOUR_SPEND,
        "percap":  [round(s * 10000 / t) for s, t in zip(TOUR_SPEND, TOUR_TRIPS)],
        "recover": [round(t / 60.1 * 100, 1) for t in TOUR_TRIPS],
    },
    "meta": {
        "trips":   {"label": "国内出游人次", "unit": "亿人次", "color": "#0e9f96"},
        "spend":   {"label": "国内出游总花费", "unit": "万亿元", "color": "#4b7fd0"},
        "percap":  {"label": "人均每次花费", "unit": "元", "color": "#ef9a45"},
        "recover": {"label": "相当于 2019 年", "unit": "%", "color": "#e2684f"},
    },
    "kpis": ["trips", "spend", "percap", "recover"],
    "structure": {
        "title": "2023 年国内出游人次 · 城乡构成",
        "items": [["城镇居民", 37.6], ["农村居民", 11.3]],
        "unit": "亿人次",
    },
    "ranking": {
        "title": "十年间国内出游人次（亿人次）",
        "items": [[y, t] for y, t in zip(YEARS_TOUR, TOUR_TRIPS)],
        "unit": "亿人次",
    },
    "insight": "2019 年 60.1 亿人次是疫情前的峰值，2020—2022 三年断崖，2023 年恢复至 81.4%，2024 年回到 56.2 亿人次；人次恢复得快，人均花费恢复得慢。",
    "source": "文化和旅游部《2025 年文化和旅游发展统计公报》图 5、国家统计局历年统计公报",
}

IND = {
    "years": YEARS_IND,
    "series": {
        "va":      [22.8, 23.5, 24.9, 27.5, 30.1, 31.2, 31.3, 37.3, 40.2, 39.9],
        "igrowth": [8.3, 6.1, 6.0, 6.6, 6.2, 5.7, 2.8, 9.6, 3.6, 4.6],
        "steel":   [8.23, 8.04, 8.08, 8.32, 9.28, 9.96, 10.53, 10.33, 10.13, 10.19],
        "power":   [5.65, 5.74, 6.14, 6.50, 6.99, 7.34, 7.62, 8.53, 8.84, 8.91],
        "profit":  [6.47, 6.36, 6.88, 7.52, 6.64, 6.20, 6.45, 8.71, 8.40, 7.69],
    },
    "meta": {
        "va":      {"label": "全部工业增加值", "unit": "万亿元", "color": "#0e9f96"},
        "igrowth": {"label": "规上工业增加值增速", "unit": "%", "color": "#4b7fd0"},
        "steel":   {"label": "粗钢产量", "unit": "亿吨", "color": "#ef9a45"},
        "power":   {"label": "发电量", "unit": "万亿千瓦时", "color": "#7b6cf6"},
        "profit":  {"label": "规上工业企业利润", "unit": "万亿元", "color": "#e2684f"},
    },
    "kpis": ["va", "igrowth", "steel", "power", "profit"],
    "structure": {
        "title": "2023 年规上工业分门类增加值增速",
        "items": [["制造业", 5.0], ["电力热力燃气及水", 4.3], ["采矿业", 2.3]],
        "unit": "%",
    },
    "ranking": {
        "title": "2023 年规上工业分经济类型增速",
        "items": [["股份制企业", 5.3], ["国有控股企业", 5.0],
                  ["电力热力燃气及水", 4.3], ["外商及港澳台商", 1.4], ["私营企业", 3.1]],
        "unit": "%",
    },
    "insight": "工业增加值十年从 22.8 万亿增至约 40 万亿，但增速中枢从 8% 降到 4% 左右；2020 年 2.8% 的低点与 2021 年 9.6% 的反弹，是疫情扰动下最醒目的两个点。",
    "source": "国家统计局历年《国民经济和社会发展统计公报》（全部工业增加值、规上工业增速、主要产品产量与分门类增速）",
}

# ---------------------------------------------------------------- 页面配置
PAGES = [
    {
        "file": "04_education.html",
        "title": "中国教育十年 · 2014—2023",
        "sub": "招生 / 在校生 / 毛入学率 · 数据来源：国家统计局、教育部年度统计公报",
        "badge": "EDUCATION",
        "data": EDU,
        "charts": [
            {"id": "c1", "span": "c8", "kind": "line", "key": "ug_enroll", "title": "普通本专科招生规模", "tag": "万人 · 十年趋势", "switch": True},
            {"id": "c2", "span": "c4", "kind": "pie", "title": "STRUCT_TITLE", "tag": "STRUCT_UNIT"},
            {"id": "c3", "span": "c6", "kind": "dual", "keys": ["pg_enroll", "pg_stock"], "title": "研究生招生与在学规模", "tag": "万人 · 双轴对照", "switch": False},
            {"id": "c4", "span": "c6", "kind": "bar", "key": "gross", "title": "高等教育毛入学率", "tag": "% · 普及化进程", "switch": True},
            {"id": "c5", "span": "c5", "kind": "hbar", "title": "RANK_TITLE", "tag": "RANK_UNIT"},
            {"id": "c6", "span": "c7", "kind": "scatter", "keys": ["ug_enroll", "gross"], "title": "招生规模 × 毛入学率", "tag": "每个点是一个年份"},
        ],
    },
    {
        "file": "05_tourism.html",
        "title": "中国旅游业十年 · 2015—2024",
        "sub": "出游人次 / 总花费 / 人均消费 · 数据来源：文化和旅游部、国家统计局",
        "badge": "TOURISM",
        "data": TOUR,
        "charts": [
            {"id": "c1", "span": "c8", "kind": "line", "key": "trips", "title": "国内出游人次", "tag": "亿人次 · 十年趋势", "switch": True},
            {"id": "c2", "span": "c4", "kind": "pie", "title": "STRUCT_TITLE", "tag": "STRUCT_UNIT"},
            {"id": "c3", "span": "c6", "kind": "dual", "keys": ["trips", "spend"], "title": "人次与总花费", "tag": "亿人次 / 万亿元 · 双轴", "switch": False},
            {"id": "c4", "span": "c6", "kind": "bar", "key": "percap", "title": "人均每次出游花费", "tag": "元 · 由总花费 / 人次推算", "switch": True},
            {"id": "c5", "span": "c5", "kind": "hbar", "title": "RANK_TITLE", "tag": "RANK_UNIT"},
            {"id": "c6", "span": "c7", "kind": "line", "key": "recover", "title": "相对 2019 年恢复度", "tag": "% · 2019 = 100", "switch": False},
        ],
    },
    {
        "file": "06_industry.html",
        "title": "中国工业十年 · 2014—2023",
        "sub": "工业增加值 / 增速 / 主要产品产量 · 数据来源：国家统计局年度统计公报",
        "badge": "INDUSTRY",
        "data": IND,
        "charts": [
            {"id": "c1", "span": "c8", "kind": "line", "key": "va", "title": "全部工业增加值", "tag": "万亿元 · 十年趋势", "switch": True},
            {"id": "c2", "span": "c4", "kind": "pie", "title": "STRUCT_TITLE", "tag": "STRUCT_UNIT"},
            {"id": "c3", "span": "c6", "kind": "bar", "key": "igrowth", "title": "规上工业增加值增速", "tag": "% · 增速中枢下移", "switch": False},
            {"id": "c4", "span": "c6", "kind": "dual", "keys": ["steel", "power"], "title": "粗钢产量与发电量", "tag": "亿吨 / 万亿千瓦时 · 双轴", "switch": False},
            {"id": "c5", "span": "c5", "kind": "hbar", "title": "RANK_TITLE", "tag": "RANK_UNIT"},
            {"id": "c6", "span": "c7", "kind": "scatter", "keys": ["igrowth", "profit"], "title": "增速 × 规上工业利润", "tag": "每个点是一个年份"},
        ],
    },
]

# ---------------------------------------------------------------- 模板
TEMPLATE = r"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__ · 国家统计局交互大屏</title>
<link rel="icon" href="data:,"><style>__CSS__</style>
<script>__ECHARTS__</script></head><body><div class="app">
<header><div class="brand"><div class="logo">▥</div><div><h1>__TITLE__</h1><p class="sub">__SUB__</p></div></div>
<div class="tools"><div class="seg" id="modeSeg"><button data-m="0" class="on">当年值</button><button data-m="1">同比</button></div>
<span class="qbadge" id="qbadge"></span><button class="btn" id="play">▶ 播放</button><button class="btn ghost" id="reset">↺ 重置</button></div></header>
<div class="timeline"><div class="tl-head"><span>年份时间轴 · 拖动选择年份（KPI、摘要与全部图表实时联动）</span><span id="hint">拖动时间轴 · 点击柱体 / 折点跳到该年 · 点击卡片聚焦</span></div>
<input type="range" id="slider" min="0" value="0"><div class="ticks" id="ticks"></div></div>
<div class="kpis" id="kpis"></div><div class="summary" id="summary"></div><div class="grid" id="grid"></div>
<footer><span><span class="pill">口径</span>__SOURCE__。部分指标按历年公报口径整理，个别年份为可比约数，仅用于教学演示，不作为统计引用依据。</span><span>国家统计局 · 十年主题交互大屏</span></footer></div>
<script>
const P=__PAYLOAD__;
const Y=P.years, S=P.series, M=P.meta, C=P.charts, K=P.kpis;
let i=Y.length-1, mode=0, focus=null, playing=false, timer=null, inst={};
const $=x=>document.getElementById(x);
const nf=(v,d=1)=>v==null?'—':Number(v).toLocaleString('zh-CN',{minimumFractionDigits:d,maximumFractionDigits:d});
const yoy=(k,n)=>n<1?null:(S[k][n]/S[k][n-1]-1)*100;
function val(k,n){return (mode===1&&P.switchKeys.indexOf(k)>=0)?yoy(k,n):S[k][n]}
function unit(k){return (mode===1&&P.switchKeys.indexOf(k)>=0)?'%':M[k].unit}
const COL=['#0e9f96','#4b7fd0','#ef9a45','#7b6cf6','#e2684f','#8fd3c7'];
const AX={axisLine:{lineStyle:{color:'#cfdce5'}},axisLabel:{color:'#7b90a0',fontSize:10},splitLine:{lineStyle:{color:'#eef3f6'}}};
const TT={trigger:'axis',backgroundColor:'#fff',borderColor:'#dfe8ee',textStyle:{color:'#16324a',fontSize:11}};

function kpiHTML(){
  return K.map((k,n)=>{
    const v=S[k][i], d=yoy(k,i), m=M[k];
    const cls=d==null?'flat':(d>=0?'up':'down');
    return `<div class="kpi ${focus===k?'focus':''}" data-k="${k}"><div class="kpi-top"><span>${m.label}</span><span class="kpi-tag">${Y[i]}</span></div>
    <div class="kpi-val">${nf(v)}<span class="unit">${m.unit}</span></div>
    <div class="kpi-delta"><span class="${cls}">同比 ${d==null?'—':(d>=0?'+':'')+nf(d)+'%'}</span><span class="flat">${nf(v-S[k][0])} 较 ${Y[0]}</span></div></div>`;
  }).join('');
}
function summaryHTML(){
  const main=K[0], v=nf(S[main][i]), d=yoy(main,i);
  return `<b>${Y[i]} 年</b> · ${M[main].label} ${v} ${M[main].unit}${d==null?'':`，同比 <span class="${d>=0?'up':'down'}">${d>=0?'+':''}${nf(d)}%</span>`}。<b>十年观察：</b>${P.insight}`;
}
function gridHTML(){
  return C.map(c=>{
    const t=c.title.replace('STRUCT_TITLE',P.structure.title).replace('RANK_TITLE',P.ranking.title);
    const g=c.tag.replace('STRUCT_UNIT',P.structure.unit).replace('RANK_UNIT',P.ranking.unit);
    return `<div class="card ${c.span}"><div class="card-h"><b>${t}</b><span>${g}</span></div><div class="chart" id="${c.id}"></div></div>`;
  }).join('');
}
function mark(k){
  return {symbol:'circle',symbolSize:9,data:[{xAxis:Y[i]}],lineStyle:{color:'#e2684f',type:'dashed',width:1.4},
    label:{show:true,formatter:Y[i],color:'#e2684f',fontSize:10,position:'insideEndTop'}};
}
function trend(c,k){
  const arr=Y.map((_,n)=>val(k,n)), m=M[k], isYoy=mode===1&&P.switchKeys.indexOf(k)>=0;
  return {
    tooltip:{...TT,valueFormatter:v=>nf(v,isYoy?1:2)},
    grid:{left:52,right:18,top:26,bottom:28},
    xAxis:{type:'category',data:Y,...AX,splitLine:{show:false}},
    yAxis:{type:'value',name:unit(k),nameTextStyle:{color:'#98a9b6',fontSize:10},...AX},
    series:[{type:c.kind==='bar'?'bar':'line',data:arr,name:m.label,smooth:.35,
      lineStyle:{width:2.6,color:m.color},itemStyle:{color:m.color,borderRadius:c.kind==='bar'?[4,4,0,0]:0},
      areaStyle:c.kind==='bar'?undefined:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:m.color+'55'},{offset:1,color:m.color+'05'}]}},
      markLine:mark(k),
      data:arr.map((v,n)=>({value:v,itemStyle:n===i?{color:'#e2684f'}:undefined}))}]
  };
}
function dual(c){
  const [a,b]=c.keys, ma=M[a], mb=M[b];
  return {tooltip:TT,legend:{data:[ma.label,mb.label],top:0,textStyle:{fontSize:10,color:'#6b7f90'}},
    grid:{left:52,right:52,top:32,bottom:28},
    xAxis:{type:'category',data:Y,...AX,splitLine:{show:false}},
    yAxis:[{type:'value',name:ma.unit,nameTextStyle:{color:'#98a9b6',fontSize:10},...AX},
           {type:'value',name:mb.unit,nameTextStyle:{color:'#98a9b6',fontSize:10},...AX,splitLine:{show:false}}],
    series:[
      {name:ma.label,type:'bar',data:S[a],itemStyle:{color:ma.color,borderRadius:[3,3,0,0]},markLine:mark(a)},
      {name:mb.label,type:'line',yAxisIndex:1,data:S[b],smooth:.35,symbolSize:6,
       lineStyle:{width:2.4,color:mb.color},itemStyle:{color:mb.color}}]};
}
function pie(c){
  const it=P.structure.items;
  return {tooltip:{trigger:'item',formatter:p=>`${p.name}<br/>${nf(p.value)} ${P.structure.unit} (${p.percent}%)`},
    legend:{orient:'vertical',right:4,top:'middle',textStyle:{fontSize:10,color:'#6b7f90'},itemWidth:9,itemHeight:9},
    series:[{type:'pie',radius:['42%','68%'],center:['36%','52%'],data:it.map((x,n)=>({name:x[0],value:x[1],itemStyle:{color:COL[n%COL.length]}})),
      label:{show:false},itemStyle:{borderColor:'#fff',borderWidth:2},
      emphasis:{label:{show:true,fontSize:11,fontWeight:'bold'}}}]};
}
function hbar(c){
  const it=P.ranking.items;
  return {tooltip:{...TT,trigger:'item',formatter:p=>`${p.name}<br/>${nf(p.value)} ${P.ranking.unit}`},
    grid:{left:96,right:34,top:12,bottom:22},
    xAxis:{type:'value',...AX},
    yAxis:{type:'category',data:it.map(x=>x[0]).reverse(),...AX,splitLine:{show:false},axisLabel:{color:'#6b7f90',fontSize:10}},
    series:[{type:'bar',data:it.map((x,n)=>({value:x[1],itemStyle:{color:COL[n%COL.length],borderRadius:[0,4,4,0]}})).reverse(),
      barWidth:'58%',label:{show:true,position:'right',fontSize:10,color:'#6b7f90',formatter:p=>nf(p.value,0)}}]};
}
function scatter(c){
  const [a,b]=c.keys;
  return {tooltip:{trigger:'item',formatter:p=>`${Y[p.dataIndex]} 年<br/>${M[a].label} ${nf(p.value[0])} ${M[a].unit}<br/>${M[b].label} ${nf(p.value[1])} ${M[b].unit}`},
    grid:{left:56,right:22,top:24,bottom:34},
    xAxis:{type:'value',name:M[a].unit,nameTextStyle:{color:'#98a9b6',fontSize:10},...AX},
    yAxis:{type:'value',name:M[b].unit,nameTextStyle:{color:'#98a9b6',fontSize:10},...AX},
    series:[{type:'scatter',data:S[a].map((v,n)=>({value:[v,S[b][n]],
      itemStyle:{color:n===i?'#e2684f':M[a].color,opacity:.85},
      symbolSize:n===i?18:10,label:n===i?{show:true,formatter:Y[n],position:'top',color:'#e2684f',fontSize:10}:undefined}))}]};
}
function option(c){
  if(c.kind==='line'||c.kind==='bar')return trend(c,c.key);
  if(c.kind==='dual')return dual(c);
  if(c.kind==='pie')return pie(c);
  if(c.kind==='hbar')return hbar(c);
  return scatter(c);
}
function render(){
  $('qbadge').textContent=Y[i];
  $('slider').max=Y.length-1; $('slider').value=i;
  $('slider').style.setProperty('--p',(i/(Y.length-1)*100)+'%');
  $('ticks').innerHTML=Y.map((y,n)=>`<span class="${n===i?'on':''}" data-n="${n}">${y}</span>`).join('');
  $('kpis').innerHTML=kpiHTML(); $('summary').innerHTML=summaryHTML();
  if(!$('grid').innerHTML)$('grid').innerHTML=gridHTML();
  document.querySelectorAll('.kpi').forEach(el=>el.onclick=()=>{focus=focus===el.dataset.k?null:el.dataset.k;render()});
  document.querySelectorAll('.ticks span').forEach(el=>el.onclick=()=>setYear(+el.dataset.n));
  C.forEach(c=>{
    const dom=$(c.id); if(!dom)return;
    if(!inst[c.id])inst[c.id]=echarts.init(dom);
    inst[c.id].setOption(option(c),true);
    inst[c.id].off('click');
    inst[c.id].on('click',p=>{if(p.dataIndex!=null&&p.dataIndex<Y.length)setYear(p.dataIndex)});
  });
}
function setYear(n){i=Math.max(0,Math.min(Y.length-1,n));render()}
function togglePlay(){
  playing=!playing; const b=$('play');
  b.textContent=playing?'❚❚ 暂停':'▶ 播放'; b.classList.toggle('playing',playing);
  if(playing)timer=setInterval(()=>setYear(i>=Y.length-1?0:i+1),1100);
  else clearInterval(timer);
}
$('slider').oninput=e=>setYear(+e.target.value);
$('play').onclick=togglePlay;
$('reset').onclick=()=>{if(playing)togglePlay();mode=0;focus=null;i=Y.length-1;
  document.querySelectorAll('#modeSeg button').forEach(b=>b.classList.toggle('on',b.dataset.m==='0'));render()};
document.querySelectorAll('#modeSeg button').forEach(b=>b.onclick=()=>{
  mode=+b.dataset.m;document.querySelectorAll('#modeSeg button').forEach(x=>x.classList.toggle('on',x===b));render()});
window.addEventListener('resize',()=>Object.values(inst).forEach(c=>c.resize()));
render();
</script></body></html>
"""


def load_css() -> str:
    src = (HERE / "01_gdp.html").read_text(encoding="utf-8")
    m = re.search(r"<style>(.*?)</style>", src, re.S)
    if not m:
        raise RuntimeError("01_gdp.html 中没有找到 <style> 段")
    return m.group(1)


def build() -> None:
    css = load_css()
    js = (ROOT / "echarts.min.js").read_text(encoding="utf-8").replace("</script", "<\\/script")
    for page in PAGES:
        data = dict(page["data"])
        switch_keys = [c["key"] for c in page["charts"]
                       if c.get("switch") and c.get("key")]
        payload = {
            "years": data["years"], "series": data["series"], "meta": data["meta"],
            "kpis": data["kpis"], "charts": page["charts"],
            "structure": data["structure"], "ranking": data["ranking"],
            "insight": data["insight"], "switchKeys": switch_keys,
        }
        html = (TEMPLATE
                .replace("__CSS__", css)
                .replace("__ECHARTS__", js)
                .replace("__TITLE__", page["title"])
                .replace("__SUB__", page["sub"])
                .replace("__SOURCE__", data["source"])
                .replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False)))
        out = HERE / page["file"]
        out.write_text(html, encoding="utf-8")
        print(f"生成 {out.name}  {out.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    build()
