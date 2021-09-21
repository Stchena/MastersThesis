# MastersThesis

## About
Welcome to my Master's Thesis project!\
I decided to compare dimensionality reduction techniques applied on text on the example of a news recommender system. \
Check the architecture of the project below. 

If you want to run the analysis yourself, it's pretty easy to do:
1. Download the repo
2. Set up `*.env` files in the `config/` directory. You need to rename the files to `app.env`, `primary_db.env` and `test_db.env`, as well as supply the necessary environment variables inside for the project to run. 
3. Run `docker compose up` in the main folder.
4. Once the `app container`finishes its job, enter the `playground container` and run the Jupyter Notebook to perform the analysis.
5. If you wish to gather news over an extended period of time, set up a cronjob or schedule a windows task to start the `app container`.

That's about it, have fun!

## Architecture
![news_recommender](https://user-images.githubusercontent.com/27273148/133613156-d39e5271-be56-4187-a764-a92b84d72169.png)
