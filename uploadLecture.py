from dokuwiki import DokuWiki
import sys
import subprocess
import os
import glob
import math

def usage():
	print "usage: uploadLecture url user password pdf lecNum lecName [delete]"
	sys.exit(1)

def convertPDFtoPNGs(pdf):
	basename, extension = os.path.splitext(pdf)
	pngname = "{0}.png".format(basename)
	subprocess.call("convert {0} {1}".format(pdf, pngname), shell=True)
	# Return the filenames of all files generated
	# We ensure they're in order, so future processing can assume so.
	filenames = glob.glob("{0}-*.png".format(basename))
	return ["{0}-{1}.png".format(basename, i) for i in range(len(filenames))]

def deletePNGs(pdf):
	basename, extension = os.path.splitext(pdf)
	pngwildcard = "{0}-*.png".format(basename)
	subprocess.call("rm -f {0}".format(pngwildcard), shell=True)

def genSlidePage(namespace, slideNum, numSlides):
	content = ""
	# The slide image
	content += "{{" + "{0}:slide{1}.png".format(namespace, slideNum) + "}}\n\n"
	# Prev button
	if slideNum > 1:
		content += "<fs 1.2em>[[{0}:slide{1}|<<Prev]]</fs> ".format(namespace, slideNum-1)
	# Slide counter
	content += "<fs 1.2em>Slide {0}/{1}</fs> ".format(slideNum, numSlides)
	# Next button
	if slideNum < numSlides:
		content += "<fs 1.2em>[[{0}:slide{1}|Next>>]]</fs>".format(namespace, slideNum+1)
	# Lecture overview
	content += "\n\n<fs 1.2em>[[{0}:overview|Lecture Overview]]</fs>\n\n".format(namespace)
	# Discussion thread
	content += "\\\\\n~~DISCUSSION~~\n"
	return content

numSlidesPerRow = 4
slideThumbSize = 200
def genOverviewPage(namespace, lectureNum, lectureName, numSlides):
	content = ""
	# Title
	content += "==== Lecture {0}: {1} ====\n\n\\\\\n".format(lectureNum, lectureName)
	# PDF Download link
	content += "{{" + "{0}:lecture{1}.pdf|Download as PDF".format(namespace, lectureNum) + "}}\n\n\\\\\n"
	# Table of slide links
	numSlidesLeft = numSlides
	numRows = int(math.ceil(float(numSlides)/numSlidesPerRow))
	for i in range(numRows):
		numCols = min(numSlidesPerRow, numSlidesLeft)
		content += "|"
		for j in range(numCols):
			slideNum = i*numSlidesPerRow + j + 1
			content += " [[{0}:slide{1}|".format(namespace, slideNum) + "{{" + "{0}:slide{1}.png?{2}".format(namespace, slideNum, slideThumbSize) + "}}]] |"
		content += "\n"
		numSlidesLeft -= numCols
	content += "\n"
	return content

def main(url, username, password, pdf, lectureNum, lectureName, doDelete):
	# Establish connection to dokuwiki
	print "=== Establishing connection to dokuwiki... ==="
	client = DokuWiki(url, username, password)
	namespace = "lectures:lecture" + str(lectureNum)
	# Convert PDF to PNGs
	print "=== Convering PDF to PNGs... ==="
	pngfilenames = convertPDFtoPNGs(pdf)
	numSlides = len(pngfilenames)
	# Upload (or delete) slide PNGs and pages
	print "=== Generating/uploading slide pages/images... ==="
	for i in range(numSlides):
		pngfname = pngfilenames[i]
		slideIndex = i+1
		sys.stdout.write("    {0}/{1}\r".format(slideIndex, numSlides))
		sys.stdout.flush()
		imgname = "{0}:slide{1}.png".format(namespace, slideIndex)
		pagename = "{0}:slide{1}".format(namespace, slideIndex)
		if doDelete:
			client.pages.delete(pagename)
			client.medias.delete(imgname)
		else:
			client.medias.add(imgname, pngfname, True) #overwrite if already exists
			client.pages.set(pagename, genSlidePage(namespace, slideIndex, numSlides))
	# Upload (or delete) overview page and PDF
	print "\n=== Uploading overview page / raw slides PDF... ==="
	overviewname = namespace + ":overview"
	lectureid = "lecture" + str(lectureNum)
	pdfname = namespace + ":" + lectureid + ".pdf"
	if doDelete:
		client.pages.delete(overviewname)
		client.medias.delete(pdfname)
	else:
		client.medias.add(pdfname, pdf, True)
		client.pages.set(overviewname, genOverviewPage(namespace, lectureNum, lectureName, numSlides))
	# Clean up tmp files
	print "=== Cleaning up... ==="
	deletePNGs(pdf)
	print "=== DONE ==="


if __name__ == "__main__":
	numArgs = len(sys.argv) - 1
	if numArgs != 6 and numArgs != 7:
		usage()
	url = sys.argv[1]
	username = sys.argv[2]
	password = sys.argv[3]
	pdf = sys.argv[4]
	lectureNum = sys.argv[5]
	lectureName = sys.argv[6]
	doDelete = False
	if numArgs == 7 and sys.argv[7] == "delete":
		doDelete = True
	main(url, username, password, pdf, lectureNum, lectureName, doDelete)




