"""Approved two-layer foundation; dimensions are nominal, not stiffness evidence."""
import math
import numpy as np
LOWER_IDS=[2,7,13,18,29,34,45,50]
CORNER_IDS=[23,39,55,60]
REPLACED_PIN_IDS=[24,25,26,27,40,41,42,43,56,57,58,59,61,62,63,64]

def reinforce(model, base):
    """Return final base, inserted parts and connection records; preserve original IDs1..64."""
    lower_ids=LOWER_IDS;corner_ids=CORNER_IDS;removed=REPLACED_PIN_IDS
    new=[];connections=[]
    def part(name,xyz,rot,note):
     p=model.Part(name,0 if name=='2780.dat' else 14,np.array(xyz)/.4,np.array(rot),0,note);new.append(p);return p
    def movedcopy(p,dy,note):return part(p.name,p.pos*.4+[0,dy,0],p.rot,note)
    # Long 6558 end points toward -Y. Local shoulder is X=-4mm.
    PR=np.array([[0,1,0],[-1,0,0],[0,0,1.]])
    def blue(x,z,collar,note,hosts):
     p=part('6558.dat',[x,collar-4,z],PR,note);connections.append({'id':note,'xz_mm':[x,z],'axis':'Y','collar_y_mm':collar,'long_end_interval_y_mm':[collar-16,collar],'short_end_interval_y_mm':[collar,collar+8],'host_ids':hosts});return p
    for i in lower_ids:movedcopy(base[i-1],16,f'D{i:02d}')
    for i in corner_ids:movedcopy(base[i-1],16,f'C{i:02d}')
    # Middle 9L fill under radial station88..152, two spaced joints at120/152.
    for i in lower_ids:
     p=base[i-1];xy=p.pos*.4;direction=np.array([np.sign(xy[0]),0,0]) if abs(xy[0])>abs(xy[2]) else np.array([0,0,np.sign(xy[2])])
     midxy=xy+direction*16;midxy[1]=120
     mid=part('40490.dat',midxy,p.rot,f'M{i:02d}')
     for t in [120,152]:
      q=xy+direction*(t-104);blue(q[0],q[2],124,f'OUT-{i}-{t}',[f'B{i:02d}',f'M{i:02d}',f'D{i:02d}'])
    for i in removed:
     p=base[i-1];x,_,z=p.pos*.4
     # Identify the old lower beam and L among original host holes later.
     blue(x,z,116,f'REPLACE-B{i:02d}',[])
    for k in range(4):
     ang=k*math.pi/2;R=np.array([[round(math.cos(ang)),0,-round(math.sin(ang))],[0,1,0],[round(math.sin(ang)),0,round(math.cos(ang))]])
     for x,z in [(56,-32),(48,-56)]:
      q=R@np.array([x,0,z]);blue(q[0],q[2],124,f'INNER-{k}-{x}',[])
    # Four small rigid contact feet. Lower beam holes13/15, middle hole14 remains free beneath long pin.
    for i in [2,29,13,45]:
     p=base[i-1];q=p.pos*.4;direction=np.array([np.sign(q[0]),0,0]) if abs(q[0])>abs(q[2]) else np.array([0,0,np.sign(q[2])])
     footxyz=q+direction*48;footxyz[1]=136;part('32523.dat',footxyz,p.rot,f'FOOT-{i}')
     for t in [144,160]:
      v=q+direction*(t-104);v[1]=132;part('2780.dat',v,PR,f'REUSED-FOOT-PIN-{i}-{t}');connections.append({'id':f'REUSED-FOOT-PIN-{i}-{t}','xz_mm':[float(v[0]),float(v[2])],'axis':'Y','collar_y_mm':132,'long_end_interval_y_mm':[124,132],'short_end_interval_y_mm':[132,140],'host_ids':[f'D{i:02d}',f'FOOT-{i}']})
    replacements={int(p.note.removeprefix('REPLACE-B')):p for p in new if p.note.startswith('REPLACE-B')}
    final=[replacements.get(i,p) for i,p in enumerate(base,1)]+[p for p in new if not p.note.startswith('REPLACE-B')]
    assert len(final)==120 and len(new)==72 and len(connections)==48
    return final,new,connections
