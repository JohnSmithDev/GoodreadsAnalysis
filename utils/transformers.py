#!/usr/bin/env python3
"""
Classes/functions to transform raw data for reports - perhaps 'engines' might
be a better name?
"""

from __future__ import division

from collections import defaultdict, namedtuple
from functools import cmp_to_key

from utils.display import render_ratings_as_bar

# TODO (maybe): ReadVsUnreadStats() and best_ranked_report() have different
#               defaults for ignore_single_book_groups - this could be
#               confusing?  The reasoning for the current status quo is:
#               * For ReadVsUnread groups, any number of read or unread is
#                 relevant
#               * For group ranking, only having a single rank is not considered
#                 sufficient representation to be meaningful

ReadVsUnreadStat = namedtuple('ReadVsUnreadStat', 'key, percentage_read, difference')
def compare_rvustat(a, b):
    if a.percentage_read == b.percentage_read:
        diff_difference = abs(b.difference) - abs(a.difference)
        if diff_difference == 0:
            return 1 if a.key > b.key else -1 # Use the key as a last resort
        else:
            return diff_difference
    else:
        return a.percentage_read - b.percentage_read


class ReadVsUnreadReport(object):
    def __init__(self, books, key_attribute, ignore_single_book_groups=True,
                 ignore_undefined_book_groups=True):
        # Would be nice to use counters, but I dunno if that's possible for two
        # counters and a generator?
        self.unread_count = defaultdict(int)
        self.read_count = defaultdict(int)
        self.grouping_count = defaultdict(int) # More efficient than unioning keys of the count dicts?
        self.ignore_single_book_groups = ignore_single_book_groups

        for book in books:
            for key in book.property_as_sequence(key_attribute):
                if key or not ignore_undefined_book_groups:
                    self.grouping_count[key] += 1
                    if book.is_unread:
                        self.unread_count[key] += 1
                    else:
                        self.read_count[key] += 1

    def process(self):
        self.stats = []
        for key in self.grouping_count:
            rd = self.read_count[key]
            ur = self.unread_count[key]
            if self.ignore_single_book_groups and (rd + ur) == 1:
                continue
            try:
                stat = ReadVsUnreadStat(key, int(100 * (rd / (rd+ur))) , rd - ur)
                self.stats.append(stat)
            except ZeroDivisionError as err:
                # Q: Can this actually happen, or am I just being over-paranoid?
                logging.warning('%s has %d read, %d unread' % (key, rd, ur))
        return self # For method chaining

    def render(self, output_function=print):
        for stat in sorted(self.stats, key=cmp_to_key(compare_rvustat)):
            output_function('%-30s : %5d%% %+3d %3d' % (str(stat[0])[:30], stat[1], stat[2],
                                             self.grouping_count[stat[0]]))



BestRankedStat = namedtuple('BestRankedStat',
                            'key, average_rating, number_of_books_rated')
def compare_brstat(a, b):
    if a.average_rating == b.average_rating:
        return b.number_of_books_rated - a.number_of_books_rated
    else:
        return int(1000 * (b.average_rating - a.average_rating)) # Has to be an int for some reason

class BestRankedReport(object):

    def __init__(self, books, key_attribute,
                       ignore_single_book_groups=False,
                       ignore_undefined_book_groups=True):
        self.ignore_single_book_groups = ignore_single_book_groups

        self.rated_count = defaultdict(int) # TODO: rename as rated_count
        self.cumulative_rating = defaultdict(int)
        # TODO (maybe): could/should this be a namedtuple or class?
        self.rating_groupings = defaultdict(lambda: [None, 0,0,0,0,0])

        for book in books:
            br = book.rating
            if br:
                for key in book.property_as_sequence(key_attribute):
                    if key or not ignore_undefined_book_groups:
                        self.rated_count[key] += 1
                        self.cumulative_rating[key] += br
                        self.rating_groupings[key][br] += 1

    def process(self):
        # TODO (maybe): Should ingore_single_book_groups be an argument here,
        #               rather than in the constructor?
        self.stats = []
        for k, rdr in self.rated_count.items():
            av = self.cumulative_rating[k] / rdr
            if not self.ignore_single_book_groups or rdr > 1:
                self.stats.append(BestRankedStat(k, av, rdr))
        return self # For method chaining

    def render(self, output_function=print, sort_by_ranking=True,
               output_bars=True):
        if sort_by_ranking:
            sorting_key=cmp_to_key(compare_brstat)
        else:
            # Sort by name order
            sorting_key=lambda z: z.key

        for stat in sorted(self.stats, key=sorting_key):
            # Standard deviation would be good too, to gauge (un)reliability
            if output_bars:
                bars = ' ' + render_ratings_as_bar(self.rating_groupings[stat.key])
            else:
                bars = ''
            output_function('%-30s : %.2f %4d%s' % (stat.key, stat.average_rating,
                                                    stat.number_of_books_rated, bars))


def best_ranked_report(books, key_attribute, output_function=print, sort_by_ranking=True,
                       ignore_single_book_groups=False,
                       ignore_undefined_book_groups=True):
    brr = BestRankedReport(books, key_attribute, ignore_single_book_groups,
                           ignore_undefined_book_groups)
    brr.process()
    brr.render(output_function, sort_by_ranking)



def get_keys_to_books_dict(books, key_attribute,
                           ignore_undefined_book_groups=True):
    """
    Return a dictionary mapping some keys (e.g. shelves, dictionaries, etc)
    to sets of Books
    """

    ret_dict = defaultdict(set)
    for book in books:
        for key in book.property_as_sequence(key_attribute):
            if key or not ignore_undefined_book_groups:
                ret_dict[key].add(book)
    return ret_dict
