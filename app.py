#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy.sql import func
from sqlalchemy import and_
import sys
import pytz
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), nullable=True)
    seeking_talent = db.Column(db.Boolean,server_default='f')
    seeking_description = db.Column(db.String())
    website = db.Column(db.String(120), nullable=True)
    shows = db.relationship('Show', backref='venue', lazy=True,cascade='all, delete-orphan')

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean,server_default='f')
    seeking_description = db.Column(db.String())
    shows = db.relationship('Show', backref='artist', lazy=True,cascade='all, delete-orphan')

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
  start_time = db.Column(db.DateTime(timezone=True), nullable=False,server_default=func.now())
#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  result =[]
  venue_areas = set()
  venues = Venue.query.all()

  # get  unique cities and states
  for venue in venues:
    venue_areas.add((venue.city,venue.state))
  
  for areas in venue_areas:
      # find all shows in the same city and state 
      shows = db.session.query(Show).join(Venue).filter(Venue.city==areas[0],Venue.state==areas[1]).all()
      if(len(shows)>0): 
        num_upcoming_shows = 0
        venue_data =[]
        for show in shows:
          # calculate number of upcoming shows
          if show.start_time > datetime.now(pytz.utc): num_upcoming_shows += 1

        venue_data.append({
          'id':show.venue.id, 
          'name':show.venue.name,
          'num_upcoming_shows':num_upcoming_shows
        }) 
      else:
        venue_data=[]
      result.append({
        'city':areas[0],
        'state':areas[1],
        'venues':venue_data
      })  
        
  return render_template('pages/venues.html', areas=result);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  term = request.form.get('search_term')
  if(len(term)< 1): 
    flash('please enter a search query !') 
    return render_template('errors/404.html')
  venues = Venue.query.filter(Venue.name.ilike(f'%{term}%')).all()
  response={
    "count":len(venues),
    "data":venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    artist_detail={
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link":show.artist.image_link ,
      "start_time": show.start_time.strftime("%d-%m-%Y %H:%M:%S")
    }
    if show.start_time > datetime.now(pytz.utc):
      upcoming_shows.append(artist_detail)
    else:
      past_shows.append(artist_detail)


  result={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link":venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  
  # data = list(filter(lambda d: d['id'] == venue_id, [venue]))[0]
  return render_template('pages/show_venue.html', venue=result)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  # print(form.name.data)
  data={}
  data['name'] =form.name.data
  try:
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    venue = Venue(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    address = form.address.data,
    phone = form.phone.data,
    image_link = form.image_link.data,
    facebook_link = form.facebook_link.data,
    genres = form.genres.data,
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data,
    website = form.website.data)
    db.session.add(venue)
    db.session.commit()
    flash('Venue ' + data['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Venue ' + data['name'] + ' could not be listed.')
    return render_template('errors/500.html')
  finally:
    db.session.close()



@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
      
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash('Venue deleted!')
  except:
      flash('Venue could not be deleted!')
      db.session.rollback()
  finally:
      db.session.close()
  return redirect(url_for('index'),200)
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.all();
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  term = request.form.get('search_term')
  if(len(term)< 1): 
    flash('please enter a search query !') 
    return render_template('errors/404.html')
  artists = Artist.query.filter(Artist.name.ilike(f'%{term}%')).all()

  response={
    "count":len(artists),
    "data":artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id).all()
  past_shows = []
  upcoming_shows = []

  for show in shows:
    venue_detail={
      "venue": show.venue.id,
      "venue": show.venue.name,
      "venue_image_link":show.venue.image_link ,
      "start_time": show.start_time.strftime("%d-%m-%Y %H:%M:%S")
    }
    if show.start_time > datetime.now(pytz.utc):
      upcoming_shows.append(venue_detail)
    else:
      past_shows.append(venue_detail)
   
  result={
  "id": artist.id,
  "name": artist.name,
  "genres": artist.genres,
  "city": artist.city,
  "state": artist.state,
  "phone": artist.phone,
  "facebook_link": artist.facebook_link,
  "seeking_venue": artist.seeking_venue,
  "seeking_description": artist.seeking_description,
  "image_link":artist.image_link,
  "past_shows": past_shows,
  "upcoming_shows": upcoming_shows,
  "past_shows_count": len(past_shows),
  "upcoming_shows_count": len(upcoming_shows),
}
  # data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=result)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  query = Artist.query.get(artist_id)
  artist={
    "id": query.id,
    "name": query.name,
    "genres": query.genres,
    "city": query.city,
    "state": query.state,
    "phone": query.phone,
    "facebook_link": query.facebook_link,
    "seeking_venue": query.seeking_venue,
    "seeking_description": query.seeking_venue,
    "image_link": query.image_link
  }
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  query = Venue.query.get(venue_id)
  venue={
    "id": query.id,
    "name": query.name,
    "genres": query.genres,
    "address": query.address,
    "city": query.city,
    "state": query.state,
    "phone":query.phone,
    "website": query.website,
    "facebook_link": query.facebook_link,
    "seeking_talent": query.seeking_talent,
    "seeking_description": query.seeking_description,
    "image_link":query.image_link
  }
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
    form = VenueForm()
    try:
      venue = Venue.query.get(venue_id)
      venue.name = form.name.data,
      venue.city = form.city.data,
      venue.state = form.state.data,
      venue.address = form.address.data,
      venue.phone = form.phone.data,
      venue.image_link = form.image_link.data,
      venue.facebook_link = form.facebook_link.data,
      venue.website = form.website.data
      db.session.commit()
      flash('Venue was successfully updated!')
      return redirect(url_for('show_venue', venue_id=venue_id))
    except:
      db.session.rollback()
      print(sys.exc_info())
      flash('An error occurred. Venue could not be updated.')
      return render_template('errors/500.html')
    finally:
      db.session.close()



#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()
  # print(form.name.data)
  data={}
  data['name'] =form.name.data
  try:
    artist = Artist(
    name = form.name.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    facebook_link = form.facebook_link.data,
    genres = form.genres.data,
    image_link = form.image_link.data,
    seeking_venue = form.seeking_venue.data,
    seeking_description = form.seeking_description.data)
    db.session.add(artist)
    db.session.commit()
    flash('Artiste ' + data['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Artiste ' + data['name'] + ' could not be listed.')
    return render_template('errors/500.html')
  finally:
    db.session.close()


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  result = []
  
  for show in shows:
      result.append({
        'venue_id':show.venue_id,
        'venue_name':show.venue.name,
        'artist_id':show.artist_id,
        'artist_image_link':show.artist.image_link,
        'start_time':show.start_time.strftime("%d-%m-%Y %H:%M:%S")
      })

  # print(result)
  return render_template('pages/shows.html', shows=result)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form  = ShowForm()
  # print(form.name.data)
  try:
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    show = Show(
    artist_id = form.artist_id.data,
    venue_id = form.venue_id.data,
    start_time= form.start_time.data)
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
    return render_template('pages/home.html')
  except:
    db.session.rollback()
    print(sys.exc_info())
    flash('An error occurred. Show could not be listed.')
    return render_template('errors/500.html')
  finally:
    db.session.close()

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
