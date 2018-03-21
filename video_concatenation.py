#!/usr/bin/python
"""
concatenate videos from a folder with rescaling, using ffmpeg
Couldn't find something that would do this, and put this together using the advice and documentation from various sites - might be useful for someone else.
specifically helpful:
http://www.bugcodemaster.com/article/concatenate-videos-using-ffmpeg
https://www.bugcodemaster.com/article/changing-resolution-video-using-ffmpeg
and obviously the concat section in 
https://ffmpeg.org/ffmpeg-filters.html

trying to keep this OS agnostic, but have only tested it on linux.
Niv Levy March 2018 . copyright under GPL v2
"""

import os
import time
import subprocess

def string_files_together(source_folder,
				 height = 1080,
				 output_filename_base = 'composite',
				 output_folder = None,
				 executable = './ffmpeg-3.4.2-64bit-static/ffmpeg',
				 start_i = 0,
				 end_i = 2**32):
	"""
	concatenate files from a folder.
	output filename is a supplied prefix + time stamp, either in a supplied folder, or
		if none is given, in the parent folder.
	:param source_folder:
	:param output_filename_base: prefix to output filename
	:param output_folder: [None] - if want to specify one explicitly, otherwise the parent folder is used.
	:param executable: ffmpeg executable
	:param start_i: index of file to start at , zero based
	:param end_i: index of file to end at, pythoneseque.
	:param height: height of video (pixels)
	:return: process return value
	"""

	if output_folder is None or len(output_folder) == 0:
		#output_folder = os.path.join( source_folder, '../')
		output_folder, output_file_name_mid = os.path.split(source_folder.rstrip(os.path.sep)) # note - don't strip the left separator!
	else:
		output_file_name_mid = ''
	
	output_filename = os.path.join(output_folder,
								time.strftime('{:}_{:}_%Y_%m_%d_%H_%M_%S.mp4'.format(output_filename_base, output_file_name_mid), time.localtime()))

	rr = os.listdir(source_folder)
	rr.sort()
	rr = rr[start_i:end_i]
	
	N = len(rr)
	print 'Will be concatenating the following files'
	# '-filter_complex "[1:v]scale=-2:1080,setsar=sar=1[Scaled];[0:v][Scaled][2:v]concat=n=3:v=1:a=0[Merged]" -map [Merged] -map 3:a /home/nlevy/se_tmp/../composite_20170628_b.mp4'
	inputs = []
	input_list = []
	filter_sections = '\"'
	concat_sources = ''
	for i, filename in enumerate(rr):
		print '{:} / {:} :  {:}'.format(i + 1, N, filename) 
		inputs.append(' -i "' + os.path.join(source_folder,filename) + '"')
		input_list.extend(['-i', os.path.join(source_folder,filename)])
		filter_sections += '[{:}:v:0] scale=-2:{:},setsar=sar=1 [Scaled{:}] ; '.format(i, height, i)
		concat_sources += '[Scaled{:}] [{:}:a:0] '.format(i,i)
	input_s = ''.join(inputs)
	filter_s = filter_sections + concat_sources + ' concat=n={:}:v=1:a=1 [v] [a]\"'.format(N)
	# this was used before i figured out escaping for subprocess.
	#return executable + input_s + ' -filter_complex ' + filter_s +  ' -map "[v]" -map "[a]"' + ' "' + output_filename + '"'
	args = [executable, ] + input_list + ['-filter_complex', filter_s.strip('"').lstrip('"'),] +  ['-map', '[v]', '-map', '[a]'] + [output_filename,]
	print 'args=\n', args
	p = subprocess.Popen(args, stdin = subprocess.PIPE, stdout = subprocess.PIPE)
	stop_requests = 0
	start_time = time.time()
	while True:
		try:
			if p.poll() is not None:
				break
			time.sleep(1)
		except KeyboardInterrupt:
			print 'trying to stop'
			stop_requests += 1
			if stop_requests < 2:
				print 'Trying to stop ffmpeg nicely - sending q'
				p.communicate(input = 'q\n')
			else:
				print 'Too many requests - trying to terminate process'
				p.terminate()
	print 'Total processing time {:0.1f} seconds'.format(time.time() - start_time)

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser(description= 'Concatenate video files from a folder while scaling them')
	parser.add_argument('-s', '--source', type = str, required = True,
			help= 'source folder')
	parser.add_argument('--start_i', type = int, default = 0,
			help= 'first file to use from the sorted list')
	parser.add_argument('--end_i', type = int, default = 2**32,
			help= 'last file to use from the sorted list - python list logic; negative numbers sllowed e.g. -1 is all but the last file')
	parser.add_argument('--height', type = int, default = 1080,
			help= 'height of scaled video')
	parser.add_argument('--output_prefix', type = str, default = 'composite',
			help= 'prefix for output file')
	parser.add_argument('--output_folder', type = str, default = '',
			help= 'output folder - if empty (default), the parent folder will be used')
	parser.add_argument('--ffmpeg', type = str, default = './ffmpeg-3.4.2-64bit-static/ffmpeg',
			help= 'ffmpeg executable')
	args = parser.parse_args()
	string_files_together(args.source,
				 height = args.height,
				 output_filename_base = args.output_prefix,
				 output_folder = args.output_folder,
				 executable = args.ffmpeg,
				 start_i = args.start_i,
				 end_i = args.end_i)
