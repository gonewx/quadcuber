"""Native-mesh projections and dimensioned candidate diagram, not assembly release."""
from pathlib import Path
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/tray-mpl-cache')
import numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties
import probe as p
FONT=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
plt.rcParams.update({'font.size':10,'axes.titleweight':'bold','figure.facecolor':'#f5f6f8','axes.facecolor':'white'})
def txt(ax,x,y,s,**kw):return ax.text(x,y,s,fontproperties=FONT,**kw)
def native(ax,parts,axes,color,alpha=1):
 for part in parts:
  vs=p.c.world(part)[:,:,axes]
  ax.add_collection(PolyCollection(vs,facecolors=color,edgecolors='none',alpha=alpha,rasterized=True))
def setup(ax,title,xlab,ylab,xlim,ylim):
 ax.set_aspect('equal');ax.set_xlim(*xlim);ax.set_ylim(*ylim)
 ax.set_title(title,fontproperties=FONT,pad=12);ax.set_xlabel(xlab);ax.set_ylabel(ylab);ax.grid(alpha=.18)
fig,axs=plt.subplots(2,2,figsize=(15,13))
a=axs[0,0];setup(a,'A  推荐：水平装料 + 低位可撤推靠工具','X / mm','Z / mm',(-92,62),(-122,55))
a.add_patch(Rectangle((-28,-28),56,56,facecolor='#fff2cb',edgecolor='#ac8421',lw=2))
core=[q for q in p.c.core_parts() if q.note in ('x_locator_upper_bar','z_locator_positiveZ_L')]
native(a,core,[0,2],'#237eab')
heads=[q for q in p.arms() if q.head and q.note=='橡胶胎'];native(a,heads,[0,2],'#343e48')
native(a,p.TOOL,[0,2],'#df8128',.95)
native(a,p.moved(p.TOOL,[-2,0,-82]),[0,2],'#df8128',.2)
a.annotate('',xy=(-28,-28),xytext=(-44,-44),arrowprops={'arrowstyle':'->','color':'#b45111','lw':2})
a.annotate('',xy=(-33.6,-111),xytext=(-33.6,-76),arrowprops={'arrowstyle':'->','color':'#b45111','lw':2})
txt(a,-17,2,'56 mm 魔方',ha='center');txt(a,30,30,'原 +X / +Z 基准边',color='#237eab')
txt(a,-88,-95,'先退出 (-2,-2) mm\n再沿 -Z 撤出 80 mm',color='#b45111')
txt(a,-88,45,'黑：水平轮胎投影\n橙：四件定位工具（在轮胎下方）',fontsize=9)
a=axs[0,1];setup(a,'B  工具高度与夹头分离（侧面投影）','X / mm','Y / mm (down)',(-60,60),(56,-36))
a.add_patch(Rectangle((-28,-28),56,56,facecolor='#fff2cb',edgecolor='#ac8421',lw=2))
native(a,[q for q in p.c.core_parts() if q.note.startswith('seat_')],[0,1],'#8897a5',.45)
native(a,heads,[0,1],'#343e48');native(a,p.TOOL,[0,1],'#df8128',.95)
a.axhline(28,color='#237eab',ls='--',lw=1)
txt(a,30,26,'托面 Y=28',color='#237eab',fontsize=9)
txt(a,-59,-33,'推靠工作带 Y=20…28\n手柄在下层 Y=28…36\n工具整体高度 ±2 mm 已作包络检查',fontsize=9,va='top')
a=axs[1,0];setup(a,'C  工具孔位与装配（俯视）','X / mm','Z / mm',(-49,0),(-84,25))
native(a,p.TOOL[:1],[0,2],'#f3b362');native(a,p.TOOL[1:2],[0,2],'#a85a21',.65)
for z in [-31.6,-23.6]:
 a.scatter([-31.6],[z],s=55,color='#17283d',zorder=6)
 a.annotate('2780',(-31.6,z),xytext=(-19,z-5),arrowprops={'arrowstyle':'-','color':'#17283d'},fontsize=9)
txt(a,-47,22,'32526 厚3×5直角梁 ×1\n32524 厚7L梁 ×1\n2780 摩擦销 ×2',fontsize=9,va='top')
txt(a,-47,-80,'孔距8 mm；两销防手柄转动\n无全圆孔薄梁；不固定在托盘上',fontsize=9)
a=axs[1,1];setup(a,'D  原竖直装料：实际网格相交，不能硬夹','X / mm','Y / mm (down)',(8,55),(56,12))
vert=[q for q in p.arms(0) if q.arm=='R' and q.head and q.note=='橡胶胎' and q.pos[1]>0]
native(a,[q for q in p.c.core_parts() if q.note in ('seat_H','seat_deck_0','seat_middle_deck_pin_16')],[0,1],'#8598a6',.6)
native(a,vert,[0,1],'#c44542',.8)
a.plot([27.525],[31.425],'ko');txt(a,29,31,'相交点',fontsize=9)
txt(a,9,52,'移除中央梁仍有H座/销/夹指支架问题。\n因此本候选不改成竖直上位装料。',fontsize=9)
fig.suptitle('本地候选：几何通过不等于重复定位或承重验收',fontproperties=FONT,fontsize=19,y=.98)
fig.text(.5,.018,'全部尺寸为名义毫米；只允许支承承重下定位检查。禁止据此降盘、撤支承或自动翻转。',ha='center',fontproperties=FONT,fontsize=11,color='#a03330')
fig.tight_layout(rect=[0,.045,1,.955]);fig.savefig(p.OUT/'candidate.png',dpi=155);fig.savefig(p.OUT/'candidate.pdf');plt.close(fig)
print(p.OUT/'candidate.png')
