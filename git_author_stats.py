#! /usr/bin/env python

# Copyright (c) 2015 Michael J Simms

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
	"""Returns True if the line appears to start with a comment, False otherwise."""
	if file_ext in ['.c', '.cpp', '.cxx', '.h', '.m', '.java', '.rs']:
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
	"""Returns True if the line appears to contain source code, False otherwise."""
	if file_ext in ['.c', '.cpp', '.cxx', '.h', '.m', '.java', '.rs']:
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

def analyze_file(file, start_time, end_time, ignore_comments, ignore_empty, only_source_lines, extensions):
	_, file_ext = os.path.splitext(file)
	if file_ext not in extensions:
		return
	
	p = subprocess.Popen(["git", "blame", file], stdout = subprocess.PIPE, stderr= subprocess.PIPE)
	blameOutput, _ = p.communicate()
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
			if timestamp >= start_time and timestamp < end_time:
				author_lines[author_str] = author_lines[author_str] + 1

def analyze_repo(repo, start_time, end_time, ignore_comments, ignore_empty, only_source_lines, extensions):
	for root, _, files in os.walk(repo):
		for file in files:
			analyze_file(os.path.join(root, file), start_time, end_time, ignore_comments, ignore_empty, only_source_lines, extensions)

def main():
	"""Entry point for the app."""
	
	parser = argparse.ArgumentParser()
	parser.add_argument("--repo", required=True, help="Path of the local repo to examine. ex: --repo /src/my_repo/")
	parser.add_argument("--start-time", required=False, help="Filter out lines that were modified before this time. ex: --repo start-time 2017-01-01")
	parser.add_argument("--end-time", required=False, help="Filter out lines that were modified after (or at) this time. ex: --repo end-time 2018-01-01")
	parser.add_argument("--ignore-comments", default=True, required=False, help="Filter out lines that start with a comment.")
	parser.add_argument("--ignore-empty", default=True, required=False, help="Filter out lines that only contain whitespace.")
	parser.add_argument("--only-source-lines", default=True, required=False, help="Only consider lines that appear to be source code lines, such as those that contain a semicolon in C-based languages.")
	parser.add_argument("--extensions", default=".c,.cpp,.h,.m,.py,.rs", required=False, help="Only consider files with certain extensions. ex: --extensions .c,.cpp,.h")
	args = parser.parse_args()

	start_time = 0
	if sys.version_info[0] < 3:
		end_time = sys.maxint
	else:
		end_time = sys.maxsize
	extensions = args.extensions.split(',')

	if args.start_time is not None:
		start_time = time.mktime(datetime.datetime.strptime(args.start_time, "%Y-%m-%d").timetuple())
	if args.end_time is not None:
		end_time = time.mktime(datetime.datetime.strptime(args.end_time, "%Y-%m-%d").timetuple())

	full_path = os.path.realpath(args.repo)
	os.chdir(full_path)

	print("Examining the following repository: " + full_path)
	print("Counting lines of code in files with the following extensions: " + args.extensions)
	print("-" * 80)

	analyze_repo(full_path, start_time, end_time, args.ignore_comments, args.ignore_empty, args.only_source_lines, extensions)

	total = 0
	for author in author_lines:
		print(author + ":\t" + str(author_lines[author]))
		total += author_lines[author]

	print("-" * 80)
	print("Total:\t" + str(total))

if __name__ == "__main__":
	main()
