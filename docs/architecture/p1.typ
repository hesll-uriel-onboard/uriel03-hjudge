#import "config.typ": *
= Introduction

#slide(title: [])[As a coach, I want to train my trainees by creating weekly problemsets, and monitor their progress.
]
#slide(title: [Context])[
	Nowadays, a lot of Online Judges, e.g. Codeforces, AtCoder
		- each has its strength
	
	#pause
	Creating a decent problemset \
	$<=>$ combining problems from different OJs\
	#pause $<=>$ *difficult to monitor*

	#pause
	$=>$ need a tool to integrate all OJ
]
#slide(title: [Context])[
	Current solutions:
	#table(
		columns: (auto, auto, auto),
		inset: 10pt,
		align: horizon,
		table.header(
			[], [*USACO Guide's Group*], [*VJudge*],
		),
		"Support", "All popular judges", "All popular judges",
		"Lesson management", sym.checkmark, [#sym.checkmark],
		"Submit", sym.diameter, sym.checkmark,
		"See submissions", sym.diameter, sym.diameter,
	)
]
#slide(title: [Problem definition])[
	Main problem:
	- System can import _any_ *exercise* from _any #underline[supported]_ *Judge*.
	- System can crawl _all_ *submissions* of _all_ *users* related to the _imported_ *exercise*
		- *User* will provide its *handles* (a.k.a username) of each respective *Judge*.

	#pause
	Side problem:
	- *User* can create *Course*, and become *CourseAdmin*
	- *CourseAdmin* can create *Lesson* in a *Course*
	- *CourseAdmin* can import *Exercise* to a *Lesson*
	- There exists a mechanism to track the *progress* of the *participants*
]
#slide(title: [Problem definition -- Assumption])[
	1. The existence of an exercise or a submission is eternity, i.e. it will never be deleted.
	2. The content of a submission is never changed.
	3.  The title of a problem is never changed.

	#pause (temporarily)
	4. *User* never change their *handle*
]
#slide(title: [Problem definition -- Glossary])[
	+ *Judge*(s): a system that contains exercises to solve, and could execute and evaluate programs from the user that attempt solve an exercise.
	+ *Exercise*: a problem of a Judge #footnote[I decided to use the word "Exercise" instead of "Problem"]
	+ *Submission*: a program in the form of code, that the user submits, and evaluated by the Judge
	+ *Verdict* of a Submission:
		- Accepted
		- Rejected, because of: Time-Limit-Exceed, Wrong-Answer, Runtime-Error, Compile-Error, etc.
]