"""Inferer for DeepSpeech2 model."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import argparse
import functools
import paddle.fluid as fluid
from data_utils.data import DataGenerator
from model_utils.model import DeepSpeech2Model
from model_utils.model_check import check_cuda, check_version
from utils.error_rate import wer, cer
from utils.utility import add_arguments, print_arguments
import codecs

parser = argparse.ArgumentParser(description=__doc__)
add_arg = functools.partial(add_arguments, argparser=parser)
# yapf: disable
add_arg('num_samples',      int,    1,     "# of samples to infer.")
add_arg('beam_size',        int,    500,    "Beam search width.")
add_arg('num_proc_bsearch', int,    5,      "# of CPUs for beam search.")
add_arg('num_conv_layers',  int,    2,      "# of convolution layers.")
add_arg('num_rnn_layers',   int,    3,      "# of recurrent layers.")
add_arg('rnn_layer_size',   int,    1024,   "# of recurrent cells per layer.")
add_arg('alpha',            float,  1.4,    "Coef of LM for beam search.")
add_arg('beta',             float,  0.35,    "Coef of WC for beam search.")
add_arg('cutoff_prob',      float,  1.0,    "Cutoff probability for pruning.")
add_arg('cutoff_top_n',     int,    40,     "Cutoff number for pruning.")
add_arg('use_gru',          bool,   True,  "Use GRUs instead of simple RNNs.")
add_arg('use_gpu',          bool,   False,   "Use GPU or not.")
add_arg('share_rnn_weights',bool,   False,   "Share input-hidden weights across "
                                            "bi-directional RNNs. Not for GRU.")
add_arg('infer_manifest',   str,
        'manifest.TAP',
        "Filepath of manifest to infer.")
add_arg('mean_std_path',    str,
        'models/baidu_en8k/mean_std.npz',
        "Filepath of normalizer's mean & std.")
add_arg('vocab_path',       str,
        'models/baidu_en8k/vocab.txt',
        "Filepath of vocabulary.")
add_arg('lang_model_path',  str,
        'models/lm/common_crawl_00.prune01111.trie.klm',
        "Filepath for language model.")
add_arg('model_path',       str,
        'models/baidu_en8k',
        "If None, the training starts from scratch, "
        "otherwise, it resumes from the pre-trained model.")
add_arg('decoding_method',  str,
        'ctc_beam_search',
        "Decoding method. Options: ctc_beam_search, ctc_greedy",
        choices = ['ctc_beam_search', 'ctc_greedy'])
add_arg('error_rate_type',  str,
        'wer',
        "Error rate type for evaluation.",
        choices=['wer', 'cer'])
add_arg('specgram_type',    str,
        'linear',
        "Audio feature type. Options: linear, mfcc.",
        choices=['linear', 'mfcc'])
# yapf: disable
args = parser.parse_args()


def infer(transcript_name):
    """Inference for DeepSpeech2."""

    # check if set use_gpu=True in paddlepaddle cpu version
    check_cuda(args.use_gpu)
    # check if paddlepaddle version is satisfied
    check_version()

    if args.use_gpu:
        place = fluid.CUDAPlace(0)
    else:
        place = fluid.CPUPlace()

    data_generator = DataGenerator(
        vocab_filepath=args.vocab_path,
        mean_std_filepath=args.mean_std_path,
        augmentation_config='{}',
        specgram_type=args.specgram_type,
        keep_transcription_text=True,
        place = place,
        is_training = False)
    batch_reader = data_generator.batch_reader_creator(
        manifest_path=args.infer_manifest,
        batch_size=args.num_samples,
        sortagrad=False,
        shuffle_method=None)
    infer_data = next(batch_reader())

    ds2_model = DeepSpeech2Model(
        vocab_size=data_generator.vocab_size,
        num_conv_layers=args.num_conv_layers,
        num_rnn_layers=args.num_rnn_layers,
        rnn_layer_size=args.rnn_layer_size,
        use_gru=args.use_gru,
        share_rnn_weights=args.share_rnn_weights,
        place=place,
        init_from_pretrained_model=args.model_path)

    # decoders only accept string encoded in utf-8
    vocab_list = [chars.encode("utf-8") for chars in data_generator.vocab_list]

    if args.decoding_method == "ctc_greedy":
        ds2_model.logger.info("start inference ...")
        probs_split = ds2_model.infer_batch_probs(
            infer_data=infer_data,
            feeding_dict=data_generator.feeding)

        result_transcripts = ds2_model.decode_batch_greedy(
            probs_split=probs_split,
            vocab_list=vocab_list)
    else:
        ds2_model.init_ext_scorer(args.alpha, args.beta, args.lang_model_path,
                                  vocab_list)
        ds2_model.logger.info("start inference ...")
        probs_split= ds2_model.infer_batch_probs(
            infer_data=infer_data,
            feeding_dict=data_generator.feeding)

        result_transcripts= ds2_model.decode_batch_beam_search(
            probs_split=probs_split,
            beam_alpha=args.alpha,
            beam_beta=args.beta,
            beam_size=args.beam_size,
            cutoff_prob=args.cutoff_prob,
            cutoff_top_n=args.cutoff_top_n,
            vocab_list=vocab_list,
            num_processes=args.num_proc_bsearch)

    transcription = result_transcripts[0].capitalize() + '.'
    print(transcription)

    with codecs.open('dataset/tap/transcription/'+transcript_name+'.txt', 'w', 'utf-8') as out_file:
        out_file.write(transcription)

    ds2_model.logger.info("finish inference")

def main():
    print_arguments(args)
    infer('transcript')

if __name__ == '__main__':
    main()
