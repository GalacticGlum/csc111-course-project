# Compile the C++ hsbg simulator from the source.
# Note: this requires git, make, g++ (>=c++17).
git clone "https://github.com/galacticglum/hearthstone-battlegrounds-simulator/" ./_temp_hsbg
cd ./_temp_hsbg
make
filename="$(find ./ -type f \( -iname "hsbg.*" -o -iname "hsbg" \))"
mkdir -p ../instance
cp "$filename" ../instance/"$filename"
cd ..
rm -rf ./_temp_hsbg