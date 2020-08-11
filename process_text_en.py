#!/usr/bin/env python3
import argparse
import re
import sys
import inflect
import codecs
import calendar
from unidecode import unidecode

# """ from https://github.com/keithito/tacotron """
_inflect = inflect.engine()
_comma_number_re = re.compile(r'([0-9][0-9\,]+[0-9])')
_decimal_number_re = re.compile(r'([0-9]+\.[0-9]+)')
_pounds_re = re.compile(r'£([0-9\,]*[0-9]+)')
_dollars_re = re.compile(r'\$([0-9\.\,]*[0-9]+)')
_ordinal_re = re.compile(r'[0-9]+(st|nd|rd|th)')
_number_re = re.compile(r'[0-9]+')
# process % , time, date
_percent_re = re.compile(r'%')
_time_re = re.compile(r'([0-1]?[0-9]):([0-5]?[0-9])')


def _expand_time(m):
  hour = _inflect.number_to_words(m.group(1))
  t2 = int(m.group(2))
  if t2 > 0:
    minute = _inflect.number_to_words(t2)
  else:
    minute = ''
  return ' ' + hour + ' ' + minute + ' '


# Not necessary!!!
# _date_re = re.compile(r'([0-1]?[0-9])\/([0-3]?[0-9])\/([0-9]+)') # MM/DD/YY
# def _expand_date(m):
#   month = calendar.month_name[int(m.group(1))]
#   date = _inflect.number_to_words(m.group(2) + 'th')
#   year = int(m.group(3))
#   if year % 100 > 10:
#     year = _inflect.number_to_words(year, andword='', zero='oh', group=2).replace(', ', ' ')
#   else:
#     year = _inflect.number_to_words(year)
  
#   return ' {} {} {} '.format(month, date, year)


def _remove_commas(m):
  return m.group(1).replace(',', '')


def _expand_decimal_point(m):
  return _inflect.number_to_words(m.group(0))


def _expand_dollars(m):
  match = m.group(1)
  parts = match.split('.')
  if len(parts) > 2:
    return match + ' dollars'  # Unexpected format
  dollars = int(parts[0]) if parts[0] else 0
  cents = int(parts[1]) if len(parts) > 1 and parts[1] else 0
  if dollars and cents:
    dollar_unit = 'dollar' if dollars == 1 else 'dollars'
    cent_unit = 'cent' if cents == 1 else 'cents'
    return '%s %s, %s %s' % (dollars, dollar_unit, cents, cent_unit)
  elif dollars:
    dollar_unit = 'dollar' if dollars == 1 else 'dollars'
    return '%s %s' % (dollars, dollar_unit)
  elif cents:
    cent_unit = 'cent' if cents == 1 else 'cents'
    return '%s %s' % (cents, cent_unit)
  else:
    return 'zero dollars'


def _expand_ordinal(m):
  return _inflect.number_to_words(m.group(0))


def _expand_number(m):
  num = int(m.group(0))
  if num > 1000 and num < 3000:
    if num == 2000:
      res =  'two thousand'
    elif num > 2000 and num < 2010:
      res = 'two thousand ' + _inflect.number_to_words(num % 100)
    elif num % 100 == 0:
      res = _inflect.number_to_words(num // 100) + ' hundred'
    else:
      res = _inflect.number_to_words(num, andword='', zero='oh', group=2).replace(', ', ' ')
  else:
    res = _inflect.number_to_words(num, andword='')

  return ' ' + res + ' '


def normalize_numbers(text):
  text = re.sub(_comma_number_re, _remove_commas, text)
  text = re.sub(_pounds_re, r'\1 pounds ', text)
  text = re.sub(_percent_re, r' percentage ', text)
  text = re.sub(_time_re, _expand_time, text)
  text = re.sub(_dollars_re, _expand_dollars, text)
  text = re.sub(_decimal_number_re, _expand_decimal_point, text)
  text = re.sub(_ordinal_re, _expand_ordinal, text)
  text = re.sub(_number_re, _expand_number, text)
  return text


# Regular expression matching whitespace:
_whitespace_re = re.compile(r'\s+')

# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [(re.compile('\\b%s\\.' % x[0], re.IGNORECASE), x[1]) for x in [
  ('mrs', 'misess'),
  ('mr', 'mister'),
  ('dr', 'doctor'),
  ('st', 'saint'),
  ('co', 'company'),
  ('jr', 'junior'),
  ('maj', 'major'),
  ('gen', 'general'),
  ('drs', 'doctors'),
  ('rev', 'reverend'),
  ('lt', 'lieutenant'),
  ('hon', 'honorable'),
  ('sgt', 'sergeant'),
  ('capt', 'captain'),
  ('esq', 'esquire'),
  ('ltd', 'limited'),
  ('col', 'colonel'),
  ('ft', 'fort'),
]]


def expand_abbreviations(text):
  for regex, replacement in _abbreviations:
    text = re.sub(regex, replacement, text)
  return text


def expand_numbers(text):
  return normalize_numbers(text)


def lowercase(text):
  return text.lower()


def collapse_whitespace(text):
  return re.sub(_whitespace_re, ' ', text)


def convert_to_ascii(text):
  return unidecode(text)

def english_cleaners(text):
  '''Pipeline for English text, including number and abbreviation expansion.'''
  text = convert_to_ascii(text)
  text = lowercase(text)
  text = expand_numbers(text)
  text = expand_abbreviations(text)
  text = collapse_whitespace(text)
  return text
# """ from https://github.com/keithito/tacotron end"""


_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
# _valid_sym = list(_letters) + ['\'', '-', ' ']
_valid_sym = list(_letters) + ['\'', ' ']

quota_underline_re = re.compile(r'^[\'\-]|[\'\-]$')

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
            print(" ".join(x[:args.skip_ncols]), end=" ")
        text = x[args.skip_ncols:]
        tokens = []
        for word in text:
            if match_rs(word, rs):
                tokens.append(word)
            else:
                word = english_cleaners(word)
                res = ''
                for char in word:
                    if char in _valid_sym:
                        res += char
                    else:
                        res += ' '

                for w in res.split():
                  while quota_underline_re.search(w):
                    w = quota_underline_re.sub('', w)
                  if w != '':
                    tokens.append(w)

        print(' '.join(tokens).lower())
        line = f.readline()


if __name__ == "__main__":
    main()
