const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {spawnSync}=require('node:child_process');
const E=require('../docs/engine.js');
const bundle=JSON.parse(fs.readFileSync('docs/model.json','utf8'));
test('independent known statistics, exact tie and empty IoU',()=>{
  const model={height:1,width:1,means:[.2],scales:[Math.sqrt(.02)]};
  assert.ok(Math.abs(E.score([[.5]],model)[0][0]-.3/Math.sqrt(.02))<1e-14);
  assert.equal(E.decide([[4]],4).anomalous,false);
  assert.equal(E.decide([[4.01]],4).anomalous,true);
  assert.equal(E.iou([[false]],[[false]]),null);
});
test('reject invalid model, pixels, dimensions, thresholds and perturbations',()=>{
  for (const image of [[],[[NaN]],[[true]],[[2]],[[0,0]]]) {
    assert.throws(()=>E.score(image,{height:1,width:1,means:[0],scales:[1]}));
  }
  assert.throws(()=>E.score([[0]],{height:1,width:1,means:[0],scales:[0]}));
  for(const threshold of [NaN,Infinity,-1]) assert.throws(()=>E.decide([[0]],threshold));
  assert.throws(()=>E.perturb([[0]],{x:0,y:0,width:2,height:1,strength:.1}));
  assert.throws(()=>E.perturb([[0]],{x:0,y:0,width:1,height:1,strength:NaN}));
});
test('perturbation preserves base, exact footprint and clipping',()=>{
  const base=Array.from({length:24},()=>Array(24).fill(.9)), copy=JSON.stringify(base);
  const r=E.perturb(base,{x:2,y:3,width:4,height:4,strength:.35});
  assert.equal(r.mask.flat().filter(Boolean).length,16);
  assert.equal(r.image[3][2],1);assert.equal(r.image[0][0],.9);
  assert.equal(JSON.stringify(base),copy);
});
test('every browser residual matches Python on perturbed images for both variants',()=>{
  const model=bundle.model, image=bundle.samples[0].image;
  const source=`import json,sys\nfrom anomaly_lab import SpatialNormal\nb=json.load(sys.stdin)\nm=SpatialNormal(**b['model'])\nprint(json.dumps([m.heatmap(im,s) for im in b['images'] for s in (False,True)]))`;
  const images=[];
  for(const strength of [-.5,-.08,0,.08,.35]) for(const brightness of [-.15,0,.15]) {
    images.push(E.perturb(image,{x:8,y:10,width:4,height:4,strength,brightness}).image);
  }
  const child=spawnSync('python',['-W','error','-c',source],{input:JSON.stringify({model,images}),encoding:'utf8',maxBuffer:4000000});
  assert.equal(child.status,0,child.stderr);
  const expected=JSON.parse(child.stdout);let k=0;
  for(const im of images) for(const standardized of [false,true]) {
    const actual=E.score(im,model,standardized).flat(), ref=expected[k++].flat();
    actual.forEach((v,i)=>assert.ok(Math.abs(v-ref[i])<1e-12));
  }
});
