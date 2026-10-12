#!/bin/sh
set -eu
r=/workspace/tool-verification/reference-recovery
g++ -std=c++20 -O1 -D_FILE_OFFSET_BITS=64 -D__WXGTK__ -I"$r/wx-dev/usr/lib/x86_64-linux-gnu/wx/include/gtk3-unicode-3.2" -I"$r/wx-dev/usr/include/wx-3.2" -I"$r/parser-source" "$r/parser-source/recover.cpp" "$r/parser-source/exceptions.cpp" "$r"/parser-source/sch_io/orcad/*.cpp /usr/lib/x86_64-linux-gnu/libwx_baseu-3.2.so.0 -o "$r/recover-dsn"
