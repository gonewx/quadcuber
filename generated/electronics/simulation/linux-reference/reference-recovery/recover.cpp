#include <fstream>
#include <iostream>
#include <iomanip>
#include <iterator>
#include <wx/log.h>
#include <ki_exception.h>
#include <sch_io/orcad/orcad_library.h>
#include <sch_io/orcad/orcad_page.h>
#include <sch_io/orcad/orcad_cache.h>
std::vector<char> read(const std::string& p) { std::ifstream f(p, std::ios::binary); if(!f) throw std::runtime_error(p); return {std::istreambuf_iterator<char>(f), {}}; }
int main(int argc,char**argv) {
 try {
  wxLog::AddTraceMask("KICAD_ORCAD_IO");
  auto l=OrcadParseLibrary(read(std::string(argv[1])+"/Library.bin"));
  std::cout<<"LIBRARY "<<l.versionMajor<<' '<<l.versionMinor<<' '<<l.strings.size()<<' '<<std::quoted(l.schematicName)<<'\n';
  auto warn=[](const wxString& s){std::cerr<<"WARNING "<<s.ToStdString()<<'\n';};
  ORCAD_DIALECT d{l.versionMajor<3,l.versionMajor<2};
  std::map<std::string, ORCAD_SYMBOL_DEF> symbols;
  std::map<std::string, ORCAD_PACKAGE> packages;
  OrcadParseCache(read(std::string(argv[1])+"/Cache.bin"),l.strings,warn,symbols,packages,ORCAD_DIALECT{l.versionMajor<3,false});
  for(const auto&[name,p]:packages) {
   std::cout<<"PACKAGE "<<std::quoted(name)<<" variants="<<p.variants.size()<<'\n';
   for(const auto&[k,v]:p.props)std::cout<<"PKGPROP "<<std::quoted(k)<<' '<<std::quoted(v)<<'\n';
   for(const auto&device:p.devices) {std::cout<<"DEVICE "<<std::quoted(device.unitRef)<<' '<<std::quoted(device.refDes);for(const auto&n:device.pinNumbers)std::cout<<' '<<std::quoted(n);std::cout<<'\n';}
   for(const auto&v:p.variants){std::cout<<"PACKAGE_VARIANT "<<std::quoted(name)<<'\n';for(const auto&[k,x]:v.props)std::cout<<"VARPROP "<<std::quoted(k)<<' '<<std::quoted(x)<<'\n';for(const auto&device:v.devices){std::cout<<"VARDEVICE";for(const auto&n:device.pinNumbers)std::cout<<' '<<std::quoted(n);std::cout<<'\n';}}
  }
  for(const auto&[name,s]:symbols) {
   std::cout<<"SYMBOL "<<std::quoted(name)<<" variants="<<s.variants.size()<<'\n';
   for(const auto&[k,v]:s.props) std::cout<<"SYMPROP "<<std::quoted(k)<<' '<<std::quoted(v)<<'\n';
   for(const auto&p:s.pins) std::cout<<"SYMPIN "<<p.position<<' '<<std::quoted(p.name)<<'\n';
   for(const auto&v:s.variants){std::cout<<"SYMBOL_VARIANT "<<std::quoted(name)<<'\n';for(const auto&[k,x]:v.props)std::cout<<"VARPROP "<<std::quoted(k)<<' '<<std::quoted(x)<<'\n';for(const auto&p:v.pins)std::cout<<"VARPIN "<<p.position<<' '<<std::quoted(p.name)<<'\n';}
  }
  for(auto name:{"Startup","Steady_State"}) {
   auto occurrence=OrcadReadOccurrenceTree(read(std::string(argv[1])+"/"+name+"-Hierarchy.bin"),l.strings,warn,d);
   std::cout<<"OCCURRENCE "<<name<<" refs="<<occurrence.partRefs.size()<<" props="<<occurrence.partProps.size()<<" blocks="<<occurrence.blocks.size()<<'\n';
   for(const auto&[id,n]:occurrence.partRefs)std::cout<<"OCCREF "<<id<<' '<<std::quoted(n)<<'\n';
   for(const auto&[id,props]:occurrence.partProps)for(const auto&[k,v]:props)std::cout<<"OCCPROP "<<id<<' '<<std::quoted(k)<<' '<<std::quoted(v)<<'\n';
   auto p=OrcadParsePage(read(std::string(argv[1])+"/"+name+".bin"),l.strings,warn,d);
   std::cout<<"PAGE "<<name<<" instances="<<p.instances.size()<<" wires="<<p.wires.size()<<" globals="<<p.globals.size()<<" nets="<<p.netmap.size()<<'\n';
   std::cout<<"PAGE_OTHER ports="<<p.ports.size()<<" offpage="<<p.offpage.size()<<" blocks="<<p.blocks.size()<<" buses="<<p.busEntries.size()<<" groups="<<p.netGroups.size()<<" graphics="<<p.graphics.size()<<" titleblocks="<<p.titleBlocks.size()<<'\n';
   for(const auto&[k,v]:p.props)std::cout<<"PAGEPROP "<<std::quoted(k)<<' '<<std::quoted(v)<<'\n';
   for(const auto&[id,n]:p.netmap)std::cout<<"NET "<<id<<' '<<std::quoted(n)<<'\n';
   for(const auto&w:p.wires)std::cout<<"WIRE "<<w.id<<' '<<w.x1<<' '<<w.y1<<' '<<w.x2<<' '<<w.y2<<'\n';
   for(const auto&i:p.instances) {
    std::cout<<"INSTANCE "<<i.dbId<<' '<<std::quoted(i.reference)<<' '<<std::quoted(i.value)<<' '<<std::quoted(i.pkgName)<<' '<<i.unitIndex<<'\n';
    for(const auto&[k,v]:i.props)std::cout<<"PROP "<<std::quoted(k)<<' '<<std::quoted(v)<<'\n';
    for(const auto&pin:i.pins)std::cout<<"PIN "<<pin.pinIndex<<' '<<pin.x<<' '<<pin.y<<' '<<pin.wordA<<' '<<pin.wordB<<'\n';
   }
   for(const auto&g:p.globals)std::cout<<"GLOBAL "<<std::quoted(g.logicalName)<<' '<<g.x<<' '<<g.y<<'\n';
  }
 }catch(const std::exception&e){std::cerr<<"ERROR "<<e.what()<<'\n';return 1;}
}
