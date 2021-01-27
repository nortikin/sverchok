Strings Tools
=============

Functionality
-------------

This node allows operating with strings with many common methods.

Parameters
----------

This node has the following parameters:

+--------------------+-------------------------------------------------------------+-----------------------+-------------+
| Function           | Description                                                 | Options               | Output      |
+====================+=============================================================+=======================+=============+
|**To String**       | Transforms inputs to strings.                               | 'Level'               | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**To Number**       | Transforms strings to numbers.                              |                       | Number      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Join**            | Join two strings.                                           |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Join All**        | Joins a list of strings into one single string              | 'Add Break Lines'     | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Split**           | Split string by a character into a maximum numbers of       | 'Character': Splitter | String List |
|                    | slices                                                      | 'Max Splits'          |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Split Lines**     | Splits the string at line breaks and returns a list         |                       | String List |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Left Partition**  | Returns a tuple where the string is parted into three       |                       | String List |
|                    | parts. Before defined value, the value (first occurrence),  |                       |             |
|                    | and the rest of the string                                  |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Right Partition** | Returns a tuple where the string is parted into three       |                       | String List |
|                    | parts. Before defined value, the value (last occurrence),   |                       |             |
|                    | and the rest of the string                                  |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find First**      | Searches the string for a specified value and returns the   | 'Start': Slice Start  | Number      |
|                    | first position of where it was found                        | 'End': Slice End      |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find First Slice**| Searches a slice of the string for a specified value and    | 'Start': Slice Start  | Number      |
|                    | returns the first position of where it was found            | 'End': Slice End      |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find Last**       | Searches the string for a specified value and returns the   |                       | Number      |
|                    | last position of where it was found                         |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find Last Slice** | Searches a slice of the string for a specified value and    | 'Start': Slice Start  | Number      |
|                    | returns the last position of where it was found             | 'End': Slice End      |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find All**        | Searches the string for a specified value and returns all   |                       | Number      |
|                    | the positions of where it was found                         |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Find All Slice**  | Searches a slice of the string for a specified value and    | 'Start': Slice Start  | Number      |
|                    | returns all the positions of where it was found             | 'End': Slice End      |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Count**           | Returns the number of times a specified value occurs in a   |                       | Number      |
|                    | string                                                      |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Replace**         | Returns a string where a specified value is replaced with a | 'Find', 'Replace'     | String      |
|                    | specified value                                             | 'Count': -1 = all     |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Lower**           | Converts a string into lower case                           |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Upper**           | Converts a string into upper case                           |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Capitalize**      | Converts the first character to upper case                  |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Title**           | Converts the first character of each word to upper case     |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Casefold**        | Converts string into lower case                             |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Swapcase**        | Swaps cases, lower case becomes upper case and vice versa   |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Strip**           | Returns a trimmed version of the string                     |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Left Strip**      | Returns a left trim version of the string                   |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Right Strip**     | Returns a right trim version of the string                  |                       | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Left Justify**    | Returns a left justified version of the string              | 'Length': Line Length | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Center**          | Returns a centered string                                   | 'Length': Line Length | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Right Justify**   | Returns a right justified version of the string             | 'Length': Line Length | String      |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+
|**Zeros Fill**      | Fills the string with a specified number of 0 values at     | 'Length': Line Length | String      |
|                    | the beginning                                               |                       |             |
+--------------------+-------------------------------------------------------------+-----------------------+-------------+

+--------------------+-------------------------------------------------------------+
| **Booleans**       |                                                             |
+====================+=============================================================+
|**Starts With**     | Returns True if the string starts with defined character    |
+--------------------+-------------------------------------------------------------+
|**Ends With**       | Returns True if the string ends with defined character      |
+--------------------+-------------------------------------------------------------+
|**Is Alphanumeric** | Returns True if the string is made by letters and numbers   |
+--------------------+-------------------------------------------------------------+
|**Is Alphabetic**   | Returns True if the string is made by letters               |
+--------------------+-------------------------------------------------------------+
|**Is Digit**        | Returns True if the string is made by numbers               |
+--------------------+-------------------------------------------------------------+
|**Is Lower**        | Returns True if all the characters are in lower case        |
+--------------------+-------------------------------------------------------------+
|**Is Space**        | Returns True if all characters in the string are whitespaces|
+--------------------+-------------------------------------------------------------+
|**Is Title**        | Returns True if the string follows the rules of a title     |
+--------------------+-------------------------------------------------------------+
|**Is Upper**        | Returns True if all characters in the string are upper case |
+--------------------+-------------------------------------------------------------+


Outputs
-------

This node has only one output: it can output Strings or Numbers or Booleans

Examples
--------

Placing measures:

.. image:: https://user-images.githubusercontent.com/10011941/104808380-0e5cf600-57e6-11eb-9240-3f80df8c21c7.png

Splitting Text:

.. image:: https://user-images.githubusercontent.com/10011941/104808922-98f32480-57e9-11eb-9b43-672a60c5a898.png
