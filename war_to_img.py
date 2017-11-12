import sys, os
from warlib import WAR
from struct import pack
from os.path import abspath, isdir

container = WAR(sys.argv[1])
if not isdir('./dumps'):
	os.mkdir('./dumps')

for img_id in container.sprites:
	for palette_id in container.colorPalettes:
		image_name = '{img}_{pal}.png'.format(img=img_id, pal=palette_id)

		try:
			RGBA = container.sprites[img_id].to_png(0, container.colorPalettes[palette_id])
		except KeyError:
			continue # Color palette not fitting for this image

		with open('./dumps/'+image_name, 'wb') as fh:
			RGBA.save(image_name, file=fh)
