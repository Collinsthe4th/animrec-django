from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from .services import clamp_k

# The production storage needs a collectstatic manifest, which tests do not build.
PLAIN_STATIC = {"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}


@override_settings(STORAGES=PLAIN_STATIC)
class PageTests(SimpleTestCase):
    def test_home_renders_form(self):
        res = self.client.get(reverse("recommender:home"))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "AnimRec")
        self.assertContains(res, 'name="title"')
        self.assertContains(res, "Mecha")  # genre dropdown is filled from the model

    def test_title_search_shows_recommendations(self):
        res = self.client.get(reverse("recommender:home"), {"title": "cowboy bebop", "k": 5})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "Because you liked")
        self.assertEqual(len(res.context["results"]), 5)
        self.assertNotIn("Cowboy Bebop", [r.title for r in res.context["results"]])

    def test_genre_filter_is_applied(self):
        res = self.client.get(reverse("recommender:home"), {"title": "Trigun", "genre": "Mecha"})
        self.assertTrue(all("Mecha" in r.genres for r in res.context["results"]))

    def test_unknown_title_returns_404_with_message(self):
        res = self.client.get(reverse("recommender:home"), {"title": "zzzz not a show"})
        self.assertEqual(res.status_code, 404)
        self.assertContains(res, "No title in the catalogue", status_code=404)

    def test_description_search(self):
        res = self.client.get(reverse("recommender:home"), {"describe": "high school basketball team"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["results"][0].title, "SLAM DUNK")

    def test_user_input_is_escaped(self):
        res = self.client.get(reverse("recommender:home"), {"describe": "<script>alert(1)</script>"})
        self.assertNotContains(res, "<script>alert(1)</script>")


class ApiTests(SimpleTestCase):
    def test_recommend_by_title(self):
        res = self.client.get(reverse("recommender:api_recommend"), {"title": "evangelion", "k": 3})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["query"], "Shin Seiki Evangelion")
        self.assertEqual(len(data["results"]), 3)
        self.assertIn("synopsis_similarity", data["results"][0])

    def test_recommend_errors(self):
        url = reverse("recommender:api_recommend")
        self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(self.client.get(url, {"title": "zzzz not a show"}).status_code, 404)
        self.assertEqual(self.client.get(url, {"title": "Trigun", "genre": "Cooking"}).status_code, 400)

    def test_search_and_health(self):
        res = self.client.get(reverse("recommender:api_search"), {"q": "gund"})
        self.assertTrue(res.json()["titles"])
        self.assertTrue(all("gund" in t.lower() for t in res.json()["titles"]))
        self.assertEqual(self.client.get(reverse("recommender:health")).json()["titles"], 200)

    def test_post_is_rejected(self):
        self.assertEqual(self.client.post(reverse("recommender:api_recommend")).status_code, 405)


class HelperTests(SimpleTestCase):
    def test_clamp_k(self):
        self.assertEqual(clamp_k(None), 10)
        self.assertEqual(clamp_k("abc"), 10)
        self.assertEqual(clamp_k("0"), 1)
        self.assertEqual(clamp_k("500"), 20)
        self.assertEqual(clamp_k("7"), 7)
