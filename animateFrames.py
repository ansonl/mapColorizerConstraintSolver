import imageio

#from os import listdir
#from os.path import isfile, join
#filenames = [f for f in listdir('frames') if isfile(join('frames', f))]

filenames = []
for x in range(5879):
    filenames.append('{}.png'.format(x))

images = []
for filename in filenames:
	images.append(imageio.imread('frames/' + filename))
imageio.mimsave('animated.gif', images, duration=0.01)