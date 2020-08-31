# Game Boy Camera frame replacer

Python script to replace the built-in frames in the Game Boy Camera rom with your own!

```
usage: gbc-fr.py [-h] -mode {copy,inject} [-src-rom src.gb]
                 [-src-frame [1-18]] [-src-image frame.bin] -dst-rom dest.gb
                 -dst-frame [1-18]
```

Two modes are available copy or inject.

Copy allows taking frame data from one rom file and pasting into another. You specify the source rom and source frame as well as target rom and target frame.

**Copy Example**: Copy frame 2 from Japanese Pocket Camera rom onto the International rom, replacing frame 7.
```
python gbc-fr.py -mode copy -src-rom pocketcam-jp.gb -src-frame 2 -dst-rom gameboycam-intl.gb -dst-frame 7
```

Inject allows using a completely new image to replace an existing frame. You specify the source image in (2bpp binary tile format) as well as the target rom and target frame.

**Inject Example**: Load tile data from supplied image onto the International rom, replacing frame 18.
```
python gbc-fr.py -mode inject -src-image cameraclub.bin -dst-rom gameboycam-intl.gb -dst-frame 18
```

## Designing your frame image
Game Boy Camera frames can use up to 96 unique tiles but a frame is made up of 136 tiles so you will need to re-use or pattern some tiles. When designing your frame, you can show a grid to be aware of how many unique tiles you've used up. The script will ignore unique frames after hitting the 96 tile limit and will re-use the first tile. The example below uses just 46 unique tiles and a re-used black tile for the rest of the frame.

![Designing with grid](docs/frame-unique-tiles.png)

## Saving your frame image
Make sure to save your image reduced down to 4 colors, this is necessary to convert to 2bpp Game Boy tile format.
![Reduced color png](docs/reduced-colors.png)

## Converting your frame image
Since this script accepts already tile formatted images, you will need to use a utility like [Pic2Tiles](http://www.budmelvin.com/dev/index.html) to do the conversion. Pic2Tiles accepts 4 color paletted images and allows saving as binary 2bpp format. Choose **binary** as the format in the application window. *Hoping to build tile conersion into this script later and eliminate this step.*
![Pic2Tiles](docs/pic2tiles.png)

## Usage
Your modified ROM will load into emulators but may show a warning about incorrect checksum. Eventually, your rom can be loaded onto a custom flashable Game Boy Camera cartridge once it becomes available.

## Credits
Thanks to @jkbenaim for his [gbcamextrac](https://github.com/jkbenaim/gbcamextract) program which helped to figure out the frame data and map tile addresses. 