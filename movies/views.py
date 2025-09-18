# movies/views.py
from collections import defaultdict

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import Movie, Review, Comment
from .forms import CommentForm


def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {
        'title': 'Movies',
        'movies': movies,
    }
    return render(request, 'movies/index.html', {'template_data': template_data})


from collections import defaultdict

def show(request, id):
    movie = get_object_or_404(Movie, id=id)
    reviews = Review.objects.filter(movie=movie).order_by('date')

    # Get all comments for these reviews in one query
    all_comments = (
        Comment.objects
        .filter(review__in=reviews)
        .select_related('review', 'author')   # 🔁 change 'author' to 'user' if your Comment model uses user instead
        .order_by('created_at')
    )

    # Group comments by review_id
    comments_by_review = defaultdict(list)
    for c in all_comments:
        comments_by_review[c.review_id].append(c)

    # Attach a flat list of comments directly onto each review
    for r in reviews:
        r.comments_flat = comments_by_review.get(r.id, [])

    template_data = {
        'title': movie.name,
        'movie': movie,
        'reviews': reviews,
    }
    return render(request, 'movies/show.html', {'template_data': template_data})



@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST.get('comment'):
        movie = get_object_or_404(Movie, id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    return redirect('movies.show', id=id)


@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)

    if request.method == 'GET':
        template_data = {
            'title': 'Edit Review',
            'review': review,
        }
        return render(request, 'movies/edit_review.html', {'template_data': template_data})

    elif request.method == 'POST' and request.POST.get('comment'):
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)

    return redirect('movies.show', id=id)


@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id, user=request.user)
    review.delete()
    return redirect('movies.show', id=id)


# Create a comment (top-level or reply) under a specific review
@login_required
def create_comment(request, id, review_id):
    """
    URL: /movies/<id>/review/<review_id>/comments/new/
    POST fields:
      - body: text of the comment (required)
      - parent: optional parent comment id (for replies); we still save it,
                but the UI shows comments flat.
    """
    review = get_object_or_404(Review, id=review_id, movie_id=id)

    if request.method != 'POST':
        return redirect('movies.show', id=id)

    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.review = review
        comment.author = request.user         # ⬅️ If your FK is 'user', use: comment.user = request.user

        # Safety: if parent is provided, it must belong to the same review
        if comment.parent and comment.parent.review_id != review.id:
            form.add_error('parent', 'Invalid parent comment.')
        else:
            comment.save()
            return redirect('movies.show', id=id)

    # If validation fails, re-render like show()
    reviews = Review.objects.filter(movie_id=id).order_by('date')
    all_comments = (
        Comment.objects
        .filter(review__in=reviews)
        .select_related('review', 'author')   # ⬅️ Change 'author' to 'user' if needed
        .order_by('created_at')
    )
    comments_by_review = defaultdict(list)
    for c in all_comments:
        comments_by_review[c.review_id].append(c)
    for r in reviews:
        r.comments_flat = comments_by_review.get(r.id, [])

    template_data = {
        'title': review.movie.name,
        'movie': review.movie,
        'reviews': reviews,
        # You can pass the form if you want to show field errors in the page;
        # your current template doesn't render form errors for comments, but no harm keeping it.
        'comment_form': form,
    }
    return render(request, 'movies/show.html', {'template_data': template_data})
