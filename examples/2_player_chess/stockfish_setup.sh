curl -JLO https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-android-armv8.tar
tar -xvf stockfish-android-armv8.tar
cd stockfish/src
make build ARCH=x86-64
