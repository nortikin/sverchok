*************************
Contributing small things
*************************

Thanks for taking the time to read this document, we gladly accept code/doc contributions. For whatever reason you want to change or add code to Sverchok, that's cool. We will always consider the proposed changes in light of our understanding of Sverchok as a whole. Sverchok's code base is large and in a few places challenging to comprehend. If we don't think it's appropriate to accept your suggestion we'll defend our position. Usually we can come to some compromise that makes sense for sverchok, yet also satisfies the amicable contributor.


Pull Requests
=============

A pull request (PR) is what you might consider a "formal suggested edit" to Sverchok. You do this either via the online Git tools provided by GitHub / or via GIT. Newcomers to git should probably user the online GitHub mechanisms for doing small edits. See GitHub's guide to PRs.

We accept one-liner PRs, but might also reject them and instead add the same (or similar) code modifications to our own frequent PR streaks. We'll then add a comment in the commit to acknowledge your input.


Informal code suggestions
=========================

If you don't want to go through a git / github interface you can suggest an edit using the issue tracker. Open a new issue, state succintly in the title what the edit hopes to achieve. In the issue you can use Markdown to show us which code you're talking about and what changes you'd like to make. 

You can copy / paste a permalink into the issue to show the immediate area of the code you're interested int. And below it write the following "differential". 

In the following file: sverchok/nodes/scene/frame_info.py on line 122

.. code-block :: diff

   - print(some_variable)
   + # print(some_variable)

This would indicate that you came across a runaway print statement and would like us to remove it with a comment for now.


Non one-liners
==============

Sometimes a small contribution is 2 or more lines. It's hard to define where the term "small contribtion" becomes inaccurate to describe your proposal. We'll know it when we see it. We also accept code block rewrites or function replacements. The more you propose to change the more we will want to see profiling/performance evidence to defend your claim. 

What gets our attention
=======================

Everything. We tend to be more lenient/rapid if your code proposal fixes a real flaw in existing code, and doesn't involve changing too much outside of the area in question.


General guidelines
==================

The document you should be reading to get a sense of how we'd like contributed code to look and behave is [here].

