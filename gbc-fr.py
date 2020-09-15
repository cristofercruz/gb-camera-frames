import os
import argparse
import binascii
from img2gb import GBTileset
from PIL import Image

from argparse import RawTextHelpFormatter
from argparse import RawDescriptionHelpFormatter

parser = argparse.ArgumentParser(description='Tool to modify standard photo frames in Game Boy Camera rom.\n\nUse inject mode to insert a frame from binary tile image file or copy mode to transfer frame data from one rom to another.', formatter_class=RawTextHelpFormatter)
parser.add_argument('--mode', '-m', required=True, choices=['copy', 'inject'], default='inject', help='\n')
parser.add_argument('--frame-type', '-ft', required=True, choices=['standard', 'wild'], default='standard', help='\n')
parser.add_argument('--source-rom', '-sr', metavar='FILE', help='source rom .gb file, required for copy mode\n\n')
parser.add_argument('--source-frame', '-sf', metavar='[1-18]', choices=range(1,26), type=int, help='standard:[1-18] wild:[1-8] (Hello Kitty - standard:[1-25] wild:[1-6]) frame number from source rom, required for copy mode\n\n')
parser.add_argument('--source-image', '-si', metavar='FILE', help='source image file for inject mode (.png, .bmp or already formatted tile data .bin)\n\n')
parser.add_argument('--target-rom', '-tr', required=True, metavar='FILE', help='target rom .gb file\n\n')
parser.add_argument('--target-frame', '-tf', required=True, metavar='[1-18]', choices=range(1,19), type=int, help='[1-18 standard] [1-8 wild] target frame number')
args = parser.parse_args()

ROM_TITLE_OFFSET = 0x134
ROM_TITLE_LENGTH = 0xF
STANDARD_FRAME_OFFSET = 0xD0000
STANDARD_FRAME_LENGTH = 0x600
STANDARD_FRAME_MAP_LENGTH = 0x88
WILD_FRAME_OFFSET = 0xC4000
WILD_FRAME_LENGTH = 0x1800
BANK_SHIFT = 0x4000
TILE_BYTES = 16
HELLO_KITTY_STANDARD_OFFSETS = [[0xC6C70, 0xCF5D0], [0xC3B80, 0xCF548], [0xCBEC0, 0xCF4C0], [0xC5F10, 0xCF658], [0xCF210, 0xCF7F0], [0xC73A0, 0xCF768], [0xB7420, 0xCF6E0], [0xBE3E0, 0xCF438], [0xB3CD0, 0xC7EF0], [0xB2B80, 0xCF3B0], [0x8FD50, 0xC7F78], [0xC3800, 0xD7800], [0xBDC00, 0xD3F70], [0xD7F70, 0xD7888], [0xC5C00, 0xD7998], [0xB7C20, 0xD7910], [0xC3ED0, 0xD3D50], [0x33F80, 0xD3CC8], [0xDB800, 0xD3DD8], [0xB2200, 0xD3EE8], [0xB34D0, 0xD3E60], [0xB3030, 0xD7A20], [0x93E00, 0xD7D50], [0x77FE0, 0xCFCB8], [0x77FF0, 0xCFDC4]]
HELLO_KITTY_WILD_OFFSETS = [0x6C000, 0x60000, 0x64000, 0x65800, 0x69800, 0x68000]

targetRomHK = False
sourceRomHK = False
frameTiles = []
frameTilesWildSides = []
frameStandardTopBottomMap = []
frameStandardSidesMap = []
uniqueStandardTileIndex = 0
currentTile = 1
limitReachedMessage = ""

standardTopBottomTilePositions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,321,322,323,324,325,326,327,328,329,330,331,332,333,334,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360]
standardSidesTilePositions = [41,42,61,62,81,82,101,102,121,122,141,142,161,162,181,182,201,202,221,222,241,242,261,262,281,282,301,302,59,60,79,80,99,100,119,120,139,140,159,160,179,180,199,200,219,220,239,240,259,260,279,280,299,300,319,320]
wildTopBottomTilePositions = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513,514,515,516,517,518,519,520,521,522,523,524,525,526,527,528,529,530,531,532,533,534,535,536,537,538,539,540,541,542,543,544,545,546,547,548,549,550,551,552,553,554,555,556,557,558,559,560]
wildLeftRightTilePositions = [101,102,121,122,141,142,161,162,181,182,201,202,221,222,241,242,261,262,281,282,301,302,321,322,341,342,361,362,119,120,139,140,159,160,179,180,199,200,219,220,239,240,259,260,279,280,299,300,319,320,339,340,359,360,379,380]

def expose_all_wild_frames(targetRom):
	# patch rom to show all 8 wild frame slots
	wildINT = bytearray.fromhex('06FA82D5FE0120020E07')
	wildJPN = bytearray.fromhex('06FA82D5FE0120020E08')
	wildALL = bytearray.fromhex('08FA82D5FE0120020E08')
	romData = bytearray()
	targetRomFile = open(targetRom, "r+b")
	romData = bytearray(targetRomFile.read())
	# only patch if needs patching
	if (romData.find(wildINT) > 0 or romData.find(wildJPN) > 0):
		romData = romData.replace(wildINT, wildALL).replace(wildJPN, wildALL)
		targetRomFile.seek(0)
		targetRomFile.write(romData)
	targetRomFile.close()

def frame_copy(frameType, sourceRom, sourceFrame, targetRom, targetFrame, hkRom):
	if frameType == 'standard':
		FRAME_LENGHT = STANDARD_FRAME_LENGTH + STANDARD_FRAME_MAP_LENGTH
		FRAME_OFFSET = STANDARD_FRAME_OFFSET
	else:
		FRAME_LENGHT = WILD_FRAME_LENGTH
		FRAME_OFFSET = WILD_FRAME_OFFSET

	sourceRomFile = open(sourceRom, "rb")

	if hkRom != True:
		# use consistent frame offset for rom other than hello kitty
		if sourceFrame < 9:
			sourceRomFile.seek(FRAME_OFFSET+FRAME_LENGHT*sourceFrame)
		else:
			sourceRomFile.seek(FRAME_OFFSET+BANK_SHIFT+FRAME_LENGHT*(sourceFrame-9))
		frameData = sourceRomFile.read(FRAME_LENGHT)
	else:
		# for hello kitty rom, use the stored non standard offset for each frame and frame map
		if frameType == 'standard':
			sourceRomFile.seek(HELLO_KITTY_STANDARD_OFFSETS[sourceFrame][0])
			frameData = sourceRomFile.read(STANDARD_FRAME_LENGTH)
			sourceRomFile.seek(HELLO_KITTY_STANDARD_OFFSETS[sourceFrame][1])
			frameData += sourceRomFile.read(STANDARD_FRAME_MAP_LENGTH)
		else:
			sourceRomFile.seek(HELLO_KITTY_WILD_OFFSETS[sourceFrame])
			frameData = sourceRomFile.read(WILD_FRAME_LENGTH)
	sourceRomFile.close()

	targetRomFile = open(targetRom, "r+b")
	if targetFrame < 9:
		targetRomFile.seek(FRAME_OFFSET+FRAME_LENGHT*targetFrame)
	else:
		targetRomFile.seek(FRAME_OFFSET+BANK_SHIFT+FRAME_LENGHT*(targetFrame-9))
	targetRomFile.write(frameData)
	targetRomFile.close()

	print("\nTarget rom modified, frame " + str(sourceFrame+1) + " copied from " + str(sourceRom) + " into slot " + str(targetFrame+1) + " on " + str(targetRom) + ".\n")

def frame_inject(frameType, sourceImage, targetRom, targetFrame, convertBitmap):
	# init tile and tile map
	global frameTiles
	global frameTilesWildSides
	global frameStandardTopBottomMap
	global frameStandardSidesMap
	global uniqueStandardTileIndex
	global currentTile

	if frameType == 'standard':
		FRAME_LENGHT = STANDARD_FRAME_LENGTH + STANDARD_FRAME_MAP_LENGTH
		FRAME_OFFSET = STANDARD_FRAME_OFFSET
	else:
		FRAME_LENGHT = WILD_FRAME_LENGTH
		FRAME_OFFSET = WILD_FRAME_OFFSET

	if convertBitmap:
		# if source is bitmap, convert to tiles and process
		image = Image.open(sourceImage)
		imageWidth, imageHeight = image.size
		# check image size
		if frameType == 'standard' and (imageWidth != 160 or imageHeight != 144):
			raise Exception("Incorrect image size, should be 160px x 144px")
		elif frameType == 'wild' and (imageWidth != 160 or imageHeight != 224):
			raise Exception("Incorrect image size, should be 160px x 224px")
		sourceImageTiles = GBTileset.from_image(image).tiles
		# process tiles
		for aTile in sourceImageTiles:
			tile = bytearray.fromhex(aTile.to_hex_string())
			process_tile(frameType, tile)
			currentTile+=1
	else:
		# if source is already in tile format, read and process
		sourceImageTiles = open(sourceImage, "rb")
		sourceImageTiles.seek(0, os.SEEK_END)

		if frameType == 'standard' and (sourceImageTiles.tell() != 5760):
			raise Exception("Incorrect source tileset size, should be 160px x 144px (5760 bytes)")
		elif frameType == 'wild' and (sourceImageTiles.tell() != 8960):
			raise Exception("Incorrect source tileset size, should be 160px x 224px (8960 bytes)")

		sourceImageTiles.seek(0)
		# read source image, one tile at a time
		tile = sourceImageTiles.read(TILE_BYTES)
		# process tiles
		while tile:
			process_tile(frameType, tile)
			# read next tile
			tile = sourceImageTiles.read(TILE_BYTES)
			currentTile+=1
		sourceImageTiles.close()

	# only need tile map for standard frames
	if frameType == 'standard':
		# combine tile maps
		tileMap = frameStandardTopBottomMap+frameStandardSidesMap

		# pad end of tile data with blank tiles if less than 96
		while len(frameTiles) < 96:
			frameTiles.append(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
	else:
		# add wild frame side tiles to the end of frame array
		frameTiles += frameTilesWildSides

	# merge all bytes
	frameData = bytearray()
	for tile in frameTiles:
		frameData.extend(tile)
	if frameType == 'standard':
		frameData.extend(bytearray(tileMap))

	targetRomFile = open(targetRom, "r+b")
	if targetFrame < 9:
		targetRomFile.seek(FRAME_OFFSET+FRAME_LENGHT*targetFrame)
	else:
		targetRomFile.seek(FRAME_OFFSET+BANK_SHIFT+FRAME_LENGHT*(targetFrame-9))
	targetRomFile.write(frameData)
	targetRomFile.close()

	print("\nTarget rom modified, source image " + str(sourceImage) + " injected into slot " + str(targetFrame+1) + " on " + str(targetRom) + ".\n" + str(limitReachedMessage))

def process_tile(frameType, tile):
	global frameTiles
	global frameTilesWildSides
	global frameStandardTopBottomMap
	global frameStandardSidesMap
	global uniqueStandardTileIndex
	global currentTile
	global limitReachedMessage

	if frameType == 'standard':
		TBTilePositions = standardTopBottomTilePositions
		LRTilePositions = standardSidesTilePositions
	else:
		TBTilePositions = wildTopBottomTilePositions
		LRTilePositions = wildLeftRightTilePositions

	# check if tile position is part of the frame
	if currentTile in TBTilePositions or currentTile in LRTilePositions:
		# check if it's a new/unique tile
		if (frameType == 'standard' and tile not in frameTiles) or (frameType == 'wild'):
			# max of 96 unique tiles per frame for standard frames
			if (frameType == 'standard' and uniqueStandardTileIndex < 96) or (frameType == 'wild'):
				# push unique tile index to tile map
				if currentTile in TBTilePositions and frameType == 'standard':
					frameStandardTopBottomMap.append(uniqueStandardTileIndex)
				elif currentTile in LRTilePositions and frameType == 'standard':
					frameStandardSidesMap.append(uniqueStandardTileIndex)
				# push tile to frame data arrays
				if currentTile in LRTilePositions and frameType == 'wild':
					# separate wild frame side tiles, these go at the end
					frameTilesWildSides.append(tile)
				else:
					frameTiles.append(tile)
				uniqueStandardTileIndex+=1
			else:
				# once tile limit is reached on standard frame, re-use last tile
				limitReachedMessage = "NOTICE: Source image used more than 96 unique tiles, injected frame will appear incomplete.\n"
				if currentTile in TBTilePositions:
					frameStandardTopBottomMap.append(95)
				elif currentTile in LRTilePositions:
					frameStandardSidesMap.append(95)
		else:
			# push re-used tile index  to tile map
			for i in range(len(frameTiles)):
				if frameTiles[i] == tile:
					if currentTile in TBTilePositions:
						frameStandardTopBottomMap.append(i)
					elif currentTile in LRTilePositions:
						frameStandardSidesMap.append(i)

def main():
	try:
		global targetRomHK
		global sourceRomHK
		targetRomFile = open(args.target_rom, "rb")
		targetRomFile.seek(ROM_TITLE_OFFSET)
		targetRomTitle = targetRomFile.read(ROM_TITLE_LENGTH).decode("utf-8")
		targetRomHK = False
		if targetRomTitle == "POCKETCAMERA_SN":
			targetRomHK = True
		if args.mode == "copy":
			sourceRomFile = open(args.source_rom, "rb")
			sourceRomFile.seek(ROM_TITLE_OFFSET)
			sourceRomTitle = sourceRomFile.read(ROM_TITLE_LENGTH).decode("utf-8")
			sourceRomHK = False
			if sourceRomTitle == "POCKETCAMERA_SN":
				sourceRomHK = True

		if targetRomHK == True:
			raise Exception("Hello Kitty Pocket Camera is only supported as a source rom using copy mode")
		elif args.target_frame > 8 and args.frame_type == 'wild':
			raise Exception("Max index for wild frames is 8")

		if args.mode == "copy":
			if args.source_frame > 8 and args.frame_type == 'wild':
				raise Exception("Max index for wild frames is 8")
			elif args.source_frame > 6 and args.frame_type == 'wild' and sourceRomHK == True:
				raise Exception("Max index for wild frames on this source rom is 6")
			elif (sourceRomHK == False and args.source_frame > 18):
				raise Exception("This rom can only select frame number from range [1-18]")
			elif (sourceRomHK == True and args.source_frame > 25):
				raise Exception("This rom can only select frame number from range [1-25]")
			else:
				frame_copy(args.frame_type, args.source_rom, args.source_frame-1, args.target_rom, args.target_frame-1, sourceRomHK)
		else:
			if args.source_image.endswith('bin'):
				frame_inject(args.frame_type, args.source_image, args.target_rom, args.target_frame-1, False)
			elif args.source_image.endswith('png') or args.source_image.endswith('bmp'):
				frame_inject(args.frame_type, args.source_image, args.target_rom, args.target_frame-1, True)
			else:
				raise Exception("Source image can be .png, .bmp or already converted .bin (2bpp)")
		expose_all_wild_frames(args.target_rom)
	except Exception as error:
		print('\n'+str(error))
	finally:
		pass

main()