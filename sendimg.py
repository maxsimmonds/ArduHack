import os
import time

while(1):
	
	os.system("fswebcam image.jpg")														## Take image
	os.system("wget --post-file=image.jpg http://www.agm.me.uk/arduhack/_putimg.php")	## wget image to server
	
	os.system("wget --post-file=data.txt http://www.agm.me.uk/arduhack/_putdata.php")	## wget data to server
	os.system("rm _put*")
		
	time.sleep(2)																		## sleep for 2 secs.

