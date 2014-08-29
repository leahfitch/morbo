Morbo
=====

|Build Status| |Coverage Status| |Docs Status|

Morbo is another python package for mapping objects to `mongodb <http://www.mongodb.com/>`_. Its goal is to provide a friendly API that includes validation and relationships without enforcing concepts from relational databases or obscuring the already very nice `pymongo <http://api.mongodb.org/python/current/>`_ query interface. There are lots of existing packages for this sort of task. Some popular ones are `MongoKit <http://namlook.github.io/mongokit/>`_, `MongoEngine <http://mongoengine.org/>`_ and Ming. Morbo was written partly because no existing package meets all of the above goals and partly because writing it is fun.

Example
~~~~~~~

.. code:: python

	from morbo import *
	
	class Person(Model):
		name = Text(required=True, maxlength=100)
		email = Email(required=True)
		
		
	class Recipe(Model):
		name = Text(required=True, maxlength=100)
		author = One(Person)
		ingredients = ManyToMany('Ingredient', inverse='recipes')
		instructions = Text()
		
		
	class Ingredient(Model):
		name = Text(required=True, maxlength=100)
		
		
	connection.setup('morbo_recipe_box')
	
	bob = Person(name='Chef Bob', email="bob-the-chef@example.com")
	bob.save()
	
	recipe = Recipe(name="Cinnamon & Sugar Popcorn")
	recipe.save()
	recipe.author = bob
	
	for n in ('popcorn', 'coconut oil', 'sugar', 'cinnamon'):
		ingredient = Ingredient(name=n)
		ingredient.save()
		recipe.ingredients.add(recipe)
		
	cinnamon = Ingredients.find_one({'name':'cinnamon'})
	recipe = cinnamon.recipes.find_one()
	print "%s by %s" % (recipe.name, recipe.author.name)
		

.. |Build Status| image:: https://travis-ci.org/elishacook/morbo.svg
   :target: https://travis-ci.org/elishacook/morbo

.. |Coverage Status| image:: https://img.shields.io/coveralls/elishacook/morbo.svg
   :target: https://coveralls.io/r/elishacook/morbo

.. |Docs Status| image:: https://readthedocs.org/projects/morbo/badge/?version=latest
   :target: https://readthedocs.org/projects/morbo/?badge=latest