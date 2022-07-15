#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import (Blueprint, render_template, request, flash, redirect, url_for)
from forms import *
from sqlalchemy import func
from datetime import datetime
from models import *

artist_page = Blueprint('artist_page', __name__, template_folder='templates')

#  Artists
#  ----------------------------------------------------------------
@artist_page.route('/artists')
def artists():
  
  artistdata = db.session.query(Artist.id, Artist.name).all()
  data = []
  for artist in artistdata:
    data.append({"id": artist.id, "name": artist.name})
  
  return render_template('pages/artists.html', artists=data)

@artist_page.route('/artists/search', methods=['POST'])
def search_artists():

  search_term = request.form.get('search_term')
  if(',' in search_term) :
    n_search = search_term.split(',')
    artists = db.session.query(Artist.id, Artist.name).filter(Artist.city == n_search[0].strip()).filter(Artist.state == n_search[1].strip()).all();
  else :
    artists = db.session.query(Artist.id, Artist.name).filter(Artist.name.ilike('%'+search_term+'%')).all();

  data = []
  for artist in artists:
    upcomingshows = db.session.query(func.count(Shows.artist_id).label("tot")).filter(Shows.artist_id == artist.id).filter(Shows.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).one()
    data.append({"id": artist.id, "name": artist.name, "num_upcoming_shows": upcomingshows.tot})
  
  response = {"count": len(artists), "data": data}
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@artist_page.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artistdata = db.session.query(Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, 
                               Artist.phone, Artist.website_link, Artist.facebook_link, Artist.seeking_venue, 
                               Artist.seeking_description, Artist.image_link).filter(Artist.id == artist_id).one()
  
  pastshows = db.session.query(Shows.venue_id, Shows.start_time,
                               Venue.name.label("venue_name"), 
                               Venue.image_link.label("venue_image_link")
                              ).join(Venue, Shows.venue_id == Venue.id).join(Artist, Shows.artist_id == Artist.id
                                  ).filter(Shows.artist_id == artist_id).filter(Shows.start_time < datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()

  upcomingshows = db.session.query(Shows.venue_id, Shows.start_time,
                               Venue.name.label("venue_name"), 
                               Venue.image_link.label("venue_image_link")
                              ).join(Venue, Shows.venue_id == Venue.id).join(Artist, Shows.artist_id == Artist.id
                                  ).filter(Shows.artist_id == artist_id).filter(Shows.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  

  data = {
    "id": artistdata.id,
    "name": artistdata.name,
    "genres": artistdata.genres.replace("{", "").replace("}", "").split(','),
    "city": artistdata.city,
    "state": artistdata.state,
    "phone": artistdata.phone,
    "website": artistdata.website_link,
    "facebook_link": artistdata.facebook_link,
    "seeking_venue": artistdata.seeking_venue,
    "seeking_description": artistdata.seeking_description,
    "image_link": artistdata.image_link,
    "past_shows_count": len(pastshows),
    "upcoming_shows_count": len(upcomingshows)
  }

  data["past_shows"] = []
  for shows in pastshows:
    psh = {"venue_id": shows.venue_id, "venue_name": shows.venue_name, "venue_image_link": shows.venue_image_link, "start_time": shows.start_time}
    data["past_shows"].append(psh)

  data["upcoming_shows"] = []
  for shows in upcomingshows:
    ush = {"venue_id": shows.venue_id, "venue_name": shows.venue_name, "venue_image_link": shows.venue_image_link, "start_time": shows.start_time}
    data["upcoming_shows"].append(ush)

  
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@artist_page.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@artist_page.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

  form = ArtistForm(request.form)
  try:
    artist = Artist.query.get(artist_id)
    form.populate_obj(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except ValueError as e:
    print(e)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('artist_page.show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------

@artist_page.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@artist_page.route('/artists/create', methods=['POST'])
def create_artist_submission():

  form = ArtistForm(request.form)
  try:
    artist = Artist()
    form.populate_obj(artist)
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except ValueError as e:
    print(e)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()

  
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  #return render_template('pages/home.html')
  return redirect(url_for('index'))


