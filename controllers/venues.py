#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import (Blueprint, jsonify, render_template, request, flash, redirect, url_for)
from forms import *
import sys
from sqlalchemy import func
from datetime import datetime
from models import *

venue_page = Blueprint('venue_page', __name__, template_folder='templates')

@venue_page.route('/venues')
def venues():

  data = []
  venuefilter = db.session.query(func.count(Venue.id).label('tot'), 
                           Venue.city,
                           Venue.state
                           ).group_by(Venue.city, Venue.state).all()
  
  for v in venuefilter :
    city = v.city
    state = v.state
    dic = {"city": city, "state": state, "venues": []}
    venuedata = db.session.query(Venue.id, Venue.name).filter(Venue.city == city).filter(Venue.state == state).all()
    for venue in venuedata :
      id = venue.id
      name = venue.name
      num = db.session.query(func.count(Shows.venue_id).label("tot")).filter(Shows.venue_id == id).filter(Shows.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).one()
      num_upcoming_shows = num.tot
      dic["venues"].append({"id": id, "name": name, "num_upcoming_shows": num_upcoming_shows})

    data.append(dic)
  
  return render_template('pages/venues.html', areas=data);

@venue_page.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term')
  if(',' in search_term) :
    n_search = search_term.split(',')
    venues = db.session.query(Venue.id, Venue.name).filter(func.lower(Venue.city) == func.lower(n_search[0].strip())).filter(func.lower(Venue.state) == func.lower(n_search[1].strip())).all();
  else :
    venues = db.session.query(Venue.id, Venue.name).filter(Venue.name.ilike('%'+search_term+'%')).all();
  
  data = []
  for venue in venues:
    upcomingshows = db.session.query(func.count(Shows.venue_id).label("tot")).filter(Shows.venue_id == venue.id).filter(Shows.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).one()
    data.append({"id": venue.id, "name": venue.name, "num_upcoming_shows": upcomingshows.tot})
    

  
  response = {"count": len(venues), "data": data}

  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@venue_page.route('/venues/<int:venue_id>')
def show_venue(venue_id):

  venuedata = db.session.query(Venue.id, Venue.name, Venue.genres, Venue.address, Venue.city, Venue.state, 
                               Venue.phone, Venue.website_link, Venue.facebook_link, Venue.seeking_talent, 
                               Venue.seeking_description, Venue.image_link).filter(Venue.id == venue_id).one()
  
  pastshows = db.session.query(Shows.artist_id, Shows.start_time,
                               Artist.name.label("artist_name"), 
                               Artist.image_link.label("artist_image_link")
                              ).join(Venue, Shows.venue_id == Venue.id).join(Artist, Shows.artist_id == Artist.id
                                  ).filter(Shows.venue_id == venue_id).filter(Shows.start_time < datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()

  upcomingshows = db.session.query(Shows.artist_id, Shows.start_time,
                               Artist.name.label("artist_name"), 
                               Artist.image_link.label("artist_image_link")
                              ).join(Venue, Shows.venue_id == Venue.id).join(Artist, Shows.artist_id == Artist.id
                                  ).filter(Shows.venue_id == venue_id).filter(Shows.start_time > datetime.now().strftime("%Y-%m-%d %H:%M:%S")).all()
  
  data = {
    "id": venuedata.id,
    "name": venuedata.name,
    "genres": venuedata.genres.replace("{", "").replace("}", "").split(','),
    "address": venuedata.address,
    "city": venuedata.city,
    "state": venuedata.state,
    "phone": venuedata.phone,
    "website": venuedata.website_link,
    "facebook_link": venuedata.facebook_link,
    "seeking_talent": venuedata.seeking_talent,
    "seeking_description": venuedata.seeking_description,
    "image_link": venuedata.image_link,
    "past_shows_count": len(pastshows),
    "upcoming_shows_count": len(upcomingshows)
  }

  data["past_shows"] = []
  for shows in pastshows:
    psh = {"artist_id": shows.artist_id, "artist_name": shows.artist_name, "artist_image_link": shows.artist_image_link, "start_time": shows.start_time}
    data["past_shows"].append(psh)

  data["upcoming_shows"] = []
  for shows in upcomingshows:
    ush = {"artist_id": shows.artist_id, "artist_name": shows.artist_name, "artist_image_link": shows.artist_image_link, "start_time": shows.start_time}
    data["upcoming_shows"].append(ush)
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@venue_page.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@venue_page.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form)
  try:
    venue = Venue()
    form.populate_obj(venue)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except ValueError as e:
    print(e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()   

  
  return redirect(url_for('index'))

@venue_page.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  try:
    db.session.query(Shows).filter(Shows.venue_id==venue_id).delete()
    db.session.query(Venue).filter(Venue.id==venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
    print(sys.exc_info())
  finally:
    db.session.close()

  return jsonify({ 'success': True })

@venue_page.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@venue_page.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm(request.form)
  try:
    venue = Venue.query.get(venue_id)
    form.populate_obj(venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except ValueError as e:
    print(e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated.')
    db.session.rollback()
  finally:
    db.session.close() 

  return redirect(url_for('venue_page.show_venue', venue_id=venue_id))

