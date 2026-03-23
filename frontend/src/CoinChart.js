import { useEffect, useState } from "react"
import axios from "axios"
import { Line } from "react-chartjs-2"

import {
Chart as ChartJS,
CategoryScale,
LinearScale,
PointElement,
LineElement,
Tooltip,
Filler
} from "chart.js"

ChartJS.register(
CategoryScale,
LinearScale,
PointElement,
LineElement,
Tooltip,
Filler
)

export default function CoinChart({coin}){

const [prices,setPrices] = useState([])
const [labels,setLabels] = useState([])

useEffect(()=>{
 loadChart()
},[coin])

const loadChart = async ()=>{

try{

let res = await axios.get(
`http://127.0.0.1:5000/history/${coin}`
)

let data = res.data

setPrices(data.map(d=>d.close))
setLabels(data.map(d=>d.date))

}catch(e){
console.log(e)
}

}

const data = {
labels: labels,
datasets: [
{
data: prices,
borderColor: "#22c55e",
borderWidth: 2,
tension: 0.4,
fill: true,
pointRadius: 0,
backgroundColor: (context)=>{
const chart = context.chart
const {ctx, chartArea} = chart
if (!chartArea) return null

const gradient = ctx.createLinearGradient(
0,
chartArea.top,
0,
chartArea.bottom
)

gradient.addColorStop(0,"rgba(34,197,94,0.5)")
gradient.addColorStop(1,"rgba(34,197,94,0)")

return gradient
}
}
]
}

const options = {

responsive:true,

interaction:{
mode:"index",
intersect:false
},

plugins:{
legend:{display:false},
tooltip:{
backgroundColor:"#111827",
titleColor:"#fff",
bodyColor:"#fff",
callbacks:{
label:(ctx)=>`$${ctx.parsed.y.toLocaleString()}`
}
}
},

scales:{
x:{
ticks:{color:"#9ca3af"},
grid:{display:false}
},
y:{
ticks:{color:"#9ca3af"},
grid:{color:"#1f2937"}
}
}

}

return(

<div style={{
background:"#111827",
padding:25,
borderRadius:18
}}>

<h2 style={{marginBottom:20}}>
{coin} Price Chart
</h2>

{prices.length>0 && (
<Line data={data} options={options}/>
)}

</div>

)

}