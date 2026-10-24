/** Zero-dependency reference only. This is a simplified geometry/beam screening utility,
 *  NOT a field-validated centralizer placement model nor a standards implementation.
 *  In every client report, describe its assumptions and limits. */
const finite = (x,name)=>{if(!Number.isFinite(x))throw new RangeError(name+' must be finite');return x;};
export const inchToM = (x)=>finite(x,'inch')*0.0254;
export const ftToM = (x)=>finite(x,'ft')*0.3048;
export const lbfToN = (x)=>finite(x,'lbf')*4.4482216152605;
export function radialClearance(holeODm,casingODm) {
  finite(holeODm,'holeODm');finite(casingODm,'casingODm');
  if (!(holeODm>casingODm && casingODm>0)) throw new RangeError('holeID must exceed positive casing OD');
  return (holeODm-casingODm)/2;
}
export function offsetStandoffRatio(holeODm,casingODm,offsetM) {
  const c=radialClearance(holeODm,casingODm); finite(offsetM,'offsetM');
  if(offsetM < -1e-12 || offsetM > c + 1e-12) throw new RangeError('center offset must be within annular clearance');
  return Math.max(0, Math.min(1, 1-offsetM/c));
}
export function rigidContactSOR(holeODm,casingODm,rigidODm) {
  radialClearance(holeODm,casingODm);finite(rigidODm,'rigidODm');
  if(rigidODm<casingODm || rigidODm>holeODm)throw new RangeError('incompatible rigid effective OD');
  return (rigidODm-casingODm)/(holeODm-casingODm);
}
export function pipeSecondMoment(odM,idM) {
  finite(odM,'odM');finite(idM,'idM');
  if(!(odM>idM && idM>0))throw new RangeError('casing OD must exceed positive ID');
  return Math.PI*(odM**4-idM**4)/64;
}
export function buoyedWeightNPerM(massKgPerM,fluidDensityKgPerM3,steelDensityKgPerM3=7850) {
  [massKgPerM,fluidDensityKgPerM3,steelDensityKgPerM3].forEach((v,i)=>finite(v,'density/mass'+i));
  if(massKgPerM<=0||fluidDensityKgPerM3<0||steelDensityKgPerM3<=0)throw new RangeError('invalid density/mass');
  return massKgPerM*9.80665*(1-fluidDensityKgPerM3/steelDensityKgPerM3);
}
export function simpleBeamSagM(qNPerM,spacingM,EI_Nm2) {
  [qNPerM,spacingM,EI_Nm2].forEach((v,i)=>finite(v,'sag input'+i));
  if(qNPerM<0||spacingM<=0||EI_Nm2<=0)throw new RangeError('invalid simple beam input');
  return 5*qNPerM*spacingM**4/(384*EI_Nm2);
}
export function midspanScreeningSOR(sorLeft,sorRight,sagM,clearanceM) {
  [sorLeft,sorRight,sagM,clearanceM].forEach((v,i)=>finite(v,'midspan input'+i));
  if(sorLeft<0||sorLeft>1||sorRight<0||sorRight>1||sagM<0||clearanceM<=0)throw new RangeError('invalid support/sag/clearance');
  return Math.max(0,Math.min(sorLeft,sorRight)-sagM/clearanceM);
}
export function interpolateStandoffAtLoad(curve,loadN){
  finite(loadN,'loadN');if(loadN<0||!Array.isArray(curve)||curve.length<2)return null;
  const arr=curve.map(p=>({loadN:p.loadN,sor:p.sor})).sort((a,b)=>a.loadN-b.loadN);
  for(let i=0;i<arr.length;i++){
    const p=arr[i]; if(!Number.isFinite(p.loadN)||!Number.isFinite(p.sor)||p.loadN<0||p.sor<0||p.sor>1) return null;
    if(i>0 && (p.loadN<=arr[i-1].loadN || p.sor>arr[i-1].sor)) return null;
  }
  if(loadN<arr[0].loadN||loadN>arr[arr.length-1].loadN)return null;
  for(let i=0;i<arr.length-1;i++){
    let a=arr[i],b=arr[i+1];
    if(loadN>=a.loadN&&loadN<=b.loadN){let w=(loadN-a.loadN)/(b.loadN-a.loadN);return a.sor+w*(b.sor-a.sor);}
  }
  return null;
}
export function doglegRad(i1Deg,a1Deg,i2Deg,a2Deg){
  for(const v of [i1Deg,a1Deg,i2Deg,a2Deg])finite(v,'survey angle');
  for(const v of [i1Deg,i2Deg])if(v<0||v>180)throw new RangeError('inclination out of range');
  for(const v of [a1Deg,a2Deg])if(v<0||v>360)throw new RangeError('azimuth out of range');
  const r=Math.PI/180,I1=i1Deg*r,I2=i2Deg*r,A1=a1Deg*r,A2=a2Deg*r;
  const x=Math.cos(I1)*Math.cos(I2)+Math.sin(I1)*Math.sin(I2)*Math.cos(A2-A1);
  return Math.acos(Math.max(-1,Math.min(1,x)));
}
export function dlsDegreesPer30m(station1,station2){
  if(!Number.isFinite(station1.mdM)||!Number.isFinite(station2.mdM)||station2.mdM<=station1.mdM)throw new RangeError('MD must increase');
  const angle=doglegRad(station1.incDeg,station1.aziDeg,station2.incDeg,station2.aziDeg);
  return angle*180/Math.PI*30/(station2.mdM-station1.mdM);
}
