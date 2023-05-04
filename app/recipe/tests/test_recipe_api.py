"""Tests for recipe API"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe

from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,)


RECIPES_URL=reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """recipe details url"""
    return reverse('recipe:recipe-detail',args=[recipe_id])


def create_recipe(user, **params):
    """Create and return a simeple recipe"""

    defaults={
        'title':'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal(4.55),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }

    defaults.update(params)

    recipe=Recipe.objects.create(user=user, **defaults)
    return recipe

class PublicRecipeAPITests(TestCase):
    def setUp(self):
        self.client=APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""

        res =self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code,status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeApiTests(TestCase):
    """Test authenticatee requests"""      

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'testpass123',
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """List recipes"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')

        serializer=RecipeSerializer(recipes,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    
    def test_recipe_list_limited_to_user(self):
        """Test list of recipes limited to authenticated users"""
        other_user=get_user_model().objects.create_user(
            'pther@example.com',
            'password123',
        )

        create_recipe(user=other_user)
        create_recipe(user=self.user)

        res =self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer=RecipeSerializer(recipes,many=True)
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        self.assertEqual(res.data,serializer.data)
    
    def test_get_recipe_detail(self):
        '''Test get recipe detail'''

        recipe=create_recipe(user=self.user)
        
        url=detail_url(recipe.id)
        res=self.client.get(url)

        serializer=RecipeDetailSerializer(recipe)
        self.assertEqual(res.data,serializer.data)

    
    def test_create_recipe(self):
        """Tesst creating a recipe"""

        payload={
        'title':'Sample recipe',
        'time_minutes': 42,
        'price': Decimal('8.55'),

        }

        res=self.client.post(RECIPES_URL,payload)

        self.assertEqual(res.status_code,status.HTTP_201_CREATED)
        recipe=Recipe.objects.get(id=res.data['id'])

        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
            
        self.assertEqual(recipe.user,   self.user)
    
    def test_full_update(self):
        """Test full update of recipe"""
        
        recipe=create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://suplementeks.com',
            description='Sample recipe description',
        )

        payload={
            'title':'New recipe title',
            'link':'http://suplementeks.com',
            'description':'New recipe description',
            'time_minutes':10,
            'price':Decimal('12.2'),
        }

        url=detail_url(recipe.id)
        res=self.client.put(url,payload)

        self.assertEqual(res.status_code,status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
        self.assertEqual(recipe.user,self.user)

    def test_update_user_returns(self):
        """Test changing the recipe user results in an error"""

        new_user=create_user(email='user2@example.com',password='test123')
        recipe=create_recipe(user=self.user)

        payload={'user':new_user.id}
        url=detail_url(recipe.id)
        self.client.patch(url,payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user,self.user)