README
*Authors: Andrew Tang and Raymond Fang
PostgreSQL Account for Database: at3456
WebApp URL: http://35.229.87.203:8111/

Description of Parts Implemented:
- Account holders can favourite and rate animes. 'Favourites page'. 
- Account holders can write reviews and post comments. 
- Adminstrators can edit and delete reviews. 

Changes
- Inputs: From set of animes to set of genres; recommendation based on genres
  - We did this because we thought it'd make more sense to recommend based off of genres.
- Added Search function for specific animes
  - For convenience; i.e. user wants to view a specific anime.
- Changed avg_rating in anime to a function that calculates the average based on user ratings
  - First, we updated avg_rating with the calculated average (from the original dataset).
  - Then, we update avg_rating everytime a user rates an anime. 
  - We did this because we were unable to accurately update the old avg_rating when a new rating is created.
- Users can edit and delete their own reviews and comments. (function; not stored in db)
- Admins can edit and delete both reviews and comments. However, edits/deletes on comments are not stored. 
- Added delete cascade for comment deletion. 
- Recommendations only show 100 max 

New Features:
- Sorting function for recommendations.
  - Sort by 1) the number of relevant genres, then 2) the avg_rating.
  - Number of relevant genres is defined by how many genres match the set of genres inputted.\

Two Interesting Web Pages:
1. /search
This is the name of the recommendations page. For this page, we took 3 inputs from index: genres, 
excluded genres, and minimum rating. The first 2 inputs are used to create temporary tables, which
are crucial for the animes query. The animes query returns rows of animes that each have the desired genres, 
don't have the excluded genres, and are above the minimum rating. It further returns a count of how many 
relevant genres each anime has, and orders by this count in descending order.

2. /anime
This is the name of the anime page, which displays the reviews, comments, and average rating of an anime that the user has selected to view.
This page is related to the database operations in two main ways: 
 1) we need to do a query on the anime table in the database to find and display the average rating
2) and then we need to do a natural join between the anime, describes, and writes tables in order to find and display
all reviews and comments written on the selected anime, as well the information of the user who left the review/comment.