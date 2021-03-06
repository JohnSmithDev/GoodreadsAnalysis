#!/usr/bin/env python3

from datetime import date
from decimal import Decimal
import unittest

from ..book import Book, NotOwnedAtSpecifiedDateError

class TestBook(unittest.TestCase):

    MOCK_BOOK = {
        'Title': 'A Mock Book',
        'Author': 'Mick Mock',
        'Additional Authors': 'Terry Test, Peter Python', # .additional_authors, .all_authors
        'Original Publication Year': '2001',
        'Publisher': 'Mock Corp',
        'Year Published': '2002',
        'Number of Pages': '123',
        'Binding': 'Paperback',
        'Average Rating': '1.23',
        'Book Id': '12345678',

        'Exclusive Shelf': 'read',
        'Bookshelves': 'testing, mocking, software, python',
        'My Rating': '4',
        'Date Added': '2012/12/22',
        'Date Read': '2015/12/25',
        'Read Count': '1',
    }

    def test_book_basic(self):
        bk = Book(self.MOCK_BOOK)
        self.assertEqual(2001, bk.year)
        self.assertTrue(bk.is_read)
        self.assertFalse(bk.is_unread)
        self.assertIsNone(bk.series)
        self.assertEqual('2000s', bk.decade)
        self.assertEqual(2015, bk.year_read)
        self.assertEqual('2015-12', bk.month_read)
        self.assertEqual(2012, bk.year_added)
        self.assertEqual('2012-12', bk.month_added)
        self.assertEqual('100-149', bk.pagination_range)
        self.assertEqual('****', bk.rating_as_stars)
        self.assertEqual('**** ', bk.padded_rating_as_stars)

        self.assertEqual(['mocking', 'python', 'read', 'software', 'testing'],
                         sorted(bk.shelves))
        self.assertEqual({'mocking', 'python', 'software', 'testing'},
                         bk.user_shelves)

        self.assertEqual(['Peter Python', 'Terry Test'],
                         sorted(bk.additional_authors))
        self.assertEqual(['Mick Mock', 'Peter Python', 'Terry Test'],
                         sorted(bk.all_authors))

        self.assertEqual(['mocking', 'python', 'read', 'software', 'testing'],
                         sorted(bk.property_as_sequence('shelves')))
        self.assertEqual([4],
                         sorted(bk.property_as_sequence('rating')))

        self.assertEqual(('mocking', 'python', 'read', 'software', 'testing'),
                         bk.property_as_hashable('shelves'))
        self.assertEqual((4,),
                         bk.property_as_hashable('rating'))

        self.assertEqual(
            'Mick Mock - [A Mock Book](https://www.goodreads.com/book/show/12345678)',
            bk.markdown)

    def test_book_in_series_with_comma(self):
        # e.g. Tales From Earthsea (Earthsea Cycle, #5)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Overlong Fantasy Series, #13)'
        bk = Book(bdict)
        self.assertEqual(('Overlong Fantasy Series', '13'), bk._series_and_volume)
        self.assertEqual('Overlong Fantasy Series', bk.series)
        self.assertEqual('13', bk.volume_number)

    def test_book_in_series_no_comma(self):
        # e.g. The Space Merchants (The Space Merchants #1)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Overlong Fantasy Series #14)'
        bk = Book(bdict)
        self.assertEqual(('Overlong Fantasy Series', '14'), bk._series_and_volume)
        self.assertEqual('Overlong Fantasy Series', bk.series)
        self.assertEqual('14', bk.volume_number)

    def test_book_in_series_no_comma_or_hash(self):
        # e.g. 'Robots and Empire (Robot 4)'
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Overlong Fantasy Series 33)'
        bk = Book(bdict)
        self.assertEqual(('Overlong Fantasy Series', '33'), bk._series_and_volume)
        self.assertEqual('Overlong Fantasy Series', bk.series)
        self.assertEqual('33', bk.volume_number)

    def test_book_in_series_trilogy(self):
        # e.g. "Annihilation (Southern Reach Trilogy 1)"
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Fantasy Trilogy 3)'
        bk = Book(bdict)
        self.assertEqual(('Fantasy', '3'), bk._series_and_volume)
        self.assertEqual('Fantasy', bk.series)
        self.assertEqual('3', bk.volume_number)

    def test_book_in_series_trilogy_with_book_in_name(self):
        # e.g. Colossus and the Crab (Colossus Trilogy Book 3)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Fantasy Trilogy Book 3)'
        bk = Book(bdict)
        self.assertEqual(('Fantasy', '3'), bk._series_and_volume)
        self.assertEqual('Fantasy', bk.series)
        self.assertEqual('3', bk.volume_number)

    def test_book_in_series_compilation(self):
        # e.g. Helliconia (Helliconia, #1-3)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Overlong Fantasy Series #1-3)'
        bk = Book(bdict)
        self.assertEqual(('Overlong Fantasy Series', '1-3'), bk._series_and_volume)
        self.assertEqual('Overlong Fantasy Series', bk.series)
        self.assertEqual('1-3', bk.volume_number)

    def test_book_in_series_no_number(self):
        # e.g. Meeting Infinity (The Infinity Project)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'The Cliche of Cliches (Overlong Fantasy Series)'
        bk = Book(bdict)
        self.assertEqual(('Overlong Fantasy Series', None), bk._series_and_volume)
        self.assertEqual('Overlong Fantasy Series', bk.series)
        self.assertIsNone(bk.volume_number)

    def test_book_with_parens_but_not_in_series(self):
        # e.g. I Am (Not) A Number: Decoding The Prisoner
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'Foo (Bar) Baz'
        bk = Book(bdict)
        self.assertIsNone(bk._series_and_volume)
        self.assertIsNone(bk.series)
        self.assertIsNone(bk.volume_number)

    def test_book_with_multiple_series(self):
        # e.g. https://www.goodreads.com/book/show/24997006-dark-state?ac=1&from_search=true
        # (I don't own this book, so not sure if it actually shows up like this
        # in the export, but have seen this in some data on other pages)
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'Dark State (Empire Games #2, Merchant Princes Universe #8)'
        bk = Book(bdict)
        self.assertEqual(('Empire Games', '2'), bk._series_and_volume)
        self.assertEqual('Empire Games', bk.series)
        self.assertEqual('2', bk.volume_number)

    def test_book_with_comma_in_series_name(self):
        # Not seen a real-life example of this, but I imagine it's possible
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'Foo Bar (I Came, I Saw, I Conquered #3)'
        bk = Book(bdict)
        self.assertEqual(('I Came, I Saw, I Conquered', '3'), bk._series_and_volume)
        self.assertEqual('I Came, I Saw, I Conquered', bk.series)
        self.assertEqual('3', bk.volume_number)



    def test_book_series_prefix_stripping(self):
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'Foo (The Foo Chronicles, #1)'
        bk = Book(bdict)
        self.assertEqual(('Foo Chronicles', '1'), bk._series_and_volume)
        self.assertEqual('Foo Chronicles', bk.series)
        self.assertEqual('1', bk.volume_number)

    def test_book_non_integer_volume_number(self):
        # e.g. https://www.goodreads.com/book/show/34456370-the-furthest-station
        bdict = self.MOCK_BOOK.copy()
        bdict['Title'] = 'Foo (The Foo Chronicles, #3.4)'
        bk = Book(bdict)
        self.assertEqual(('Foo Chronicles', '3.4'), bk._series_and_volume)
        self.assertEqual('Foo Chronicles', bk.series)
        self.assertEqual('3.4', bk.volume_number)

    def test_book_historical_before_added(self):
        before_it_was_added = date(1980, 4, 1)

        with self.assertRaises(NotOwnedAtSpecifiedDateError):
            bk = Book(self.MOCK_BOOK, as_of_date=before_it_was_added)

    def test_book_historical_after_added_before_read(self):
        midpoint_time = date(2013, 4, 1)

        bk = Book(self.MOCK_BOOK, as_of_date=midpoint_time)
        self.assertFalse(bk.is_read)
        # Q: Re. next line, this is current behaviour, but is it correct?
        #    i.e. should bk.date_read be None instead?
        self.assertEqual(date(2015, 12, 25), bk.date_read)

        self.assertEqual(100, bk.days_on_tbr_pile) # Late 2012/12 - early 2013/04 = 3 +  bit months

    def test_book_was_owned_or_read_by(self):
        bk = Book(self.MOCK_BOOK)
        self.assertFalse(bk.was_owned_by(date(2002, 2, 2)))
        self.assertFalse(bk.was_read_by(date(2002, 2, 2)))

        self.assertTrue(bk.was_owned_by(date(2013, 2, 2)))
        self.assertFalse(bk.was_read_by(date(2013, 2, 2)))

        self.assertTrue(bk.was_owned_by(date(2016, 2, 2)))
        self.assertTrue(bk.was_read_by(date(2016, 2, 2)))

    def test_unrated_book(self):
        bdict = self.MOCK_BOOK.copy()
        bdict['My Rating'] = '0'
        bk = Book(bdict)
        self.assertIsNone(bk.rating)
        self.assertEqual('', bk.rating_as_stars)
        self.assertEqual('     ', bk.padded_rating_as_stars)
        self.assertIsNone(bk.rating_difference_from_average)

    def test_custom_format(self):
        bk = Book(self.MOCK_BOOK)
        self.assertEqual('AA Mock BookBMick MockC2001D',
                         bk.custom_format('A{title}B{author}C{year}D'))

    def test_patching(self):
        patches = [([('title', 'A Mock Book'), ('author', 'Mick Mock')],
                    [('year_published', '2019')]),
                   ([('author', 'Mick Mock')],
                   [('state', 'to-read')]),
                   ([('title', 'This Will Not Be Applied')],
                    [('pagination', '999')])]
        bk = Book(self.MOCK_BOOK, patches=patches)
        self.assertEqual('to-read', bk.state)
        self.assertEqual(2019, bk.year_published)
        # Next value may seem unexpected, but year is a computed property,
        # taking the min of year_published and originally_published_year
        self.assertEqual(2001, bk.year)

        self.assertEqual(123, bk.pagination) # And this didn't match, so no patch


if __name__ == '__main__':
    unittest.main()
