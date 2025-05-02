import requests
import re
import os
import shutil
class FoodRecipe:
    _BASE_URL = "https://www.themealdb.com/api/json/v1/1/"
    def __init__(self, **kwargs):
        """Enter {random:True} or {search:str or int}. or do it later using get_random_recipe or get_recipe."""
        self.detail:dict = {}
        self.id:int = -1
        self.name:str = ""
        self.category:str = ""
        self.image_url:str = ""
        self.process_url:str = ""
        self.ingredient:dict = {}
        self.area:str = ""
        self.tags:str = ""
        self.instructions:list = []
        self._isfilled:bool = False

        try:
            if kwargs["random"] == True:
                self.get_random_recipe()
                self._isfilled = True
        except KeyError:
            pass
        
        if not self._isfilled and "search" in kwargs:
            self.get_recipe(kwargs["search"])
            self._isfilled = True

    def __str__(self) -> str:
        return str({"ID" : self.id,
                "Name" : self.name,
                "Category" : self.category,
                "Area" : self.area,
                "Tags" : self.tags})

    def get_random_recipe(self):
        recipe = FoodRecipe.random_recipe()
        self._set_var(recipe)
        self._isfilled = True

    def get_recipe(self, search_content):
        """Search by {name:str} or {ID:int}."""
        if type(search_content) == str:
            # containing only allowed characters
            if len(re.split(r"[a-zA-Z &,]+", search_content)) == 2:
                php_url = "search.php"
                filter_url = "?s=" + search_content
            else:
                raise Exception("Name search can only contains allowed characters")
        elif type(search_content) == int:
            php_url = "lookup.php"
            filter_url = "?i=" + str(search_content)
        else:
            raise Exception("Invalid input.")
        recipe = FoodRecipe._api_call(php_url, filter_url)["meals"][0]
        self._set_var(recipe)
        self._isfilled = True

    def save_file(self):
        dir = "Recipe/"
        if not os.path.exists(dir):
            os.makedirs(dir)

        full_name = str(self.id) + " - " + self.name
        with open(os.path.join(dir, full_name+".jpg"), "wb") as out_file:
            _ = requests.get(self.image_url, stream=True).raw
            shutil.copyfileobj(_, out_file)

        with open(os.path.join(dir, full_name+".txt"), "w") as out_file:
            out_file.writelines([i + '\n' for i in self.instructions])
        

    def _set_var(self, recipe:dict):
        # get possible ingredient ids
        ingredient_id = [key for key in recipe.keys() if "Ingredient" in key]
        # get all the ingredient using the ids -> exclude empty string (empty str is false)
        ingredients = [ingredient for ingredient in [recipe[i] for i in ingredient_id] if ingredient]
        # get possible measure ids -> get measures
        measure_id = ["strMeasure"+ str(i) for i in range(1, len(ingredients)+1)]
        measures = [recipe[i] for i in measure_id]

        # split str based on capital letter
        instructions = [i.strip() for i in re.split("(?=[A-Z])", recipe["strInstructions"]) if i.strip()]

        self.detail=recipe
        self.id=recipe["idMeal"]
        self.name=recipe["strMeal"]
        self.image_url=recipe["strMealThumb"]
        # combine ingredient and measurement
        self.ingredient={i[0]:i[1] for i in zip(ingredients, measures)}
        self.category=recipe["strCategory"]
        self.area=recipe["strArea"]
        self.process_url=recipe["strYoutube"]
        self.tags=recipe["strTags"]
        self.instructions=instructions

    @staticmethod
    def get_filtered_recipes(**filters:dict) -> dict:
        """Set {area:str} or {category:str} or {ingredient:str}."""
        if len(filters) != 1:
            raise Exception("Expeting only one parameter.")

        if "area" in filters:
            filter_url = "?a=" + filters["area"]
        elif "category" in filters:
            filter_url = "?c=" + filters["category"]
        elif "ingredient" in filters:
            filter_url = "?i=" + filters["ingredient"]
        else:
            raise Exception("Invaild keyword. Only area, category or ingredient is accepted.")

        recipe = FoodRecipe._api_call("filter.php", filter_url)["meals"]
        return {meal["idMeal"]: meal["strMeal"] for meal in recipe}

    @staticmethod
    def all_filter_options(area:bool=False, category:bool=False, ingredient:bool=False) -> list:
        """Set one of parameters to be True."""
        if area + category + ingredient != 1:
            raise Exception("Expeting only one parameter to be true.")

        if area:
            filter_url = "?a=list"
            _="strArea"
        elif category:
            filter_url = "?c=list"
            _="strCategory"
        elif ingredient:
            filter_url = "?i=list"
            _="strIngredient"
        else:
            raise Exception("Invaild keyword. Only area, category or ingredient is accepted.")

        result = FoodRecipe._api_call("list.php", filter_url)
        return [i[_] for i in result["meals"]]

    @staticmethod
    def random_recipe() -> dict:
        return FoodRecipe._api_call("random.php", "")["meals"][0]

    @staticmethod
    def _api_call(php_url:str, filter_url:str) -> dict:
        url = FoodRecipe._BASE_URL + php_url + filter_url
        return requests.get(url).json()