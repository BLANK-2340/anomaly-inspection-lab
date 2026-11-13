"use strict";
(async()=>{
  const $=id=>document.getElementById(id);
  try {
    const response=await fetch("model.json");
    if (!response.ok) throw Error("Could not load frozen model");
    const bundle=await response.json();
    if (bundle.schema_version!==1) throw Error("Unsupported model bundle");
    function paint(id, grid, kind, scale=1) {
      const context=$(id).getContext("2d");
      grid.forEach((row,y)=>row.forEach((v,x)=>{
        const a=Math.max(0,Math.min(1,Number(v)/scale));
        context.fillStyle=kind==="heat"?`rgb(${Math.round(255*a)},${Math.round(145*a)},${Math.round(20*a)})`:
          `rgb(${Math.round(255*a)},${Math.round(255*a)},${Math.round(255*a)})`;
        context.fillRect(x,y,1,1);
      }));
    }
    function inspect(event) {
      event?.preventDefault();
      if (!$('controls').reportValidity()) return;
      try {
        const strength=Number($("strength").value), brightness=Number($("brightness").value);
        $("strength-value").textContent=strength.toFixed(2);
        $("brightness-value").textContent=brightness.toFixed(2);
        const spot=$("shape").value==="spot";
        const {image,mask}=Anomaly.perturb(bundle.samples[Number($("sample").value)].image,
          {x:Number($("x").value),y:Number($("y").value),width:spot?4:1,height:spot?4:6,strength,brightness});
        const variant=$("variant").value, threshold=bundle.thresholds[variant];
        const heatmap=Anomaly.score(image,bundle.model,variant==="standardized");
        const result=Anomaly.decide(heatmap,threshold), iou=Anomaly.iou(result.mask,mask);
        paint("input",image,"gray");paint("heatmap",heatmap,"heat",2*threshold);
        paint("predicted",result.mask,"gray");paint("truth",mask,"gray");
        $("decision").textContent=result.anomalous?"Anomaly detected":"Within normal threshold";
        $("metrics").textContent=`Maximum residual ${result.maximum.toFixed(6)} · frozen threshold ${threshold.toFixed(6)} · mask IoU ${iou===null?"undefined (empty union)":iou.toFixed(4)}`;
      } catch(error) {$("decision").textContent="Inspection error";$("metrics").textContent=error.message;}
    }
    $("controls").addEventListener("submit",inspect);
    $("clean").addEventListener("click",()=>{$("strength").value="0";inspect();});
    for (const id of ["strength","brightness"]) $(id).addEventListener("input",inspect);
    inspect();
  } catch(error) {$("decision").textContent="Demo unavailable";$("metrics").textContent=error.message;}
})();
