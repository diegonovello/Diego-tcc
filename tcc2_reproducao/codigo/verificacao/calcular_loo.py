import numpy as np
from scipy.optimize import minimize
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
data=json.loads((ROOT/'dados/ensaios_posicionamento_cm.json').read_text(encoding='utf8'))
target=np.array(data['teorico'][1:])
beta=np.deg2rad([[20,20,20],[-20,-20,-20],[10,20,15],[-10,-20,-15],[45,45,45],[-45,-45,-45]])
raw={name: {'c':data[key][0], 'p':data[key][1::2]} for name,key in [('sem','sem_ajuste'),('com','com_ajuste')]}
results={}

def fk(g):
    th=np.repeat(beta*g/3,3,axis=1); ph=np.cumsum(th,axis=1)
    x=5*np.sin(ph).sum(axis=1)-2*np.sin(ph[:,-1]);y=1.5+5*np.cos(ph).sum(axis=1)-2*np.cos(ph[:,-1]);return np.column_stack([x,y-44.5])

def rot(x,angle):
    c,s=np.cos(angle),np.sin(angle);return x@np.array([[c,-s],[s,c]]).T

for condition, v in raw.items():
    p=np.array(v['p']); centers=np.array(v['c']); meas=p-centers[None,:,:]; desired=target-np.array([0,44.5]);
    print('\n',condition,'model accuracy nominal mean cm',np.linalg.norm(meas-desired[:,None,:],axis=2).mean())
    def fit(train,fitg):
        def obj(z):
            angle=z[0]; g=z[1] if fitg else 1.
            prediction=fk(g)[train] if fitg else desired[train]
            resid=rot(meas[train],angle)-prediction[:,None,:]
            return np.sum(resid**2)
        ans=minimize(obj,[0,1] if fitg else [0],bounds=[(-.2,.2),(.5,1.5)] if fitg else [(-.2,.2)],method='L-BFGS-B',options={'ftol':1e-14})
        return ans.x
    results[condition]={}
    for fitg in [False,True]:
        z=fit(np.arange(6),fitg); errs=[]; angles=[]; gains=[]
        for held in range(6):
            train=np.array([i for i in range(6) if i!=held]); zz=fit(train,fitg); theta=zz[0];gain=zz[1] if fitg else 1
            model=fk(gain)[held] if fitg else desired[held]
            err=np.linalg.norm(rot(meas[held],theta)-model,axis=1)
            errs.extend(err);angles.append(theta);gains.append(gain)
        training=np.linalg.norm(rot(meas,z[0])-(fk(z[1]) if fitg else desired)[:,None,:],axis=2).mean()
        results[condition]['rotation_gain' if fitg else 'rotation']={'training':float(training),'loo':float(np.mean(errs)),'per_pose':np.array(errs).reshape(6,5).mean(axis=1).tolist(),'fit':z.tolist(),'loo_gains':gains}
        print('rotation+g' if fitg else 'rotation only','in sample',round(training,4),'LOO',round(np.mean(errs),4),'per pose',np.round(np.array(errs).reshape(6,5).mean(axis=1),3),'fit',z, 'loo g',np.round(gains,3))
# direct kinematics distal joints: 7 fixed links, joint 8 +5°, joint 9 +15°
th=np.zeros(9);th[7]=np.deg2rad(5);th[8]=np.deg2rad(15);ph=np.cumsum(th)
x=5*np.sin(ph).sum()-2*np.sin(ph[-1]);y=1.5+5*np.cos(ph).sum()-2*np.cos(ph[-1]);print('M1 direct dx,dy,norm',x,y-44.5,np.hypot(x,y-44.5))

(ROOT/'dados/reanalise/validacao_loo.json').write_text(json.dumps(results,indent=2),encoding='utf8')
