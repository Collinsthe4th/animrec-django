"""Pages and JSON endpoints of the AnimRec site."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .services import all_genres, clamp_k, get_recommender

MAX_QUERY_LENGTH = 300


@require_GET
def home(request: HttpRequest) -> HttpResponse:
    """Search form. With ``?title=`` or ``?describe=`` it also shows results."""
    rec = get_recommender()
    title = request.GET.get("title", "").strip()[:MAX_QUERY_LENGTH]
    describe = request.GET.get("describe", "").strip()[:MAX_QUERY_LENGTH]
    genre = request.GET.get("genre", "").strip()
    genre = genre if genre in rec.genre_names else ""
    k = clamp_k(request.GET.get("k"))

    context = {
        "genres": all_genres(),
        "title": title,
        "describe": describe,
        "genre": genre,
        "k": k,
        "results": None,
        "matched": None,
        "error": None,
        "catalogue_size": len(rec.titles),
    }
    status = 200
    if title:
        try:
            context["results"] = rec.recommend(title, k=k, genre=genre or None)
            context["matched"] = rec.find_title(title)
        except KeyError:
            context["error"] = f"No title in the catalogue matches “{title}”. Try a shorter part of the name."
            context["suggestions"] = rec.search(title[:4])
            status = 404
    elif describe:
        context["results"] = rec.recommend_from_text(describe, k=k, genres=[genre] if genre else None)
    return render(request, "recommender/home.html", context, status=status)


@require_GET
def api_recommend(request: HttpRequest) -> JsonResponse:
    """``/api/recommend?title=...&k=5&genre=Action`` or ``?describe=...``."""
    rec = get_recommender()
    title = request.GET.get("title", "").strip()[:MAX_QUERY_LENGTH]
    describe = request.GET.get("describe", "").strip()[:MAX_QUERY_LENGTH]
    genre = request.GET.get("genre") or None
    k = clamp_k(request.GET.get("k"))

    if genre and genre not in rec.genre_names:
        return JsonResponse({"error": f"Unknown genre '{genre}'", "genres": rec.genre_names}, status=400)
    if title:
        try:
            results = rec.recommend(title, k=k, genre=genre)
        except KeyError:
            return JsonResponse({"error": f"'{title}' is not in the catalogue"}, status=404)
        return JsonResponse({"query": rec.find_title(title), "results": [r.to_dict() for r in results]})
    if describe:
        results = rec.recommend_from_text(describe, k=k, genres=[genre] if genre else None)
        return JsonResponse({"query": describe, "results": [r.to_dict() for r in results]})
    return JsonResponse({"error": "Provide a 'title' or 'describe' parameter"}, status=400)


@require_GET
def api_search(request: HttpRequest) -> JsonResponse:
    """Autocomplete: ``/api/search?q=gund``."""
    q = request.GET.get("q", "").strip()[:MAX_QUERY_LENGTH]
    return JsonResponse({"q": q, "titles": get_recommender().search(q, limit=8)})


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "titles": len(get_recommender().titles)})
