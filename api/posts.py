from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from db.models import Post, User
from core.database import get_db
from .schemas import PostCreate, PostUpdate, PostResponse, LikedPostResponse, SavedPostResponse
from .auth import get_current_user

router = APIRouter()


@router.get('/posts/', response_model=list[PostResponse], tags=['posts'])
def post_list(db: Session = Depends(get_db)):
    posts = db.query(Post).all()
    return posts


@router.post('/posts/create', response_model=PostResponse, tags=['posts'])
def create_post(post: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_post = Post(title=post.title, content=post.content, author_id=current_user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get('/posts/{post_id}', response_model=PostResponse, tags=['posts'])
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.put('/posts/{post_id}', response_model=PostUpdate, tags=['posts'])
def update_post( post_id: int, post: PostUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_post = db.query(Post).get(post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Post not found')
    if existing_post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Запрещен в доступе ')
    existing_post.title = post.title
    existing_post.content = post.content
    db.commit()
    db.refresh(existing_post)
    return existing_post


@router.delete('/posts/{post_id}', tags=['posts'])
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_post = db.query(Post).get(post_id)
    if not existing_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пост не найден')
    if existing_post.author_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Запрещено')
    db.delete(existing_post)
    db.commit()
    return {'message': 'Пост успешно удален'}


@router.post('/posts/{post_id}/like', tags=['post_likes_dislike'])
def like_dislike_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пост не найден')
    if current_user.id == post.author_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You cannot like your own post')
    if current_user in post.liked_by:
        post.liked_by.remove(current_user)
        db.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail='Post disliked')
    post.liked_by.append(current_user)
    db.commit()
    return HTTPException(status_code=status.HTTP_200_OK, detail='Post liked!')


@router.post('/posts/{post_id}/favorites', tags=['favorites'])
def favorite_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).get(post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пост не найден')
    if current_user.id == post.author_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You cannot save your own post')
    if current_user in post.saved_by:
        post.saved_by.remove(current_user)
        db.commit()
        raise HTTPException(status_code=status.HTTP_200_OK, detail='Post unsaved')
    post.saved_by.append(current_user)
    db.commit()
    return HTTPException(status_code=status.HTTP_200_OK, detail='Post saved!')


@router.get("/saved_posts", response_model=SavedPostResponse, tags=['favorites'])
def favorited_posts(current_user: User = Depends(get_current_user)):
    saved_posts = current_user.saved_posts
    return {'saved_posts': saved_posts}


@router.get("/liked_posts", response_model=LikedPostResponse, tags=['liked-post'])
def liked_posts(current_user: User = Depends(get_current_user)):
    liked_posts = current_user.liked_posts
    return {'liked_posts': liked_posts}