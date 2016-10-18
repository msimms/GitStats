#! /usr/bin/env python

# Copyright (c) 2015 Michael J Simms

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


import argparse
import collections
import os
import re
import string
import subprocess
import sys
import datetime
import time

authorLines = collections.Counter()
authorExpr = re.compile(r'[a-zA-Z ]+')
timestampExpr = re.compile(r'[\d]+-[\d]+-[\d]+\s[\d]+:[\d]+:[\d]+')

def is_empty(sourceStr):
	return len(sourceStr) == 0

def is_comment(sourceStr, fileExt):
	if fileExt in ['.c', '.cpp', '.cxx', '.h', '.m', '.java']:
		if sourceStr.find('//') == 0 or sourceStr.find('/*') == 0:
			return True
	elif fileExt in ['.py']:
		if sourceStr.find('#') == 0:
			return True
	elif fileExt in ['.asm']:
		if sourceStr.find(';') == 0:
			return True
	return False

def is_source_line(sourceStr, fileExt):
	if fileExt in ['.c', '.cpp', '.cxx', '.h', '.m', '.java']:
		if sourceStr.find(';') > 0:
			return True
	elif fileExt in ['.py']:
		if len(sourceStr) > 0:
			return True
	return False

def parse_line(line):
	try:
		asciiLine = line.decode('ascii')
		leftParenIndex = line.find('(')

		if leftParenIndex >= 0:
			subLine = asciiLine[leftParenIndex + 1:]
			authorMatch = authorExpr.search(subLine)
			timestampMatch = timestampExpr.search(subLine)

			if authorMatch is not None and timestampMatch is not None:
				authorStr = subLine[authorMatch.start():authorMatch.end()]
				authorStr = authorStr.strip()
				timestampStr = subLine[timestampMatch.start():timestampMatch.end()]
				timestampStr = timestampStr.strip()
				remainderStr = subLine[timestampMatch.end():]
				sourceStrIndex = remainderStr.find(')')
				sourceStr = remainderStr[sourceStrIndex + 1:]
				return authorStr, timestampStr, sourceStr
					
	except UnicodeDecodeError:
		pass
	return "", "", ""

def analyze_file(file, startTime, ignoreComments, ignoreEmpty, onlySourceLines, extensions):
	fileName, fileExt = os.path.splitext(file)
	if fileExt not in extensions:
		return
	
	p = subprocess.Popen(["git", "blame", file], stdout = subprocess.PIPE, stderr= subprocess.PIPE)
	blameOutput,blameError = p.communicate()
	blameLines = blameOutput.split('\n')

	for line in blameLines:
		authorStr, timestampStr, sourceStr = parse_line(line)

		if len(authorStr) > 0 and len(timestampStr) > 0 and len(sourceStr) > 0:
			timestamp = time.mktime(datetime.datetime.strptime(timestampStr, "%Y-%m-%d %H:%M:%S").timetuple())
			strippedStr = sourceStr.strip()
			if ignoreComments and is_comment(strippedStr, fileExt):
				continue
			if ignoreEmpty and is_empty(strippedStr):
				continue
			if onlySourceLines and not is_source_line(strippedStr, fileExt):
				continue
			if timestamp >= startTime:
				authorLines[authorStr] = authorLines[authorStr] + 1

def analyze_repo(repo, startTime, ignoreComments, ignoreEmpty, onlySourceLines, extensions):
	for root, dirs, files in os.walk(repo):
		for file in files:
			analyze_file(os.path.join(root, file), startTime, ignoreComments, ignoreEmpty, onlySourceLines, extensions)

parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True)
parser.add_argument("--startTime", required=False)
parser.add_argument("--ignoreComments", default=True, required=False)
parser.add_argument("--ignoreEmpty", default=True, required=False)
parser.add_argument("--onlySourceLines", default=True, required=False)
parser.add_argument("--extensions", default=".c,.cpp,.h,.m,.py", required=False)
args = parser.parse_args()

startTime = 0
extensions = args.extensions.split(',')

if args.startTime is not None:
	startTime = time.mktime(datetime.datetime.strptime(args.startTime, "%Y-%m-%d").timetuple())

fullPath = os.path.realpath(args.repo)
os.chdir(fullPath)
analyze_repo(fullPath, startTime, args.ignoreComments, args.ignoreEmpty, args.onlySourceLines, extensions)

for author in authorLines:
	print author + "\t" + str(authorLines[author])
