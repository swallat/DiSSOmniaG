*text*

**text**

``text``

this is \ *one*\  word.

:emphasis:`emphasis`

:strong:`strong`

:literal:`literal``

:subscript:`subscript`
sss

:superscript:`superscript`
sss

:title-reference:`title-reference`
sss

*   This is a bulleted list.
*   It has two items, the second
    item uses two lines.


1.  This is a numbered list.
2.  It has two items too.

#.  This is a numbered list with #.
#.  It has two items too.


*  this is
*  a list

   *  with a nested list
   *  and some subitems

*  and here the parent list continues


term (up to a line of text)
   Definition of the term, which must be indented

   and can even consist of multiple paragraphs

next term
   Description.


This is an ordinary paragraph, introducing a block quote.

    "It is my business to know things.  That is my trade."

    -- Sherlock Holmes

FieldList:


:Date: 2001-08-16
:Version: 1
:Authors: - Me
          - Myself
          - I
:Indentation: Since the field marker may be quite long, the second
   and subsequent lines of the field body do not have to line up
   with the first line, but they must be indented relative to the
   field name marker, and they must line up with each other.
:Parameter i: integer



| These lines are
| broken exactly like in
| the source file.


OptionsList:


-a         Output all.
-b         Output both (this description is
           quite long).
-c arg     Output just arg.
--long     Output all day long.

-p         This option has two paragraphs in the description.
           This is the first.

           This is the second.  Blank lines may be omitted between
           options (as above) or left in (as here and below).

--very-long-option  A VMS-style option.  Note the adjustment for
                    the required two spaces.

--an-even-longer-option
           The description can also start on the next line.

-2, --two  This option has two variants.

-f FILE, --file=FILE  These two options are synonyms; both have
                      arguments.


Quoted Literal Blocks:


John Doe wrote::

>> Great idea!
>
> Why didn't I think of that?

You just did!  ;-)


Doctest Blocks:

This is an ordinary paragraph.

>>> print 'this is a Doctest block'
this is a Doctest block

The following is a literal block::

    >>> This is not recognized as a doctest block by
    reStructuredText.  It *will* be recognized by the doctest
    module, though!


Source Code:


This is a normal text paragraph. The next paragraph is a code sample::

   It is not processed in any way, except
   that the indentation is removed.

   It can span multiple lines.

This is a normal text paragraph again.

Table:

+------------------------+----------+----------+----------+
| Header row, column 1   | Header 2 | Header 3 | Header 4 |
| (header rows optional) |          |          |          |
+========================+==========+==========+==========+
| body row 1, column 1   | column 2 | column 3 | column 4 |
+------------------------+----------+----------+----------+
| body row 2             | ...      | ...      |          |
+------------------------+----------+----------+----------+


SimpleTable:

=====  =====  =======
A      B      A and B
=====  =====  =======
False  False  False
True   False  False
False  True   False
True   True   True
=====  =====  =======


External Link:

`Link text <http://example.com/>`_


External Link with variable:

This is a paragraph that contains `a link`_.

.. _a link: http://example.com/

##########
Part Title
##########

*************
Chapter Title
*************

=============
Section Title
=============

----------------
Subsection Title
----------------

Subsubsection Title
===================

Subsubsubsection Title
----------------------

Paragraph Title
"""""""""""""""

A. Einstein was a really
smart dude.

.. danger::
   Beware killer rabbits!
   
.. attention::
   Beware killer rabbits!

.. caution::
   Beware killer rabbits!
   
.. error:: 
   Beware killer rabbits!
   
.. hint::
   Beware killer rabbits!
   
.. important:: 
   Beware killer rabbits!

.. note:: This is a paragraph

   - Here is a bullet list.
   
.. tip::
   Beware killer rabbits!
   
.. warning:: 
   Beware killer rabbits!


.. admonition:: And, by the way...

   You can make up your own admonition too.


.. container:: custom

   This paragraph might be rendered in a custom way.

.. topic:: Topic Title

    Subsequent indented lines comprise
    the body of the topic, and are
    interpreted as body elements.
    
.. sidebar:: Sidebar Title
   :subtitle: Optional Sidebar Subtitle

   Subsequent indented lines comprise
   the body of the sidebar, and are
   interpreted as body elements.
     
.. epigraph::

   No matter where you go, there you are.

   -- Buckaroo Banzai
   
.. compound::

   The 'rm' command is very dangerous.  If you are logged
   in as root and enter ::

       cd /
       rm -rf *

   you will erase the entire contents of your file system.
   

.. list-table:: Frozen Delights!
   :widths: 15 10 30
   :header-rows: 1

   * - Treat
     - Quantity
     - Description
   * - Albatross
     - 2.99
     - On a stick!
   * - Crunchy Frog
     - 1.49
     - If we took the bones out, it wouldn't be
       crunchy, now would it?
   * - Gannet Ripple
     - 1.99
     - On a stick!
   

Lorem ipsum [#f1]_ dolor sit amet ... [#f2]_

.. rubric:: Footnotes

.. [#f1] Text of the first footnote.
.. [#f2] Text of the second footnote.


Lorem ipsum [Ref]_ dolor sit amet.

.. [Ref] Book or article reference, URL or whatever.

API

.. automodule:: dissomniag
   :members:

.. automodule:: dissomniag.server
   :members:

.. automodule:: dissomniag.initMigrate
   :members:

.. automodule:: dissomniag.auth.User
   :members:

.. autoclass:: dissomniag.auth.User.User
   :members:

.. automodule:: dissomniag.dbAccess
   :members:
