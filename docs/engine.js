/* Original browser CPU inference. SPDX-License-Identifier: MIT */
"use strict";
const Anomaly = (() => {
  function validate(image, model) {
    const {height:h, width:w, means, scales} = model;
    if (!Number.isInteger(h) || !Number.isInteger(w) || h<1 || w<1 || h>256 || w>256 ||
        !Array.isArray(means) || !Array.isArray(scales) ||
        means.length!==h*w || scales.length!==h*w ||
        means.some(x=>!Number.isFinite(x) || x<0 || x>1) ||
        scales.some(x=>!Number.isFinite(x) || x<=0)) throw Error("Invalid model");
    if (!Array.isArray(image) || image.length!==h || image.some(row=>
        !Array.isArray(row) || row.length!==w || row.some(x=>
          typeof x!=="number" || !Number.isFinite(x) || x<0 || x>1))) {
      throw Error("Image must match model dimensions with finite pixels in [0,1]");
    }
  }
  function score(image, model, standardized=true) {
    validate(image, model);
    if (typeof standardized!=="boolean") throw Error("Invalid scoring variant");
    return image.map((row,y)=>row.map((x,i)=>{
      const k=y*model.width+i;
      return Math.abs(x-model.means[k])/(standardized?model.scales[k]:1);
    }));
  }
  function decide(heatmap, threshold) {
    if (!Number.isFinite(threshold) || threshold<0 || !Array.isArray(heatmap) ||
        !heatmap.length || !heatmap[0].length || heatmap.some(row=>
          !Array.isArray(row) || row.length!==heatmap[0].length ||
          row.some(x=>!Number.isFinite(x) || x<0))) throw Error("Invalid decision input");
    const maximum=Math.max(...heatmap.flat());
    return {maximum, anomalous:maximum>threshold,
      mask:heatmap.map(row=>row.map(x=>x>threshold))};
  }
  function perturb(base, {x,y,width,height,strength,brightness=0}) {
    if (![x,y,width,height].every(Number.isInteger) || x<0 || y<0 || width<1 || height<1 ||
        !Number.isFinite(strength) || strength<-.5 || strength>.5 ||
        !Number.isFinite(brightness) || Math.abs(brightness)>.15 ||
        !Array.isArray(base) || !base.length || !Array.isArray(base[0]) ||
        x+width>base[0].length || y+height>base.length) throw Error("Invalid perturbation");
    const mask=base.map((row,j)=>row.map((_,i)=>
      strength!==0 && j>=y && j<y+height && i>=x && i<x+width));
    const image=base.map((row,j)=>row.map((v,i)=>
      Math.min(1,Math.max(0,v+brightness+(mask[j][i]?strength:0)))));
    return {image, mask};
  }
  function iou(predicted, truth) {
    let intersection=0, union=0;
    truth.forEach((row,y)=>row.forEach((v,x)=>{
      intersection+=Number(v && predicted[y][x]);
      union+=Number(v || predicted[y][x]);
    }));
    return union ? intersection/union : null;
  }
  return {score,decide,perturb,iou};
})();
if (typeof module!=="undefined") module.exports=Anomaly;
if (typeof window!=="undefined") window.Anomaly=Anomaly;
