#!/bin/sh
set -eu
export PATH=/workspace/tools/xyce-deps/usr/bin:$PATH
export BISON_PKGDATADIR=/workspace/tools/xyce-deps/usr/share/bison
export M4=/workspace/tools/xyce-deps/usr/bin/m4
/workspace/tools/cmake-python/cmake/data/bin/cmake \
 -S /workspace/tools/src/xyce-7.10 -B /workspace/tools/build/xyce-7.10 \
 -DCMAKE_INSTALL_PREFIX=/workspace/tools/xyce-7.10 \
 -DCMAKE_BUILD_TYPE=Release \
 -DTrilinos_ROOT=/workspace/tools/trilinos-14.4 \
 -DFLEX_EXECUTABLE=/workspace/tools/xyce-deps/usr/bin/flex \
 -DFLEX_INCLUDE_DIR=/workspace/tools/xyce-deps/usr/include \
 -DBISON_EXECUTABLE=/workspace/tools/xyce-deps/usr/bin/bison \
 -DXyce_ADMS_MODELS=OFF -DXyce_NEURON_MODELS=OFF -DXyce_USE_CURL=OFF -DXyce_TRACKING_URL= -DXyce_USE_FFT=OFF
