#import "config.typ": *
= Components

#slide(title: [OJService])[
	*Responsibility:*
	- Handle all tasks relating to integration with various Online Judges

	*Features:*
	- Crawl the content of an exercise
	- Schedulely crawl latest submissions of users in supported Judges
	- Given an exercise and a user, return respective submissions and URLs
]
#slide(title: [LMService])[
	*Responsibility and Features:*
	- Crawl the content of an exercise
	- Schedulely crawl submissions of users in supported Judges, and linked to its urls

	*Features*
	- Creating and updating courses and lessons
	- Monitor the progress of participants
]	

= Process

#slide(title: [Pattern used])[
	- Abstract Factory: 
		- given a DB service, yield a Unit-of-Work which is a Repository factory
		- given the crawler service, yield a Judge factory
	- Singleton: 
		- for each UoW, only one instance per type of Repository are created.
]	
#slide(title: [How I created a functionality])[
	1. Define the model class
		- defined the functionality
		- necessary fields and methods
	
	#pause
	2. Define the necessary entity of the respective class
		- cannot make model as entity, as after `session.commit()`, data is inaccessible because they are expired.
	
	#pause
	3. Define the Repository
		- basic CRUD
		- separate the logic of DB from services
]	

#slide(title: [How I created a functionality])[
	Each functionality corresponds to one endpoint, which corresponds to one function service.

	#pause
	4. Define the service functions
		- The params are inject with an `AbstractUnitOfWork` and sometimes `JudgeFactory`
	
	#pause
	5. Define the endpoints
		- Litestar backend is inject with an `AbstractUOWFactory` and `JudgeFactory` (as which judge to choose is decided in the service layer)
]	