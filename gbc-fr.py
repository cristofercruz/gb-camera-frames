import argparse
import binascii
from img2gb import GBTileset
from PIL import Image

from argparse import RawTextHelpFormatter
from argparse import RawDescriptionHelpFormatter

parser = argparse.ArgumentParser(description='Tool to modify standard photo frames in Game Boy Camera rom.\n\nUse inject mode to insert a frame from binary tile image file or copy mode to transfer frame data from one rom to another.', formatter_class=RawDescriptionHelpFormatter)
parser.add_argument('-mode', required=True, choices=['copy', 'inject'], default='inject', help='inject or copy')
parser.add_argument('-src-rom', metavar='src.gb', help='source rom for copy mode')
parser.add_argument('-frame-type', required=True, choices=['standard', 'wild'], default='standard', help='standard or wild')
parser.add_argument('-src-frame', metavar='[1-18]', choices=range(1,19), type=int, help='[1-18 standard] [1-8 wild] frame number from source rom')
parser.add_argument('-src-image', metavar='frame.png', help='source image in inject mode (.png, .bmp or already formatted tile data .bin)')
parser.add_argument('-dst-rom', required=True, metavar='dest.gb', help='destination rom file')
parser.add_argument('-dst-frame', required=True, metavar='[1-18]', choices=range(1,19), type=int, help='[1-18 standard] [1-8 wild] destination frame number')
args = parser.parse_args()

standardFramesStartAddr = 850296
standardFrameLength = 1672
wildFramesStartAddr = 796672
wildFrameLength = 6144

def frame_copy(frame_type, source_rom, source_frame, destination_rom, destination_frame):
	try:
		if frame_type == 'standard':
			frameLength = standardFrameLength
			frameStartAddr = standardFramesStartAddr
		else:
			frameLength = wildFrameLength
			frameStartAddr = wildFramesStartAddr
		sourceRom = open(source_rom, "rb")
		sourceRom.seek(frameStartAddr+frameLength*source_frame)
		frameData = sourceRom.read(frameLength)
		sourceRom.close()

		destinationRom = open(destination_rom, "r+b")
		if destination_frame < 10:
			destinationRom.seek(frameStartAddr+frameLength*destination_frame)
		else:
			destinationRom.seek(frameStartAddr+16384+frameLength*(destination_frame-9))
		destinationRom.write(frameData)
		destinationRom.close()
	finally:
		print('destination rom modified, frame copied\n')

frameTiles = []
frameTilesWildLR = []
tbMap = []
lrMap = []
uniqueTileIndex = 0
currentTile = 1
tileBytes = 16
standardTBTilePositions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360]
standardLRTilePositions = [41,42,61,62,81,82,101,102,121,122,141,142,161,162,181,182,201,202,221,222,241,242,261,262,281,282,301,302,59,60,79,80,99,100,119,120,139,140,159,160,179,180,199,200,219,220,239,240,259,260,279,280,299,300,319,320]
wildTBTilePositions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558,559,560]
wildLRTilePositions = [101,102,121,122,141,142,161,162,181,182,201,202,221,222,241,242,261,262,281,282,301,302,321,322,341,342,361,362,119,120,139,140,159,160,179,180,199,200,219,220,239,240,259,260,279,280,299,300,319,320,339,340,359,360,379,380]

def expose_all_wild_frames(destination_rom):
	# patch rom to show all 8 wild frame slots
	romData = bytearray()
	destinationRom = open(destination_rom, "r+b")
	romData = bytearray(destinationRom.read())
	romData = romData.replace(bytearray.fromhex('06FA82D5FE0120020E07'), bytearray.fromhex('08FA82D5FE0120020E08')).replace(bytearray.fromhex('06FA82D5FE0120020E08'), bytearray.fromhex('08FA82D5FE0120020E08'))
	destinationRom.seek(0)
	destinationRom.write(romData)
	destinationRom.close()

def process_tile(frame_type, tile):
	global frameTiles
	global frameTilesWildLR
	global tbMap
	global lrMap
	global uniqueTileIndex
	global currentTile

	if frame_type == 'standard':
		TBTilePositions = standardTBTilePositions
		LRTilePositions = standardLRTilePositions
	else:
		TBTilePositions = wildTBTilePositions
		LRTilePositions = wildLRTilePositions

	# check if tile position is part of the frame
	if currentTile in TBTilePositions or currentTile in LRTilePositions:
		# check if it's a new/unique tile
		if (frame_type == 'standard' and tile not in frameTiles) or (frame_type == 'wild'):
			# max of 96 unique tiles per frame
			if (frame_type == 'standard' and uniqueTileIndex < 96) or (frame_type == 'wild'):
				# push unique tile index to tile map
				if currentTile in TBTilePositions:
					tbMap.append(uniqueTileIndex)
				elif currentTile in LRTilePositions:
					lrMap.append(uniqueTileIndex)
				# push tile to frame data
				if currentTile in LRTilePositions and frame_type == 'wild':
					frameTilesWildLR.append(tile)
				else:
					frameTiles.append(tile)
				uniqueTileIndex+=1
			else:
				# once tile limit is reached, re-use first tile
				if currentTile in TBTilePositions:
					tbMap.append(95)
				elif currentTile in LRTilePositions:
					lrMap.append(95)
		else:
			# push re-used tile index  to tile map
			for i in range(len(frameTiles)):
				if frameTiles[i] == tile:
					if currentTile in TBTilePositions:
						tbMap.append(i)
					elif currentTile in LRTilePositions:
						lrMap.append(i)

def frame_inject(frame_type, source_image, destination_rom, destination_frame, convert_2bpp):
	try:
		# init tile and tile map
		global frameTiles
		global frameTilesWildLR
		global tbMap
		global lrMap
		global uniqueTileIndex
		global currentTile
		frameTiles = []
		tbMap = []
		lrMap = []
		uniqueTileIndex = 0
		currentTile = 1

		if frame_type == 'standard':
			frameLength = standardFrameLength
			frameStartAddr = standardFramesStartAddr
		else:
			frameLength = wildFrameLength
			frameStartAddr = wildFramesStartAddr

		if convert_2bpp:
			# if source is bitmap, convert and process
			image = Image.open(source_image)
			sourceImage = GBTileset.from_image(image).tiles
			for aTile in sourceImage:
				tile = bytearray.fromhex(aTile.to_hex_string())
				process_tile(frame_type, tile)
				currentTile+=1
		else:
			# if source is already in tile format, read and process
			sourceImage = open(source_image, "rb")
			sourceImage.seek(0)
			# read source image, one tile at a time
			tile = sourceImage.read(tileBytes)
			while tile:
				process_tile(frame_type, tile)
				# read next tile
				tile = sourceImage.read(tileBytes)
				currentTile+=1
			sourceImage.close()

		if frame_type == 'standard':
			# combine tile maps
			tileMap = tbMap+lrMap

			# pad end of tile data with blank tiles if less than 96
			while len(frameTiles) < 96:
				frameTiles.append(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
		else:
			frameTiles += frameTilesWildLR

		# merge all bytes
		frameData = bytearray()
		for tile in frameTiles:
			frameData.extend(tile)

		if frame_type == 'standard':
			frameData.extend(bytearray(tileMap))

		destinationRom = open(destination_rom, "r+b")
		if destination_frame < 10:
			destinationRom.seek(frameStartAddr+frameLength*destination_frame)
		else:
			destinationRom.seek(frameStartAddr+16384+frameLength*(destination_frame-9))
		destinationRom.write(frameData)
		destinationRom.close()
	finally:
		print('destination rom modified, frame injected\n')

if (args.src_frame > 8 or args.dst_frame > 8) and args.frame_type == 'wild':
	print('max index for wild frames is 8\n')
else:
	if args.mode == "copy":
		expose_all_wild_frames(args.dst_rom)
		frame_copy(args.frame_type, args.src_rom, args.src_frame, args.dst_rom, args.dst_frame)
	else:
		if args.src_image.endswith('bin'):
			expose_all_wild_frames(args.dst_rom)
			frame_inject(args.frame_type, args.src_image, args.dst_rom, args.dst_frame, False)
		elif args.src_image.endswith('png') or args.src_image.endswith('bmp'):
			expose_all_wild_frames(args.dst_rom)
			frame_inject(args.frame_type, args.src_image, args.dst_rom, args.dst_frame, True)
		else:
			print('source image can be .png, .bmp or already converted .bin (2bpp)\n')