import { useEffect, useState, useCallback } from "react"
import axios from "axios"
import { Bar } from "react-chartjs-2"
import CoinChart from "./CoinChart"

import {
Chart as ChartJS,
CategoryScale,
LinearScale,
BarElement
} from "chart.js"

ChartJS.register(CategoryScale, LinearScale, BarElement)

export default function Dashboard(){

const [coin,setCoin] = useState("BTC")

const [signal,setSignal] = useState("")
const [probs,setProbs] = useState([])
const [history,setHistory] = useState([])
const [trade,setTrade] = useState("")
const [sentiment,setSentiment] = useState(null)

const [view,setView] = useState("live")
const [loading,setLoading] = useState(false)

const loadAll = useCallback(async ()=>{

try{

setLoading(true)

let p = await axios.get(`http://127.0.0.1:5000/predict/${coin}`)
setSignal(p.data.prediction)
setProbs(p.data.probabilities)
setTrade(p.data.trade)

let s = await axios.get(`http://127.0.0.1:5000/sentiment/${coin}`)
setSentiment(s.data.sentiment_score)

let h = await axios.get(`http://127.0.0.1:5000/history/${coin}`)
setHistory(h.data)

setTimeout(()=>setLoading(false),500)

}catch(e){
console.log(e)
setLoading(false)
}

},[coin])

useEffect(()=>{
loadAll()
},[coin,view])

return(

<div style={{
padding:30,
background:"#0b1220",
color:"white",
minHeight:"100vh",
maxWidth:1400,
margin:"auto"
}}>

{/* ⭐ LOADER */}

{loading && (
<div style={loader}>
<div className="spin"/>
<h2 style={{marginTop:20}}>Loading {coin}...</h2>
</div>
)}

{/* ⭐ HEADER */}

<h1 style={logo}>CCRisk</h1>

{/* ⭐ MODE BUTTONS */}

<div style={{textAlign:"center",marginBottom:25}}>

<button
onClick={()=>setView("live")}
style={toggle(view==="live")}
>
Live
</button>

<button
onClick={()=>setView("history")}
style={toggle(view==="history")}
>
History
</button>

</div>

{/* ⭐ COIN SELECT */}

<div style={{textAlign:"center",marginBottom:25}}>
<select
value={coin}
onChange={e=>setCoin(e.target.value)}
style={select}
>
<option>BTC</option>
<option>ETH</option>
<option>SOL</option>
<option>XRP</option>
</select>
</div>

{/* ⭐ LIVE MODE */}

{view==="live" && (

<>
<div style={cardWrap}>

<div style={card}>
<h3>Trade</h3>
<h1 style={{
color:
trade==="BUY"?"#22c55e":
trade==="HOLD"?"#f59e0b":"#ef4444"
}}>
{trade || "-"}
</h1>
</div>

<div style={card}>
<h3>Risk Signal</h3>
<h1 style={{
color:
signal==="LOW"?"#22c55e":
signal==="MED"?"#f59e0b":"#ef4444"
}}>
{signal || "-"}
</h1>
</div>

<div style={card}>
<h3>Sentiment</h3>
<h1 style={{color:"#38bdf8"}}>
{sentiment!==null ? sentiment.toFixed(3) : "-"}
</h1>
</div>

<div style={{...card,flex:2}}>
<h3>Risk Probabilities</h3>

{probs.length>0 && (
<Bar
data={{
labels:["LOW","MED","HIGH"],
datasets:[{
data:probs,
backgroundColor:["#22c55e","#f59e0b","#ef4444"]
}]
}}
options={{
plugins:{legend:{display:false}},
scales:{y:{display:false},x:{ticks:{color:"white"}}}
}}
/>
)}

</div>

</div>

<br/>

<CoinChart coin={coin}/>

</>

)}

{/* ⭐ HISTORY MODE */}

{view==="history" && (

<div style={tableBox}>

<h2 style={{marginBottom:20}}>
Last 30 Day Risk ({coin})
</h2>

<table style={{width:"100%",borderCollapse:"collapse"}}>

<thead>
<tr style={thead}>
<th style={th}>Date</th>
<th style={th}>Open</th>
<th style={th}>High</th>
<th style={th}>Close</th>
<th style={th}>Risk</th>
</tr>
</thead>

<tbody>

{history.map((row,i)=>(

<tr key={i} style={rowLine}>

<td style={td}>{row.date}</td>
<td style={td}>${Number(row.open).toLocaleString()}</td>
<td style={td}>${Number(row.high).toLocaleString()}</td>
<td style={td}>${Number(row.close).toLocaleString()}</td>

<td style={td}>
<span style={{
padding:"6px 14px",
borderRadius:20,
fontWeight:600,
color:
row.prediction==="LOW"?"#22c55e":
row.prediction==="MED"?"#f59e0b":"#ef4444",
border:
row.prediction==="LOW"?"1px solid #22c55e":
row.prediction==="MED"?"1px solid #f59e0b":"1px solid #ef4444"
}}>
{row.prediction}
</span>
</td>

</tr>

))}

</tbody>

</table>

</div>

)}

<style>{`

.spin{
width:70px;
height:70px;
border-radius:50%;
border:6px solid #1f2937;
border-top:6px solid #38bdf8;
animation:spin 1s linear infinite;
}

@keyframes spin{
100%{transform:rotate(360deg)}
}

`}</style>

</div>

)

}

const logo={
fontSize:64,
fontWeight:900,
textAlign:"center",
marginBottom:30,
background:"linear-gradient(90deg,#22c55e,#38bdf8,#a78bfa)",
WebkitBackgroundClip:"text",
WebkitTextFillColor:"transparent"
}

const loader={
position:"fixed",
top:0,
left:0,
width:"100vw",
height:"100vh",
background:"rgba(11,18,32,.95)",
display:"flex",
flexDirection:"column",
justifyContent:"center",
alignItems:"center",
zIndex:9999
}

const toggle=(active)=>({
marginRight:10,
padding:"8px 18px",
background: active ? "#38bdf8" : "#1f2937",
border:"none",
borderRadius:8,
color:"white",
cursor:"pointer"
})

const select={
padding:12,
borderRadius:10,
background:"#111827",
color:"white",
border:"1px solid #1f2937"
}

const cardWrap={
display:"flex",
gap:20,
flexWrap:"wrap"
}

const card={
background:"#111827",
padding:25,
borderRadius:18,
minWidth:220,
flex:1
}

const tableBox={
background:"#111827",
padding:25,
borderRadius:18
}

const thead={
borderBottom:"1px solid #1f2937",
color:"#9ca3af",
textAlign:"left"
}

const th={padding:12}
const td={padding:12}
const rowLine={borderBottom:"1px solid #1f2937"}