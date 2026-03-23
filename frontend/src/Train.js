import axios from "axios";
import {useState} from "react";

export default function Train(){

const [file,setFile]=useState(null);

const upload = async ()=>{

const form = new FormData();
form.append("file", file);

await axios({
  method: "post",
  url: "http://localhost:5000/train",
  data: form,
  headers: {
    "Content-Type": "multipart/form-data"
  }
});

alert("Model trained");

};

return(
<div>
<h2>Train Model</h2>

<input type="file" onChange={e=>setFile(e.target.files[0])}/>
<button onClick={upload}>Train</button>

</div>
);

}