#!/usr/bin/env python3
# coding: utf-8
import argparse
import re
import sys
import codecs

utf8_to_ascii = {u'\u0660':'0', u'\u0661':'1', u'\u0662':'2', \
                u'\u0663':'3', u'\u0664':'4', u'\u0665':'5', \
                u'\u0666':'6', u'\u0667':'7', u'\u0668':'8', \
                u'\u0669':'9', u'\u06F0':'0', u'\u06F1':'1', \
                u'\u06F2':'2', u'\u06F3':'3', u'\u06F4':'4', \
                u'\u06F5':'5', u'\u06F6':'6', u'\u06F7':'7', \
                u'\u06F8':'8', u'\u06F9':'9'}

#Patterns
#Match any character not in the Arabic charts
#Including presentation forms
p_not_arb = re.compile(u'[^\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]',re.U)

#Segment punctuation
latin_punc = re.compile(u'([\u0021-\u002F\u003A-\u0040\u005B-\u0060\u007B-\u007E\u00A1-\u00BF\u2010-\u2027\u2030-\u205E\u20A0-\u20B5\u2E2E]{1})',re.U)
arb_punc = re.compile(u'([\u0609-\u060D\u061B-\u061F\u066A\u066C-\u066D\u06D4]{1})',re.U)
other_punc = re.compile(u'([\u2E2E]{1})',re.U)

#Segment digits
ascii_digit = re.compile(r'(\d+)',re.U)
arb_digit = re.compile(u'([\u06F0-\u06F9\u0660-\u0669]+)',re.U)

#Patterns commonly found in newswire (e.g., the ATB)
date_cluster = re.compile(r'\d+\-\d+',re.U)
email_cluster = re.compile(r'[\w\-][\w\-\.]+@[\w\-][\w\-\.]+[a-zA-Z]{1,4}',re.U)
url_cluster = re.compile(r'[a-zA-Z]+.[a-zA-Z]+',re.U)
ellipsis = re.compile(r'(\.{2,})',re.U)

#Strip diacritics, tatweel, extended Arabic
p_diac = re.compile(u'[\u064B-\u0652]',re.U)
#p_tat = re.compile(u'ـ',re.U)
p_tat = re.compile(u'\u0640',re.U)
p_quran = re.compile(u'[\u0615-\u061A\u06D6-\u06E5]',re.U)

#Normalize alif
#p_alef = re.compile(u'ا|إ|أ|آ|\u0671',re.U)
#p_alef = re.compile(u'\u0627|\u0625|\u0623|\u0622|\u0671',re.U)
p_alef = re.compile(u'\u0627',re.U)

#Escape Basic Latin (U0000) and Latin-1 (U0080) characters
p_latin = re.compile(u'[\u0000-\u00FF]',re.U)


def arb_digit_to_ascii(string):
    global utf8_to_ascii
    ascii_digits = []
    for c_idx in range(0,len(string)):
        new_digit = utf8_to_ascii[string[c_idx]]
        if new_digit:
            ascii_digits.append(new_digit)
        else:
            return string
    return ''.join(ascii_digits)


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
            elif date_cluster.match(word):
                tokens.append(word)
            elif email_cluster.match(word):
                tokens.append(word)
            elif url_cluster.match(word):
                tokens.append(word)
            elif ellipsis.search(word):
                tokens.extend(ellipsis.sub(r' \1' ,word).split())
            else:
                word = latin_punc.sub(r' \1 ', word)
                word = other_punc.sub(r' \1 ',word)
                word = arb_punc.sub(r' \1 ',word)
                word = ascii_digit.sub(r' \1 ',word)
                word = arb_digit.sub(r' \1 ',word)
                tokens.extend(word.split())

        res = []
        for word in tokens:
            if p_latin.match(word):
                res.append(word)
            elif arb_digit.match(word):
                asciified = arb_digit_to_ascii(word)
                res.append(asciified)
            elif word == u'\u060C':
                res.append(u',')
            elif word == u'\u061F' or word == u'\u2E2E':
                res.append(u'?')
            else:
                w1 = p_diac.sub('',word)
                w2 = p_tat.sub('',w1)
                #w3 = p_alef.sub(u'ا',w2)
                w3 = p_alef.sub(u'\u0627',w2)
                w4 = p_quran.sub('',w3)
                res.append(w4)
        print(' ' .join(res))
        line = f.readline()


if __name__ == '__main__':
    main()
