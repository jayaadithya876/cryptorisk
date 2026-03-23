
import axios from "axios";
import {useEffect,useState} from "react";
export default function Metrics(){

const [m,setM]=useState({});

useEffect(()=>{

axios.get("http://127.0.0.1:5000/metrics")
.then(res=>setM(res.data));

},[]);

return(

<div>
<h2>Metrics</h2>
<p>Macro F1: {m.macro_f1}</p>
<p>AUC: {m.auc}</p>
</div>

);

}