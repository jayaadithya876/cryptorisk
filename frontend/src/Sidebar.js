import React from "react";

export default function Sidebar({setPage}) {

return (
<div style={{width:200,background:"#1e1e2f",height:"100vh",color:"white"}}>
<h2>BTC Risk</h2>

<button onClick={()=>setPage("dashboard")}>
Dashboard
</button>
<button onClick={()=>setPage("train")}>Train</button>
<button onClick={()=>setPage("predict")}>Predict</button>
<button onClick={()=>setPage("metrics")}>Metrics</button>

</div>
);

}