# Game Boy Camera frame replacer

Python script to replace the built-in frames in the Game Boy Camera rom with your own!

## Requisites
This script requires the following Python libraries:
```
python -m pip install --upgrade Pillow
python -m pip install --upgrade img2gb
```
## Usage
```
usage: gbc-fr.py [-h] -mode {copy,inject}
			[-src-rom src.gb] [-src-frame [1-18]] [-src-image frame.png]
			-dst-rom dest.gb -dst-frame [1-18]
```

Two modes are available copy or inject.

Copy allows taking frame data from one rom file and pasting into another. You specify the source rom and source frame as well as target rom and target frame.

**Copy Example**: Copy frame 2 from Japanese Pocket Camera rom onto the International rom, replacing frame 7.
```
python gbc-fr.py -mode copy -src-rom pocketcam-jp.gb -src-frame 2 -dst-rom gameboycam-intl.gb -dst-frame 7
```

Inject allows using a completely new image to replace an existing frame. You can specify the source image as a .png, .bmp and it will be converted to tile data or you can provide already formatted tile data as .bin. You will also specify the target rom and target frame.

**Inject Example**: Load tile data from supplied image onto the International rom, replacing frame 18.
```
python gbc-fr.py -mode inject -src-image cameraclub.png -dst-rom gameboycam-intl.gb -dst-frame 18
```

## Designing your frame image
Game Boy Camera frames can use up to 96 unique tiles but a frame is made up of 136 tiles so you will need to re-use or pattern some tiles. When designing your frame, you can show a grid to be aware of how many unique tiles you've used up. The script will ignore unique tiles after hitting the 96 tile limit and will re-use the last tile. The example below uses just 46 unique tiles and a re-used black tile for the rest of the frame.

![Designing with grid](docs/frame-unique-tiles.png)

## Saving your frame image
Make sure to save your image reduced down to 4 colors, this is necessary to convert to 2bpp Game Boy tile format well. **Be sure that your 4 shades have contrast or the converted result will appear with less than 4 colors.**
![Reduced color png](docs/reduced-colors.png)

## Converting your frame image
This script uses img2gb library to convert .png and .bmp source images to tile data but if you prefer to do the conversion yourself for better control over the result, you can do so using a utility like [Pic2Tiles](http://www.budmelvin.com/dev/index.html)
![Pic2Tiles](docs/pic2tiles.png)

## Usage
Your modified ROM will load into emulators but may show a warning about incorrect checksum. Eventually, your rom can be loaded onto a custom flashable Game Boy Camera cartridge once it becomes available.

## Credits
Thanks to @jkbenaim for their [gbcamextract](https://github.com/jkbenaim/gbcamextract) program which helped to figure out the frame data and tile map addresses.
Thanks to @flozz for their [img2gb](https://github.com/flozz/img2gb) library which provides tile conversion for this script.