#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import (Blueprint, render_template, request, flash, redirect, url_for)
from forms import *
from models import *

shows_page = Blueprint('shows_page', __name__, template_folder='templates')

#  Shows
#  ----------------------------------------------------------------

@shows_page.route('/shows')
def shows():

  showsdata = db.session.query(Shows.venue_id, Shows.artist_id, Shows.start_time, 
                               Venue.name.label("venue_name"), 
                               Artist.name.label("artist_name"), 
                               Artist.image_link.label("artist_image_link")
                              ).join(Venue, Shows.venue_id == Venue.id).join(Artist, Shows.artist_id == Artist.id).all()
  data = []
  for shows in showsdata:
    data.append({"venue_id": shows.venue_id, "venue_name": shows.venue_name, 
                 "artist_id": shows.artist_id, "artist_name": shows.artist_name, 
                 "artist_image_link": shows.artist_image_link, "start_time": shows.start_time})

  
  return render_template('pages/shows.html', shows=data)

@shows_page.route('/shows/create')
def create_shows():
  
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@shows_page.route('/shows/create', methods=['POST'])
def create_show_submission():

  form = ShowForm(request.form)
  try:
    shows = Shows()
    form.populate_obj(shows)
    db.session.add(shows)
    db.session.commit()
    flash('Show was successfully listed!')
  except ValueError as e:
    print(e)
    flash('An error occurred. Show could not be listed.')
    db.session.rollback()
  finally:
    db.session.close()
  
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return redirect(url_for('index'))

