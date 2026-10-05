"""真实零件试装模型：矩形骨架、双导轨与厚滑块。仅设计候选。"""
from pathlib import Path
import sys,math,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/lego/v3'))
import model as m
import mesh_clearance as mesh
import run_check,check,fcl
m.CATALOG.update({'39794.dat':('11x7整体框架','solid'),'39793.dat':('3x3九孔厚连接块','solid'),'32184.dat':('三孔垂直接头','solid'),'60484.dat':('3x3T形粗梁','solid'),'60485.dat':('9号轴','axle'),'3737.dat':('10号轴','axle'),'3705.dat':('4号轴','axle'),'23948.dat':('11号轴','axle')})
m.CONNECTOR_LEN.update({'60485.dat':180,'3737.dat':200,'3705.dat':80,'23948.dat':220});check.CONNECTOR_LEN.update(m.CONNECTOR_LEN)
C0=m.CROSS_CLOSED_X
OPEN_S=C0-m.cross_x_for_beta(m.OPEN_BETA)
# 原构造器仅用于后部舵机与固定支架；允许其生成新直线行程的端点。
m.OPEN_S=OPEN_S
BASE_MODULE=m.module
TALL=m.orient('+z','-x','-y')
WIDE=m.orient('+y','-x','+z')
SLIDER_ROT=m.orient('+x','+z','-y')
END_ROT=m.orient('+y','+z','+x')
BUSH_Y=m.orient('+x','-z','+y')

def beta(s):
 c=C0-s;dx=m.PIVOT_X-c;r=math.hypot(dx,m.JAW_Y)
 return math.atan2(m.JAW_Y,dx)-math.acos((r*r+m.JAW_A**2-m.LINK_L**2)/(2*m.JAW_A*r))

def head(stroke=0.):
 out=[];c=C0-stroke;b=beta(stroke)
 def a(n,p,r,note,col=71):
  q=m.Part(n,col,p,r,1,note);q.head=True;out.append(q);return q
 def bush(p,r,note='固定轴套',half=False):return a('32123a.dat' if half else '3713.dat',p,r,note,72)
 def pin(p,r,note):return a('2780.dat',p,r,note,0)
 a('18938.dat',m.TT_C,m.TT_ROT,'转盘上半')
 a('64179.dat',[-270,0,0],TALL,'后整体框',1)
 a('39793.dat',[-90,0,0],SLIDER_ROT,'前固定导轨块',1)
 for sz in (-1,1):
  a('64179.dat',[-190,0,100*sz],m.FRAME_XY_LONG_X,'侧整体框',1)
  for y in (-40,40):
   a('32316.dat',[-210,y,80*sz],m.BEAM_X_HOLES_Z,'侧承重直梁',72)
   # 后框经短垫梁接侧框；根部贯穿轴连接内外立梁。
   a('43857.dat',[-260,y,60*sz],m.BEAM_X_HOLES_Z,'后框侧垫梁',72)
   pin([-270,y,50*sz],m.ALONG_Z,'后框连接销')
   a('6558.dat',[-250,y,80*sz],m.ALONG_Z if sz>0 else m.LPIN_SHORT_Z,'后框侧垫梁销',1)
   pin([-170,y,90*sz],m.ALONG_Z,'侧框固定销')
   a('43857.dat',[-130,y-np.sign(y)*10,60*sz],m.BEAM_Y_HOLES_Z,'根架间隔梁',72)
   a('32073.dat',[-130,y,70*sz],m.ALONG_Z,'根架贯穿轴',0)
   for zz in (25,115):bush([-130,y,zz*sz],m.BUSH_Z,'根架贯穿轴限位',True)
  a('32525.dat',[-130,0,80*sz],m.BEAM_Y_HOLES_Z,'夹指根立梁',71)
  a('32525.dat',[-130,0,40*sz],m.BEAM_Y_HOLES_Z,'根轴内侧支承梁',71)
  a('60484.dat',[-90,0,20*sz],m.orient('-y','+z','-x'),'前导轨T支板',1)
  for y in (-20,20):a('6558.dat',[-130,y,40*sz],m.ALONG_Z if sz>0 else m.LPIN_SHORT_Z,'导轨支板固定销',1)
  a('32523.dat',[-150,0,60*sz],m.BEAM_X_HOLES_Z,'中梁延长梁',72)
  for x in (-170,-150):pin([x,0,70*sz],m.ALONG_Z,'中梁延长固定销')
  a('6558.dat',[-130,0,60*sz],m.ALONG_Z if sz>0 else m.LPIN_SHORT_Z,'中梁根架长销',1)
  # T形梁一件跨接转盘两个孔和中间直梁两个孔；不靠两个短摇臂定形。
  a('60484.dat',[-250,0,60*sz],m.orient('-y','+z','-x'),'转盘T形接口梁',72)
  a('32524.dat',[-210,0,80*sz],m.BEAM_X_HOLES_Z,'中间承重直梁',72)
  for y in (-20,20):
   pin([-290,y,50*sz],m.ALONG_Z,'转盘接口销')
  a('6558.dat',[-270,0,60*sz],m.ALONG_Z if sz>0 else m.LPIN_SHORT_Z,'后框中梁长销',1)
  pin([-250,0,70*sz],m.ALONG_Z,'T梁中梁固定销')
 for x in (-110,-90):a('6558.dat',[x,0,0],m.ALONG_Z,'前导轨块固定销',1)
 # 导轨端座：同一根贯穿Y轴穿两只32184。两根平行轴分开40LDU，固定端座朝向。
 for x,span,axname,fill in [(-270,60,'3707.dat',(-40,0,40))]:
  for sy in (-1,1):
   a('32184.dat',[x,20*sy,0],END_ROT,'导轨固定孔座',72)
  for z in (-20,20):
   a(axname,[x,0,z],m.ALONG_Y,'端座贯穿定位轴',0)
   for y in fill:bush([x,y,z],BUSH_Y,'端座内隔套')
   if x==-270:
    for y in (-75,75):bush([x,y,z],BUSH_Y,'后端座外限位',True)
 # 11L导轨穿后座与前固定厚块，轴向限位在两座内侧。
 for y in (-20,20):
  a('23948.dat',[-170,y,0],m.ALONG_X,'承重导轨',0)
  for x in (-255,-125):bush([x,y,0],m.BUSH_X,'导轨内限位',True)
 a('39793.dat',[c+20,0,0],SLIDER_ROT,'承重滑块',14)
 # 输入公共轴在厚滑块后排圆孔，不是滑块中心。
 a('44294.dat',[c,0,0],m.ALONG_Z,'输入公共轴',0)
 for sz in (-1,1):
  bush([c,0,65*sz],m.BUSH_Z,'输入公共轴外限位',True)
  sy=sz
  piv=np.array([-130,80*sy,0.]);R=m.rot_z(b*sy)
  joint=piv+R@np.array([-40.,0.,0.]);v=joint-np.array([c,0,0]);v/=np.linalg.norm(v)
  # 上下夹指各用左右对称的两根杆，消除名义夹紧力造成的滚转力偶。
  layer=30 if sy<0 else 50
  for side in (-1,1):
   a('32316.dat',(joint+np.array([c,0,0]))/2+[0,0,layer*side],m.orient(np.cross([0,0,1.],v),'+z',v),'输入粗连杆',25)
   if layer==50:bush(joint+[0,0,20*side],m.BUSH_Z,'输入关节间隔')
   bush(joint+[0,0,(layer-15)*side],m.BUSH_Z,'输入关节内半隔套',True)
   bush(joint+[0,0,(layer+15)*side],m.BUSH_Z,'输入关节外限位',True)
  a('32073.dat' if layer==30 else '44294.dat',joint,m.ALONG_Z,'输入关节轴',0)
  # 与原方案相同接触点；最近的根轴支承仍在两侧立梁z±40。
  a('32524.dat',piv,R@m.BEAM_X_HOLES_Z,'夹指主梁',4)
  a('3737.dat',piv,m.ALONG_Z,'夹指根轴',0)
  for z in (-20,20):bush(piv+[0,0,z],m.BUSH_Z,'夹指根轴内隔套')
  for z in (-95,95):bush(piv+[0,0,z],m.BUSH_Z,'夹指根轴外限位',True)
  br=m.orient('+x',[0,0,sy],[0,-sy,0])
  for side in (-1,1):
   for z in (55,65):a('32056.dat',[-130,sy*120,side*z],br,'防翻折限位架',71)
   a('6558.dat',[-130,sy*100,side*60],m.ALONG_Z if side>0 else m.LPIN_SHORT_Z,'限位架固定销',1)
  a('3707.dat',[-90,sy*120,0],m.ALONG_Z,'开限位挡轴',0)
  for z in (-75,75):bush([-90,sy*120,z],m.BUSH_Z,'开限位挡轴轴套',True)
  front=piv+R@np.array([100.,0,0])
  for z in (-15,15):a('32449.dat',piv+R@np.array([70.,0,z]),R@m.BEAM_X_HOLES_Z,'压头支承薄梁',4)
  a('4519.dat',piv+R@np.array([40.,0,0]),R@m.ALONG_Z,'薄梁固定轴',0)
  for z in (-25,25):bush(piv+R@np.array([40.,0,z]),R@m.BUSH_Z,'薄梁固定轴限位',True)
  a('32054.dat',piv+R@np.array([60.,0,-10]),R@m.ALONG_Z,'薄梁固定挡套销',4)
  a('32062.dat',front,R@m.ALONG_Z,'轮毂贯穿轴',0)
  a('42610.dat',front,R,'轮毂',71);a('50945_nominal.dat',front,R,'橡胶胎',0)
 # 2孔薄梁两端十字孔；本处为直线输入的固定长度联接，未使用全圆孔薄梁。
 d=c-20
 for z in (-15,15):a('41677.dat',[d,0,z],m.BEAM_X_HOLES_Z,'推杆短接片',22)
 a('32013.dat',[d,0,0],m.CROSSHEAD_ROT,'推杆铰接头',72)
 a('4519.dat',[d,0,0],m.ALONG_Z,'推杆铰轴',0)
 for z in (-25,25):bush([d,0,z],m.BUSH_Z,'推杆铰轴外限位',True)
 a('50451.dat',[d-170,0,0],m.ALONG_X,'一体推杆',0)
 return out

def module(open_s=0.,angle=0.,steps=False,on_base=False):
 old=BASE_MODULE(open_s,steps=False,on_base=on_base)
 fixed=[p for p in old if not p.head or (p.head and p.name=='32123a.dat' and not p.note and p.pos[0]<-350)]
 for p in fixed:
  if p.head and angle:
   p.pos=m.rot_x(angle)@p.pos;p.rot=m.rot_x(angle)@p.rot
 out=fixed+[p.moved(m.rot_x(angle),[m.MODULE_DX,0,0]) for p in head(open_s)]
 return out

def scan(n=11):
 hits={};checks={};queries=0
 for frac in np.linspace(0,1,n):
  ps=module(float(frac*OPEN_S));bb=[check._obb(p) for p in ps]
  if frac in (0.,1.):checks[str(frac)]={k:f(ps) for k,f in [('孔型',run_check.pins_in_axle_holes),('销深',run_check.pin_depth),('长销',check.long_pins)]}
  for i,a in enumerate(ps):
   for j in range(i+1,len(ps)):
    b=ps[j]
    if not(a.head or b.head):continue
    lo,hi=bb[i];low,high=bb[j]
    if np.any(np.minimum(hi,high)-np.maximum(lo,low)<=1e-7):continue
    if mesh.fitting(a,b):continue
    queries+=1;dist=fcl.distance(mesh.obj(a),mesh.obj(b),fcl.DistanceRequest(),fcl.DistanceResult())
    if dist<=1e-8:
     if nominal_contact(a,b):continue
     key=(a.name,a.note,b.name,b.note)
     hits.setdefault(key,{'frac':float(frac),'positions':[a.pos.tolist(),b.pos.tolist()]})
 return {'states':n,'queries':queries,'connections':checks,'hits':[{'pair':k,**v} for k,v in hits.items()]}

def nominal_contact(a,b):
 """仅检验指定固定框架贴合面；分离1e-4后须得到同样大小的距离。"""
 tt,part=(a,b) if a.note=='转盘上半' else (b,a)
 if tt.note=='转盘上半' and part.note=='转盘T形接口梁':
  v=np.array([0.,0.,np.sign(part.pos[2])*1e-4])
  return fcl.distance(mesh.obj(tt),mesh.obj(part.moved(m.I,v)),fcl.DistanceRequest(),fcl.DistanceResult())>=.999e-4
 frame,beam=(a,b) if a.note in ('后整体框','前整体框') else (b,a)
 if frame.note not in ('后整体框','前整体框'):return False
 v=np.zeros(3)
 if beam.note=='导轨座横梁' or (frame.note=='后整体框' and beam.note=='端座内隔套'):v[1]=-np.sign(beam.pos[1])*1e-4
 elif frame.note=='前整体框' and beam.note in ('侧承重直梁','中间承重直梁'):v[2]=-np.sign(beam.pos[2])*1e-4
 else:return False
 dist=fcl.distance(mesh.obj(frame),mesh.obj(beam.moved(m.I,v)),fcl.DistanceRequest(),fcl.DistanceResult())
 return dist>=.999e-4
if __name__=='__main__':
 out=Path(__file__).parent
 (out/'boxed-slider.ldr').write_text(m.to_ldr(module(),'矩形框架滑座候选，实物承载待测'))
 r=scan(81);(out/'boxed-check.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False,indent=2))
