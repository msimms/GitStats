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

author_lines = collections.Counter()
author_expr = re.compile(r'[a-zA-Z ]+')
timestamp_expr = re.compile(r'[\d]+-[\d]+-[\d]+\s[\d]+:[\d]+:[\d]+')

def is_empty(source_str):
	return len(source_str) == 0

def is_comment(source_str, file_ext):
	if file_ext in ['.c', '.cpp', '.cxx', '.h', '.m', '.java']:
		if source_str.find('//') == 0 or source_str.find('/*') == 0:
			return True
	elif file_ext in ['.py']:
		if source_str.find('#') == 0:
			return True
	elif file_ext in ['.asm']:
		if source_str.find(';') == 0:
			return True
	return False

def is_source_line(source_str, file_ext):
	if file_ext in ['.c', '.cpp', '.cxx', '.h', '.m', '.java']:
		if source_str.find(';') > 0:
			return True
	elif file_ext in ['.py']:
		if len(source_str) > 0:
			return True
	return False

def parse_line(line):
	try:
		ascii_line = line.decode('ascii')
		left_paren_index = line.find('(')

		if left_paren_index >= 0:
			sub_line = ascii_line[left_paren_index + 1:]
			author_match = author_expr.search(sub_line)
			timestamp_match = timestamp_expr.search(sub_line)

			if author_match is not None and timestamp_match is not None:
				author_str = sub_line[author_match.start():author_match.end()]
				author_str = author_str.strip()
				timestamp_str = sub_line[timestamp_match.start():timestamp_match.end()]
				timestamp_str = timestamp_str.strip()
				remainder_str = sub_line[timestamp_match.end():]
				source_str_index = remainder_str.find(')')
				source_str = remainder_str[source_str_index + 1:]
				return author_str, timestamp_str, source_str
					
	except UnicodeDecodeError:
		pass
	return "", "", ""

def analyze_file(file, start_time, ignore_comments, ignore_empty, only_source_lines, extensions):
	file_name, file_ext = os.path.splitext(file)
	if file_ext not in extensions:
		return
	
	p = subprocess.Popen(["git", "blame", file], stdout = subprocess.PIPE, stderr= subprocess.PIPE)
	blameOutput,blameError = p.communicate()
	blameLines = blameOutput.split('\n')

	for line in blameLines:
		author_str, timestamp_str, source_str = parse_line(line)

		if len(author_str) > 0 and len(timestamp_str) > 0 and len(source_str) > 0:
			timestamp = time.mktime(datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timetuple())
			strippedStr = source_str.strip()
			if ignore_comments and is_comment(strippedStr, file_ext):
				continue
			if ignore_empty and is_empty(strippedStr):
				continue
			if only_source_lines and not is_source_line(strippedStr, file_ext):
				continue
			if timestamp >= start_time:
				author_lines[author_str] = author_lines[author_str] + 1

def analyze_repo(repo, start_time, ignore_comments, ignore_empty, only_source_lines, extensions):
	for root, dirs, files in os.walk(repo):
		for file in files:
			analyze_file(os.path.join(root, file), start_time, ignore_comments, ignore_empty, only_source_lines, extensions)

parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True)
parser.add_argument("--start-time", required=False)
parser.add_argument("--ignore-comments", default=True, required=False)
parser.add_argument("--ignore-empty", default=True, required=False)
parser.add_argument("--only-source-lines", default=True, required=False)
parser.add_argument("--extensions", default=".c,.cpp,.h,.m,.py", required=False)
args = parser.parse_args()

start_time = 0
extensions = args.extensions.split(',')

if args.start_time is not None:
	start_time = time.mktime(datetime.datetime.strptime(args.start_time, "%Y-%m-%d").timetuple())

full_path = os.path.realpath(args.repo)
os.chdir(full_path)
analyze_repo(full_path, start_time, args.ignore_comments, args.ignore_empty, args.only_source_lines, extensions)

for author in author_lines:
	print author + "\t" + str(author_lines[author])
