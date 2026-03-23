import axios from "axios";
import { useState } from "react";
import { Bar } from "react-chartjs-2";
import {
Chart as ChartJS,
CategoryScale,
LinearScale,
BarElement
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, BarElement);

export default function Predict(){

const [ohlcv,setOhlcv]=useState({
open:"",
high:"",
low:"",
close:"",
volume:""
});

const [result,setResult]=useState("");
const [probs,setProbs]=useState([]);

const fetchBTC = async ()=>{

const res = await axios.get(
"http://127.0.0.1:5000/livebtc"
);

setOhlcv(res.data);

};

const predict = async ()=>{

const res = await axios.post(
"http://127.0.0.1:5000/predict",
ohlcv
);

setResult(res.data.prediction);
setProbs(res.data.probabilities);

};

return(

<div style={{padding:20}}>

<h2>BTC Risk Predictor</h2>

<button onClick={fetchBTC}>
Fetch Live BTC
</button>

<br/><br/>

{Object.keys(ohlcv).map(k=>(
<input
key={k}
placeholder={k}
value={ohlcv[k]}
onChange={e=>{
setOhlcv({...ohlcv,[k]:e.target.value})
}}
style={{margin:5}}
/>
))}

<br/><br/>

<button onClick={predict}>
Predict Risk
</button>

<h2>{result}</h2>

{probs.length>0 && (

<Bar
data={{
labels:["LOW","MED","HIGH"],
datasets:[{
label:"Risk Probability",
data:probs,
backgroundColor:["green","orange","red"]
}]
}}
/>

)}

</div>

);

}