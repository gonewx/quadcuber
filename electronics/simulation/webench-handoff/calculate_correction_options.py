from pathlib import Path
import json
D=Path(__file__).resolve().parent
rows=[]
for b,t in [(13.3,.01),(13.3,.001),(13.7,.01),(13.7,.001),(13.5,.001)]:
 rows.append(dict(top_kohm=100,bottom_kohm=b,initial_tolerance=t,min_V=.581*(1+100*(1-t)/(b*(1+t))),typ_V=.596*(1+100/b),max_V=.611*(1+100*(1+t)/(b*(1-t)))))
lo=(1-.001)*(1-.0025);hi=(1+.001)*(1+.0025)
out={'scope':'Independent static corners only; not full system PVT or transient guarantee','rows':rows,'same_ratio_0p1_temperature_example':{'delta_C':100,'each_TCR_ppm_C':25,'min_V':.581*(1+100*lo/(13.3*hi)),'max_V':.611*(1+100*hi/(13.3*lo))},'Cmin_uF_at_4p75V':5.1/(4.75*40000)*1e6}
(D/'minimal-correction-numbers.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
