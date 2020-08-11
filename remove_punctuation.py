#!/usr/bin/env python3
# coding: utf-8
import argparse
import re
import sys
import codecs


#Segment punctuation
# latin_punc = re.compile(u'([\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]{1})',re.U)
latin_punc = re.compile(u'^[\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]|[\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E]$',re.U)
other_punc = re.compile(u'([\u00A1-\u00BF\u2010-\u2027\u2030-\u205E\u20A0-\u20B5\u2E2E]{1})',re.U)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Arabic text normalizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--skip-ncols", "-s", default=0, type=int, help="skip first n columns"
    )
    parser.add_argument(
        "--non-lang-syms",
        "-l",
        default=None,
        type=str,
        help="list of non-linguistic symobles, e.g., <NOISE> etc.",
    )
    parser.add_argument("text", type=str, default=False, nargs="?", help="input text")
    return parser


def match_rs(word, rs):
    for r in rs:
        if r.match(word):
            return True

    return False


def main():
    parser = get_parser()
    args = parser.parse_args()

    rs = []
    if args.non_lang_syms is not None:
        with codecs.open(args.non_lang_syms, "r", encoding="utf-8") as f:
            nls = [x.rstrip() for x in f.readlines()]
            rs = [re.compile(re.escape(x)) for x in nls]

    if args.text:
        f = codecs.open(args.text, encoding="utf-8")
    else:
        f = codecs.getreader("utf-8")(sys.stdin.buffer)

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer)
    line = f.readline()
    while line:
        x = line.split()
        if args.skip_ncols > 0:
            print(" ".join(x[: args.skip_ncols]), end=" ")

        tokens = []
        for word in x[args.skip_ncols:]:
            if match_rs(word, rs):
                tokens.append(word)
            else:
                while latin_punc.search(word):
                    word = latin_punc.sub('', word)
                while other_punc.search(word):
                    word = other_punc.sub(' ',word)
                tokens.extend(word.split())

        print(' ' .join(tokens))
        line = f.readline()


if __name__ == '__main__':
    main()
