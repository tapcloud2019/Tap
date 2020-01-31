"""Prepare NSC ASR datasets.

Download, unpack and create manifest files.
Manifest file is a json-format file with each line containing the
meta data (i.e. audio filepath, transcript and audio duration)
of each audio file in the data set.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import distutils.util
import os
import sys
import argparse
import soundfile
import json
import codecs
import io
import re
from pydub import AudioSegment
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--target_dir",
    default='./dataset/tap/temp',
    type=str,
    help="Directory to save the dataset. (default: %(default)s)")
parser.add_argument(
    "--manifest_prefix",
    default="manifest",
    type=str,
    help="Filepath prefix for output manifests. (default: %(default)s)")
args = parser.parse_args()


def create_manifest(data_dir, manifest_path):
    """Create a manifest json file summarizing the data set, with each line
    containing the meta data (i.e. audio filepath, transcription text, audio
    duration) of each audio file within the data set.
    """
    print("Creating manifest %s ..." % manifest_path)
    json_lines = []
    for subfolder, _, filelist in sorted(os.walk(data_dir)):
        wav_filelist = [
            filename for filename in filelist if filename.endswith('.WAV')
        ]
        if len(wav_filelist) > 0:
            for wav in wav_filelist:
                wav_filepath = os.path.join(subfolder, wav)
                parent_dir, _ = os.path.split(subfolder)
                new_path = os.path.join(parent_dir,'archive', wav)
                shutil.move(wav_filepath, new_path)

                audio_data, samplerate = soundfile.read(new_path)
                duration = float(len(audio_data)) / samplerate
                json_lines.append(
                    json.dumps({
                        'audio_filepath': new_path,
                        'duration': duration,
                        'text': ''
                    }))
                print(parent_dir)
    with codecs.open(manifest_path, 'w', 'utf-8') as out_file:
        for line in json_lines:
            out_file.write(line + '\n')


def main():
    if args.target_dir.startswith('~'):
        args.target_dir = os.path.expanduser(args.target_dir)
    create_manifest(
        data_dir=args.target_dir,
        manifest_path=args.manifest_prefix + ".TAP")


if __name__ == '__main__':
    main()
