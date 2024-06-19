# unifi-events-rtsp
A script to host 3x RTSP streams, showing the latest event snapshots from unifi protect

# Installation
You MUST compile opencv from source with gstreamer support [https://github.com/bluenviron/mediamtx?tab=readme-ov-file#opencv](https://github.com/bluenviron/mediamtx?tab=readme-ov-file#opencv)

```shell
sudo apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev gstreamer1.0-plugins-ugly gstreamer1.0-rtsp python3-dev python3-numpy
git clone --depth=1 -b 4.5.4 https://github.com/opencv/opencv
cd opencv
mkdir build && cd build
cmake -D CMAKE_INSTALL_PREFIX=/usr -D WITH_GSTREAMER=ON ..
make -j$(nproc)
sudo make install
```

todo..
