import argparse
import binascii
from img2gb import GBTileset
from PIL import Image

from argparse import RawTextHelpFormatter
from argparse import RawDescriptionHelpFormatter

parser = argparse.ArgumentParser(description='Tool to modify standard photo frames in Game Boy Camera rom.\n\nUse inject mode to insert a frame from binary tile image file or copy mode to transfer frame data from one rom to another.', formatter_class=RawDescriptionHelpFormatter)
parser.add_argument('-mode', required=True, choices=['copy', 'inject'], default='inject', help='inject or copy')
parser.add_argument('-src-rom', metavar='src.gb', help='source rom in copy mode')
parser.add_argument('-src-frame', metavar='[1-18]', choices=range(1,19), type=int, help='frame number [1-18] from source rom in copy mode')
parser.add_argument('-src-image', metavar='frame.png', help='source image in inject mode (.png, .bmp or already formatted tile data .bin)')
parser.add_argument('-dst-rom', required=True, metavar='dest.gb', help='destination rom file')
parser.add_argument('-dst-frame', required=True, metavar='[1-18]', choices=range(1,19), type=int, help='destination frame number [1-18]')
args = parser.parse_args()

def frame_copy(source_rom, source_frame, destination_rom, destination_frame):
	try:
		sourceRom = open(source_rom, "rb")
		sourceRom.seek(850296+1672*source_frame)
		frameData = sourceRom.read(1672)
		sourceRom.close()

		destinationRom = open(destination_rom, "r+b")
		if destination_frame < 10:
			destinationRom.seek(850296+1672*destination_frame)
		else:
			destinationRom.seek(850296+16384+1672*(destination_frame-9))
		destinationRom.write(frameData)
		destinationRom.close()
	finally:
		print('destination rom modified, frame copied\n')

def frame_inject(source_image, destination_rom, destination_frame, convert_2bpp):
	try:
		# iterate through source image, find unique tiles and store list of tiles as byte arrays
		frameTiles = []
		tbMap = []
		lrMap = []
		uniqueTileIndex = 0
		currentTile = 1
		tileBytes = 16
		tbTilePositions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360]
		lrTilePositions = [41,42,61,62,81,82,101,102,121,122,141,142,161,162,181,182,201,202,221,222,241,242,261,262,281,282,301,302,59,60,79,80,99,100,119,120,139,140,159,160,179,180,199,200,219,220,239,240,259,260,279,280,299,300,319,320]

		if convert_2bpp:
			image = Image.open(source_image)
			sourceImage = GBTileset.from_image(image).tiles
			for aTile in sourceImage:
				tile = bytearray.fromhex(aTile.to_hex_string())
				# check if tile position is part of the frame
				if currentTile in tbTilePositions or currentTile in lrTilePositions:
					# check if it's a new/unique tile
					if tile not in frameTiles:
						# max of 96 unique tiles per frame
						if uniqueTileIndex < 96:
							# push unique tile index to tile map
							if currentTile in tbTilePositions:
								tbMap.append(uniqueTileIndex)
							elif currentTile in lrTilePositions:
								lrMap.append(uniqueTileIndex)
							# push tile to frame data
							frameTiles.append(tile)
							uniqueTileIndex+=1
						else:
							# once tile limit is reached, re-use first tile
							if currentTile in tbTilePositions:
								tbMap.append(95)
							elif currentTile in lrTilePositions:
								lrMap.append(95)
					else:
						# push re-used tile index  to tile map
						for i in range(len(frameTiles)):
							if frameTiles[i] == tile:
								if currentTile in tbTilePositions:
									tbMap.append(i)
								elif currentTile in lrTilePositions:
									lrMap.append(i)
				currentTile+=1
		else:
			sourceImage = open(source_image, "rb")
			sourceImage.seek(0)
			# read source image, one tile at a time
			tile = sourceImage.read(tileBytes)
			while tile:
				# check if tile position is part of the frame
				if currentTile in tbTilePositions or currentTile in lrTilePositions:
					# check if it's a new/unique tile
					if tile not in frameTiles:
						# max of 96 unique tiles per frame
						if uniqueTileIndex < 96:
							# push unique tile index to tile map
							if currentTile in tbTilePositions:
								tbMap.append(uniqueTileIndex)
							elif currentTile in lrTilePositions:
								lrMap.append(uniqueTileIndex)
							# push tile to frame data
							frameTiles.append(tile)
							uniqueTileIndex+=1
						else:
							# once tile limit is reached, re-use first tile
							if currentTile in tbTilePositions:
								tbMap.append(95)
							elif currentTile in lrTilePositions:
								lrMap.append(95)
					else:
						# push re-used tile index  to tile map
						for i in range(len(frameTiles)):
							if frameTiles[i] == tile:
								if currentTile in tbTilePositions:
									tbMap.append(i)
								elif currentTile in lrTilePositions:
									lrMap.append(i)
				# read next tile
				tile = sourceImage.read(tileBytes)
				currentTile+=1
			sourceImage.close()

		# combine tile maps
		tileMap = tbMap+lrMap

		# pad end of tile data with blank tiles if less than 96
		while len(frameTiles) < 96:
			frameTiles.append(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')

		# merge all bytes
		frameData = bytearray()
		for tile in frameTiles:
			frameData.extend(tile)
		frameData.extend(bytearray(tileMap))

		destinationRom = open(destination_rom, "r+b")
		if destination_frame < 10:
			destinationRom.seek(850296+1672*destination_frame)
		else:
			destinationRom.seek(850296+16384+1672*(destination_frame-9))
		destinationRom.write(frameData)
		destinationRom.close()
	finally:
		print('destination rom modified, frame injected\n')

if args.mode == "copy":
	frame_copy(args.src_rom, args.src_frame, args.dst_rom, args.dst_frame)
else:
	if args.src_image.endswith('bin'):
		frame_inject(args.src_image, args.dst_rom, args.dst_frame, False)
	elif args.src_image.endswith('png') or args.src_image.endswith('bmp'):
		frame_inject(args.src_image, args.dst_rom, args.dst_frame, True)
	else:
		print('-src-image can be .png, .bmp or already converted .bin (2bpp)')